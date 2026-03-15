"""
Cemini Financial Suite — Kalshi Rewards / Incentive Program Tracker

Polls Kalshi's incentive_programs API daily to track active volume and liquidity
incentive programs, detect new/expired programs, and publish a summary to Redis.

API endpoint used
-----------------
GET /trade-api/v2/incentive_programs
    status: active | upcoming | closed | paid_out | all
    type:   volume | liquidity | all

Note: Kalshi does NOT expose per-account accrued reward balances via the API.
Actual payout amounts only appear in portfolio/balance after a period closes and
paid_out=true.  This tracker monitors:
  - Active program metadata (pool sizes, market tickers, end dates)
  - Recently paid-out programs (inferred from status transition)
  - Balance snapshot (correlate balance increases with paid_out events)
  - Change detection vs. previous run (new / dropped programs)

Output channels
---------------
  Redis   → intel:kalshi_rewards  (TTL 86400 s — refreshed daily)
  JSONL   → /mnt/archive/kalshi_rewards/rewards_YYYYMMDD.jsonl
  Discord → DISCORD_WEBHOOK_URL env var (optional)

Usage
-----
  cd /opt/cemini
  PYTHONPATH=/opt/cemini python3 scripts/kalshi_rewards.py

  # or via cron (8:00 AM ET = 12:00 UTC Mon-Fri):
  0 12 * * 1-5 cd /opt/cemini && PYTHONPATH=/opt/cemini /usr/bin/python3 \\
      scripts/kalshi_rewards.py >> /mnt/archive/kalshi_rewards/cron.log 2>&1
"""

import base64
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from beartype import beartype
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

# ── Repo-root import path ──────────────────────────────────────────────────────
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core.intel_bus import _sync_client  # noqa: E402  (repo-root import)
from core.discord_notifier import get_notifier  # noqa: E402

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)
logger = logging.getLogger("kalshi_rewards")

# ── Config ─────────────────────────────────────────────────────────────────────
KALSHI_API_KEY = os.getenv("KALSHI_API_KEY", "")
KALSHI_PRIVATE_KEY_PATH = os.getenv(
    "KALSHI_PRIVATE_KEY_PATH",
    str(Path(__file__).resolve().parent.parent / "Kalshi by Cemini" / "private_key.pem"),
)
KALSHI_ENVIRONMENT = os.getenv("KALSHI_ENVIRONMENT", "production")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

KALSHI_BASE_URL = (
    "https://demo-api.kalshi.co/trade-api/v2"
    if KALSHI_ENVIRONMENT == "demo"
    else "https://api.elections.kalshi.com/trade-api/v2"
)

ARCHIVE_DIR = "/mnt/archive/kalshi_rewards"
INTEL_KEY = "intel:kalshi_rewards"
INTEL_TTL_DAILY = 86400  # 24 h — refresh daily

# Redis key to persist known active program IDs between runs
_PREV_IDS_KEY = "kalshi:rewards_prev_ids"


# ── RSA signing (matches pattern in autopilot.py) ──────────────────────────────

@beartype
def _load_private_key(path: str):
    """Load RSA private key from PEM file. Returns None on failure."""
    try:
        with open(path, "rb") as fh:
            return serialization.load_pem_private_key(fh.read(), password=None)
    except Exception as exc:
        logger.warning("🔑 [kalshi_rewards] Could not load private key at %s: %s", path, exc)
        return None


