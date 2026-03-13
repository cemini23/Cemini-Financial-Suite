"""Cemini Financial Suite — FRED Macro Data Monitor (Step 39).

Polls the Federal Reserve Economic Data (FRED) API for key macro series,
publishes intelligence to Redis intel:fred_* channels, stores snapshots
in PostgreSQL fred_observations table, and archives to JSONL.

Poll interval : 900s (15 min)
Redis TTL     : 1800s (2× poll interval — see LESSONS.md Redis TTL mismatch)
Rate limit    : 0.6s sleep between API calls (well under 120 req/min)
FRED sentinel : FRED returns '.' for missing/unreported values → stored as NULL

Series covered
--------------
Yield curve  : T10Y2Y, T10Y3M
Fed policy   : DFF, WALCL
Credit spread: BAMLH0A0HYM2
Labor market : ICSA, UNRATE, PAYEMS
Inflation    : PCEPI, CPILFESL
Sentiment    : UMCSENT, VIXCLS
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone

import psycopg2
import redis
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [FRED] %(levelname)s %(message)s",
)
logger = logging.getLogger("fred_monitor")

# ── Constants ──────────────────────────────────────────────────────────────────
FRED_POLL_INTERVAL = 900       # 15 minutes between poll cycles
FRED_TTL = 1800                # Redis key TTL — must be >= 2× FRED_POLL_INTERVAL
FRED_BACKFILL_DAYS = 90        # Days to backfill on startup
FRED_RATE_LIMIT_SLEEP = 0.6   # Seconds between API calls (conservative vs 120/min)
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
ARCHIVE_DIR = "/mnt/archive/fred"

# ── FRED Series Configuration ──────────────────────────────────────────────────
FRED_SERIES = {
    # Yield curve (recession predictors)
    "T10Y2Y": {"channel": "intel:fred_yield_curve", "field": "spread_10y2y", "freq": "daily"},
    "T10Y3M": {"channel": "intel:fred_yield_curve", "field": "spread_10y3m", "freq": "daily"},
    # Fed policy / liquidity
    "DFF": {"channel": "intel:fred_fed_policy", "field": "fed_funds_rate", "freq": "daily"},
    "WALCL": {"channel": "intel:fred_fed_policy", "field": "fed_balance_sheet_mm", "freq": "weekly"},
    # Credit spreads (risk-on/risk-off)
    "BAMLH0A0HYM2": {"channel": "intel:fred_credit_spread", "field": "hy_oas_spread", "freq": "daily"},
    # Labor market
    "ICSA": {"channel": "intel:fred_labor", "field": "initial_claims", "freq": "weekly"},
    "UNRATE": {"channel": "intel:fred_labor", "field": "unemployment_rate", "freq": "monthly"},
    "PAYEMS": {"channel": "intel:fred_labor", "field": "nonfarm_payrolls_k", "freq": "monthly"},
    # Inflation
    "PCEPI": {"channel": "intel:fred_inflation", "field": "pce_index", "freq": "monthly"},
    "CPILFESL": {"channel": "intel:fred_inflation", "field": "core_cpi_index", "freq": "monthly"},
    # Sentiment
    "UMCSENT": {"channel": "intel:fred_sentiment", "field": "michigan_sentiment", "freq": "monthly"},
    "VIXCLS": {"channel": "intel:fred_sentiment", "field": "vix_close", "freq": "daily"},
}

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "cemini_redis_2026")
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "quest")


# ── Redis / Postgres helpers ───────────────────────────────────────────────────

def _get_redis():
    return redis.Redis(
        host=REDIS_HOST,
        port=6379,
        password=REDIS_PASSWORD,
        decode_responses=True,
    )


def _get_db_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=5432,
        user=os.getenv("POSTGRES_USER", "admin"),
        password=DB_PASSWORD,
        database=os.getenv("POSTGRES_DB", "qdb"),
    )


# ── FRED API helpers ───────────────────────────────────────────────────────────

def _build_fred_url(
    series_id: str,
    api_key: str,
    observation_start: str = None,
    limit: int = 5,
) -> str:
    """Construct FRED API URL for series observations."""
    url = (
        f"{FRED_BASE_URL}?series_id={series_id}&api_key={api_key}"
        f"&file_type=json&sort_order=desc&limit={limit}"
    )
    if observation_start:
        url += f"&observation_start={observation_start}"
    return url


def _parse_fred_value(raw) -> "float | None":
    """FRED returns '.' for missing/unreported values — convert to None."""
    if raw is None:
        return None
    s = str(raw).strip()
    if s == "." or s == "":
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _fetch_series(
    series_id: str,
    api_key: str,
    observation_start: str = None,
    limit: int = 5,
) -> list:
    """Fetch observations from FRED API.

    Returns list of {"date": "YYYY-MM-DD", "value": float|None} dicts.
    Returns empty list on any error (caller continues to next series).
    """
    url = _build_fred_url(series_id, api_key, observation_start, limit)
    try:
        # nosemgrep: semgrep.missing-rate-limit-requests — caller enforces FRED_RATE_LIMIT_SLEEP
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        observations = resp.json().get("observations", [])
        return [
            {"date": obs["date"], "value": _parse_fred_value(obs.get("value", "."))}
            for obs in observations
        ]
    except requests.exceptions.HTTPError as exc:
        logger.warning("FRED HTTP error for %s: %s", series_id, exc)
        return []
    except Exception as exc:
        logger.warning("FRED fetch error for %s: %s", series_id, exc)
        return []


# ── Database helpers ───────────────────────────────────────────────────────────

def _store_observations(cursor, series_id: str, observations: list) -> int:
    """INSERT observations with ON CONFLICT DO NOTHING for idempotency.

    Returns number of rows actually inserted.
    """
    count = 0
    for obs in observations:
        if not obs.get("date"):
            continue
        cursor.execute(
            """
            INSERT INTO fred_observations (series_id, observation_date, value, fetched_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (series_id, observation_date) DO NOTHING
            """,
            (series_id, obs["date"], obs["value"]),
        )
        count += cursor.rowcount
    return count


# ── Redis publish helpers ──────────────────────────────────────────────────────

def _group_by_channel(observations_by_series: dict) -> dict:
    """Group latest observations by Redis channel.

    observations_by_series: {series_id: [{"date": str, "value": float|None}, ...]}
    Returns: {channel: {"field_name": value, "observation_date": str, "source": str}}
    """
    channels: dict = {}
    for series_id, config in FRED_SERIES.items():
        obs_list = observations_by_series.get(series_id, [])
        if not obs_list:
            continue
        latest = obs_list[0]  # sort_order=desc → first is newest
        if latest["value"] is None:
            continue
        channel = config["channel"]
        field = config["field"]
        if channel not in channels:
            channels[channel] = {"observation_date": latest["date"], "source": "fred"}
        channels[channel][field] = latest["value"]
        # Keep the most recent observation_date across fields for this channel
        if latest["date"] > channels[channel].get("observation_date", ""):
            channels[channel]["observation_date"] = latest["date"]
    return channels


def _publish_to_redis(r, channel: str, payload: dict) -> None:
    """Publish FRED intel to Redis with TTL=FRED_TTL.

    Uses IntelPublisher envelope format for cross-service compatibility.
    TTL is explicitly FRED_TTL (2× FRED_POLL_INTERVAL) — see LESSONS.md.
    """
    envelope = json.dumps({
        "value": payload,
        "source_system": "fred_monitor",
        "timestamp": time.time(),
        "confidence": 1.0,
    })
    try:
        r.set(channel, envelope, ex=FRED_TTL)
        logger.debug("Published %d fields to %s (TTL=%ds)", len(payload), channel, FRED_TTL)
    except Exception as exc:
        logger.warning("Redis publish failed for %s: %s", channel, exc)


# ── Archive helper ─────────────────────────────────────────────────────────────

def _archive_observation(series_id: str, date: str, value) -> None:
    """Append a single observation to the daily JSONL archive."""
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    today = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
    path = os.path.join(ARCHIVE_DIR, f"fred_{today}.jsonl")
    record = {
        "series_id": series_id,
        "observation_date": date,
        "value": value,
        "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    try:
        with open(path, "a") as fh:
            fh.write(json.dumps(record) + "\n")
    except Exception as exc:
        logger.warning("Archive write failed (%s): %s", path, exc)


# ── Core logic ─────────────────────────────────────────────────────────────────

def backfill(cursor, api_key: str) -> None:
    """Backfill last FRED_BACKFILL_DAYS of data for all series (idempotent)."""
    start_date = (
        datetime.now(tz=timezone.utc) - timedelta(days=FRED_BACKFILL_DAYS)
    ).strftime("%Y-%m-%d")
    logger.info("📥 Backfilling %d days of FRED data (start=%s)…", FRED_BACKFILL_DAYS, start_date)
    for series_id in FRED_SERIES:
        try:
            obs = _fetch_series(series_id, api_key, observation_start=start_date, limit=200)
            inserted = _store_observations(cursor, series_id, obs)
            logger.info("  %s: %d fetched, %d new rows", series_id, len(obs), inserted)
        except Exception as exc:
            logger.warning("Backfill error for %s: %s", series_id, exc)
        time.sleep(FRED_RATE_LIMIT_SLEEP)


def poll_and_publish(cursor, r, api_key: str) -> None:
    """Fetch latest observations for all series, publish to Redis, store, archive."""
    observations_by_series: dict = {}
    for series_id in FRED_SERIES:
        obs = _fetch_series(series_id, api_key, limit=5)
        observations_by_series[series_id] = obs
        try:
            _store_observations(cursor, series_id, obs)
        except Exception as exc:
            logger.warning("DB store error for %s: %s", series_id, exc)
        for ob in obs[:1]:  # Archive only the latest observation per cycle
            _archive_observation(series_id, ob["date"], ob["value"])
        time.sleep(FRED_RATE_LIMIT_SLEEP)

    channel_data = _group_by_channel(observations_by_series)
    fetched_at = datetime.now(tz=timezone.utc).isoformat()
    for channel, payload in channel_data.items():
        payload["fetched_at"] = fetched_at
        _publish_to_redis(r, channel, payload)
        fields = {k: v for k, v in payload.items() if k not in ("fetched_at", "source", "observation_date")}
        logger.info("📡 %s → %s", channel, fields)


def _wait_for_postgres(max_attempts: int = 12):
    """Wait for Postgres with exponential backoff (max ~5 min)."""
    delay = 5
    for attempt in range(1, max_attempts + 1):
        try:
            conn = _get_db_conn()
            conn.autocommit = True
            return conn
        except Exception as exc:
            logger.warning(
                "Postgres not ready (attempt %d/%d): %s — retrying in %ds",
                attempt, max_attempts, exc, delay,
            )
            time.sleep(delay)
            delay = min(delay * 2, 300)
    raise RuntimeError(f"Could not connect to Postgres after {max_attempts} attempts")


def main() -> None:
    logger.info("🏦 FRED Macro Monitor starting (Step 39) — poll interval %ds, TTL %ds", FRED_POLL_INTERVAL, FRED_TTL)
    api_key = os.getenv("FRED_API_KEY", "")
    if not api_key:
        logger.warning("FRED_API_KEY not set — will retry every 60s until configured")

    conn = _wait_for_postgres()
    cursor = conn.cursor()
    r = _get_redis()

    if api_key:
        backfill(cursor, api_key)
    else:
        logger.warning("Skipping backfill — FRED_API_KEY not set")

    while True:
        api_key = os.getenv("FRED_API_KEY", "")
        if not api_key:
            logger.warning("FRED_API_KEY not set — sleeping 60s")
            time.sleep(60)
            continue
        try:
            poll_and_publish(cursor, r, api_key)
        except Exception as exc:
            logger.error("Poll cycle error: %s", exc)
        logger.info("💤 Next poll in %ds", FRED_POLL_INTERVAL)
        time.sleep(FRED_POLL_INTERVAL)


if __name__ == "__main__":
    main()