@beartype
def _build_headers(key_id: str, private_key, method: str, path: str) -> dict:
    """
    Build Kalshi RSA-PSS auth headers.

    Parameters
    ----------
    key_id      : KALSHI-ACCESS-KEY value
    private_key : loaded cryptography private key
    method      : HTTP method in uppercase (GET, POST)
    path        : API path including /trade-api/v2/... prefix (no base URL)
    """
    timestamp = str(int(time.time() * 1000))
    msg = (timestamp + method + path).encode("utf-8")
    signature = private_key.sign(
        msg,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    return {
        "KALSHI-ACCESS-KEY": key_id,
        "KALSHI-ACCESS-SIGNATURE": base64.b64encode(signature).decode("utf-8"),
        "KALSHI-ACCESS-TIMESTAMP": timestamp,
        "Content-Type": "application/json",
    }


# ── Kalshi API calls ───────────────────────────────────────────────────────────

@beartype
def fetch_incentive_programs(
    key_id: str,
    private_key,
    status: str = "active",
    program_type: str = "all",
    limit: int = 200,
) -> list:
    """
    Fetch incentive programs from Kalshi API.

    Parameters
    ----------
    status       : active | upcoming | closed | paid_out | all
    program_type : volume | liquidity | all
    limit        : max results per call (1–10000)

    Returns
    -------
    list of IncentiveProgram dicts, empty list on any failure.
    """
    path = "/trade-api/v2/incentive_programs"
    url = KALSHI_BASE_URL.replace("/trade-api/v2", "") + path
    headers = _build_headers(key_id, private_key, "GET", path)

    params: dict[str, Any] = {"status": status, "limit": limit}
    if program_type != "all":
        params["type"] = program_type

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        programs = data.get("incentive_programs", [])
        logger.info(
            "📋 [kalshi_rewards] %s status=%s type=%s → %d programs",
            path, status, program_type, len(programs),
        )
        return programs
    except Exception as exc:
        logger.warning("⚠️ [kalshi_rewards] fetch_incentive_programs failed: %s", exc)
        return []


@beartype
def fetch_balance(key_id: str, private_key) -> dict:
    """
    Fetch portfolio balance.  Returns dict with 'balance' and 'portfolio_value'
    in cents, or an empty dict on failure.
    """
    path = "/trade-api/v2/portfolio/balance"
    url = KALSHI_BASE_URL.replace("/trade-api/v2", "") + path
    headers = _build_headers(key_id, private_key, "GET", path)

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        logger.info(
            "💰 [kalshi_rewards] balance=%d cents  portfolio=%d cents",
            data.get("balance", 0),
            data.get("portfolio_value", 0),
        )
        return {
            "balance_cents": data.get("balance", 0),
            "portfolio_value_cents": data.get("portfolio_value", 0),
        }
    except Exception as exc:
        logger.warning("⚠️ [kalshi_rewards] fetch_balance failed: %s", exc)
        return {}


# ── Change detection ───────────────────────────────────────────────────────────

@beartype
def detect_changes(
    current_ids: list,
    prev_ids: list,
) -> dict:
    """
    Compare current active program IDs to previous snapshot.

    Returns
    -------
    dict with keys:
      new_ids  : programs that appeared since last run
      lost_ids : programs that disappeared (expired or moved to paid_out)
    """
    current_set = set(current_ids)
    prev_set = set(prev_ids)
    return {
        "new_ids": sorted(current_set - prev_set),
        "lost_ids": sorted(prev_set - current_set),
    }


@beartype
def _load_prev_ids(r) -> list:
    """Load previously seen active program IDs from Redis."""
    try:
        raw = r.get(_PREV_IDS_KEY)
        return json.loads(raw) if raw else []
    except Exception as exc:
        logger.debug("[kalshi_rewards] _load_prev_ids failed: %s", exc)
        return []


@beartype
def _save_prev_ids(r, ids: list) -> None:
    """Persist current active program IDs to Redis (TTL 48h)."""
    try:
        r.set(_PREV_IDS_KEY, json.dumps(sorted(ids)), ex=172800)
    except Exception as exc:
        logger.debug("[kalshi_rewards] _save_prev_ids failed: %s", exc)


# ── Redis publish ──────────────────────────────────────────────────────────────

@beartype
def publish_to_redis(payload: dict) -> None:
    """
    Publish rewards snapshot to intel:kalshi_rewards with 24h TTL.
    Wraps the standard IntelBus envelope format so downstream readers
    (MCP tools, dashboard) can consume it like any other intel key.
    """
    envelope = {
        "value": payload,
        "source_system": "kalshi_rewards",
        "timestamp": time.time(),
        "confidence": 1.0,
    }
    try:
        r = _sync_client()
        r.set(INTEL_KEY, json.dumps(envelope), ex=INTEL_TTL_DAILY)
        r.close()
        logger.info("📡 [kalshi_rewards] Published to Redis key: %s (TTL 86400s)", INTEL_KEY)
    except Exception as exc:
        logger.warning("⚠️ [kalshi_rewards] Redis publish failed: %s", exc)


# ── JSONL archive ──────────────────────────────────────────────────────────────

@beartype
def write_jsonl(record: dict) -> None:
    """
    Append one record to the daily JSONL archive file.

    File: /mnt/archive/kalshi_rewards/rewards_YYYYMMDD.jsonl
    """
    try:
        os.makedirs(ARCHIVE_DIR, exist_ok=True)
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        filepath = os.path.join(ARCHIVE_DIR, f"rewards_{date_str}.jsonl")
        with open(filepath, "a") as fh:
            fh.write(json.dumps(record, default=str) + "\n")
        logger.info("📁 [kalshi_rewards] Appended to %s", filepath)
    except Exception as exc:
        logger.warning("⚠️ [kalshi_rewards] JSONL write failed: %s", exc)


# ── Discord alert ──────────────────────────────────────────────────────────────

@beartype
def send_discord_alert(changes: dict, active_programs: list) -> None:
    """
    Post a Discord embed when new programs are detected or programs are paid out.
    No-op if DISCORD_WEBHOOK_URL is not set.
    """
    if not DISCORD_WEBHOOK_URL:
        return
    new_count = len(changes.get("new_ids", []))
    lost_count = len(changes.get("lost_ids", []))
    if new_count == 0 and lost_count == 0:
        return  # nothing notable to report

    fields = []
    if new_count:
        fields.append({
            "name": f"🟢 New Incentive Programs ({new_count})",
            "value": "\n".join(changes["new_ids"][:10]) or "—",
            "inline": False,
        })
    if lost_count:
        fields.append({
            "name": f"🔴 Ended Programs ({lost_count})",
            "value": "\n".join(changes["lost_ids"][:10]) or "—",
            "inline": False,
        })
    fields.append({
        "name": "Active Programs",
        "value": str(len(active_programs)),
        "inline": True,
    })

    notifier = get_notifier()
    ok = notifier.send_alert(
        "🏆 Kalshi Incentive Program Update",
        f"{new_count} new / {lost_count} ended incentive program(s).",
        alert_type="INFO",
        enrich=True,
        fields=fields,
    )
    if ok:
        logger.info("🔔 [kalshi_rewards] Discord alert sent")
    else:
        logger.warning("⚠️ [kalshi_rewards] Discord alert failed or rate-limited")


# ── Summarise a program list ───────────────────────────────────────────────────

@beartype
def summarise_programs(programs: list) -> list:
    """
    Extract a compact summary from raw API program objects.

    Returns a list of dicts with human-readable fields.
    """
    out = []
    for prog in programs:
        out.append({
            "id": prog.get("id", ""),
            "market_ticker": prog.get("market_ticker", ""),
            "series_ticker": prog.get("series_ticker", ""),
            "incentive_type": prog.get("incentive_type", ""),
            "start_date": prog.get("start_date", ""),
            "end_date": prog.get("end_date", ""),
            "period_reward_cents": prog.get("period_reward", 0),
            "paid_out": prog.get("paid_out", False),
            "target_size": prog.get("target_size"),
            "discount_factor_bps": prog.get("discount_factor_bps"),
        })
    return out


# ── Main ───────────────────────────────────────────────────────────────────────

def run() -> dict:
    """
    Execute one full rewards check cycle.

    Returns the payload dict published to Redis (useful for testing).
    """
    logger.info("🏆 [kalshi_rewards] Starting Kalshi rewards check")

    if not KALSHI_API_KEY:
        logger.error("❌ [kalshi_rewards] KALSHI_API_KEY not set — aborting")
        return {}

    private_key = _load_private_key(KALSHI_PRIVATE_KEY_PATH)
    if private_key is None:
        logger.error("❌ [kalshi_rewards] Could not load private key — aborting")
        return {}

    # 1. Fetch active incentive programs (both types)
    active_raw = fetch_incentive_programs(KALSHI_API_KEY, private_key, status="active")

    # 2. Fetch recently paid-out programs (last closed period)
    paid_out_raw = fetch_incentive_programs(
        KALSHI_API_KEY, private_key, status="paid_out", limit=20
    )

    # 3. Fetch upcoming programs
    upcoming_raw = fetch_incentive_programs(
        KALSHI_API_KEY, private_key, status="upcoming", limit=50
    )

    # 4. Balance snapshot
    balance_data = fetch_balance(KALSHI_API_KEY, private_key)

    # 5. Change detection vs previous run
    current_ids = [p.get("id", "") for p in active_raw]
    try:
        r = _sync_client()
        prev_ids = _load_prev_ids(r)
        changes = detect_changes(current_ids, prev_ids)
        _save_prev_ids(r, current_ids)
        r.close()
    except Exception as exc:
        logger.warning("⚠️ [kalshi_rewards] Redis state read failed: %s", exc)
        prev_ids = []
        changes = {"new_ids": [], "lost_ids": []}

    if changes["new_ids"]:
        logger.info("🆕 [kalshi_rewards] New programs detected: %s", changes["new_ids"])
    if changes["lost_ids"]:
        logger.info("📭 [kalshi_rewards] Programs ended/paid-out: %s", changes["lost_ids"])

    # 6. Build payload
    payload: dict = {
        "active_promotions": summarise_programs(active_raw),
        "recently_paid_out": summarise_programs(paid_out_raw[:5]),
        "upcoming_programs": summarise_programs(upcoming_raw[:10]),
        "unclaimed_rewards": {
            # Kalshi does not expose per-account accrued reward balance.
            # Actual payouts appear in portfolio/balance after paid_out=true.
            "note": "No per-account accrual API — payouts reflected in balance_cents",
            **balance_data,
        },
        "program_counts": {
            "active": len(active_raw),
            "recently_paid_out": len(paid_out_raw),
            "upcoming": len(upcoming_raw),
        },
        "changes": changes,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # 7. Publish to Redis
    publish_to_redis(payload)

    # 8. Archive to JSONL
    write_jsonl(payload)

    # 9. Discord alert on changes
    send_discord_alert(changes, active_raw)

    total = len(active_raw)
    logger.info(
        "✅ [kalshi_rewards] Done — %d active programs, %d new, %d ended",
        total, len(changes["new_ids"]), len(changes["lost_ids"]),
    )
    return payload


if __name__ == "__main__":
    run()
