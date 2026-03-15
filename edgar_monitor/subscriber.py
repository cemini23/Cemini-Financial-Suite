"""Cemini Financial Suite — EDGAR Monitor Subscriber (Step 17).

Polls intel:edgar_filing and intel:edgar_insider on a schedule, scores each
event, and publishes intel:edgar_alert for high-significance filings.

Integration:
  - Reads from:    intel:edgar_filing, intel:edgar_insider (SET by Step 40)
  - Publishes to:  intel:edgar_alert  (SET with TTL)
  - Writes to:     edgar_alerts Postgres table
  - Archives at:   /mnt/archive/edgar_alerts/YYYY-MM-DD.jsonl
  - Audit chain:   shared.audit_trail.chain_writer (source_table="edgar_alerts")
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Repo root ──────────────────────────────────────────────────────────────────
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

try:
    import redis as redis_lib
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False

try:
    import psycopg2
    _PG_AVAILABLE = True
except ImportError:
    _PG_AVAILABLE = False

try:
    import uuid_utils
    def _new_uuid() -> str:
        return str(uuid_utils.uuid7())
except ImportError:
    import uuid
    def _new_uuid() -> str:
        return str(uuid.uuid4())

from edgar_monitor.alert_rules import ALERT_THRESHOLD, score_filing
from edgar_monitor.insider_cluster import InsiderTrade, detect_clusters
from edgar_monitor.metric_extractor import extract_8k_metrics
from edgar_monitor.models import EdgarAlert, InsiderCluster

logger = logging.getLogger("edgar_monitor.subscriber")

ALERT_CHANNEL = "intel:edgar_alert"
ALERT_TTL = 3600  # 1 hour — significant enough to persist longer than source TTL

ARCHIVE_ROOT_DEFAULT = "/mnt/archive/edgar_alerts"

# ── Config ─────────────────────────────────────────────────────────────────────
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "cemini_redis_2026")
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_USER = os.getenv("POSTGRES_USER", "admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "quest")
DB_NAME = os.getenv("POSTGRES_DB", "qdb")


def _archive_root() -> str:
    return os.getenv("EDGAR_ALERT_ARCHIVE_DIR", ARCHIVE_ROOT_DEFAULT)


def _redis_client():
    return redis_lib.Redis(
        host=REDIS_HOST, port=6379, password=REDIS_PASSWORD,
        decode_responses=True, socket_connect_timeout=2,
    )


def _read_intel(key: str) -> Optional[dict]:
    """Read one Intel Bus key. Returns the full envelope or None."""
    if not _REDIS_AVAILABLE:
        return None
    try:
        rdb = _redis_client()
        try:
            raw = rdb.get(key)
        finally:
            rdb.close()
        return json.loads(raw) if raw else None
    except Exception as exc:  # noqa: BLE001
        logger.debug("Intel read failed (%s): %s", key, exc)
        return None


def _publish_alert(alert: EdgarAlert) -> None:
    """Publish EdgarAlert to intel:edgar_alert (SET with TTL)."""
    if not _REDIS_AVAILABLE:
        return
    try:
        rdb = _redis_client()
        try:
            rdb.set(ALERT_CHANNEL, json.dumps(alert.to_intel_envelope(), default=str), ex=ALERT_TTL)
            logger.info("Published alert: %s score=%d [%s]", alert.ticker, alert.significance_score, alert.alert_type)
        finally:
            rdb.close()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Alert publish failed: %s", exc)


def _write_to_postgres(alert: EdgarAlert, conn) -> None:
    """Insert alert into edgar_alerts table."""
    if conn is None:
        return
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO edgar_alerts (id, ticker, alert_type, significance_score, summary, filing_url, payload, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (
                    alert.alert_id,
                    alert.ticker,
                    alert.alert_type,
                    alert.significance_score,
                    alert.summary,
                    alert.filing_url,
                    json.dumps(alert.payload, default=str),
                    alert.created_at,
                ),
            )
            conn.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("edgar_alerts INSERT failed: %s", exc)
        try:
            conn.rollback()
        except Exception:  # noqa: BLE001
            pass


def _write_to_jsonl(alert: EdgarAlert) -> None:
    """Append alert to daily JSONL archive."""
    try:
        root = Path(_archive_root())
        root.mkdir(parents=True, exist_ok=True)
        date_str = alert.created_at.strftime("%Y-%m-%d")
        path = root / f"{date_str}.jsonl"
        with path.open("a") as fh:
            fh.write(json.dumps(alert.model_dump(mode="json"), default=str) + "\n")
    except Exception as exc:  # noqa: BLE001
        logger.warning("JSONL write failed: %s", exc)


def _write_to_audit_chain(alert: EdgarAlert, conn) -> None:
    """Write alert to cryptographic audit hash chain."""
    try:
        from shared.audit_trail.chain_writer import write_audit_entry
        write_audit_entry(
            source_table="edgar_alerts",
            source_id=alert.alert_id,
            payload=alert.model_dump(mode="json"),
            pg_conn=conn,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("Audit chain write skipped: %s", exc)


def _emit_alert(alert: EdgarAlert, conn) -> None:
    """Full alert emission: Redis + Postgres + JSONL + audit chain."""
    _publish_alert(alert)
    _write_to_postgres(alert, conn)
    _write_to_jsonl(alert)
    _write_to_audit_chain(alert, conn)


# ── State tracking — avoid re-alerting on same accession ──────────────────────
_seen_accessions: set[str] = set()
_MAX_SEEN = 1000  # cap memory usage


def _is_seen(accession: str) -> bool:
    return accession in _seen_accessions


def _mark_seen(accession: str) -> None:
    if len(_seen_accessions) >= _MAX_SEEN:
        # Drop oldest half
        keep = list(_seen_accessions)[-(_MAX_SEEN // 2):]
        _seen_accessions.clear()
        _seen_accessions.update(keep)
    _seen_accessions.add(accession)


# ── Filing alert logic ─────────────────────────────────────────────────────────

def process_filing_payload(payload: dict, conn=None) -> Optional[EdgarAlert]:
    """Score a filing payload and emit an alert if score >= threshold.

    Args:
        payload: Filing dict with keys: ticker, cik, form_type, accession_number,
                 description, filed_at.
        conn:    Optional psycopg2 connection for Postgres writes.

    Returns:
        EdgarAlert if threshold was met, else None.
    """
    ticker = payload.get("ticker", "")
    cik = payload.get("cik", "")
    form_type = payload.get("form_type", "")
    accession = payload.get("accession_number", "")
    description = payload.get("description", "")
    filing_url = payload.get("filing_url")

    if not accession or _is_seen(accession):
        return None

    # Parse filed_at
    filed_at = None
    raw_filed = payload.get("filed_at")
    if raw_filed:
        try:
            if isinstance(raw_filed, (int, float)):
                filed_at = datetime.fromtimestamp(raw_filed, tz=timezone.utc)
            else:
                filed_at = datetime.fromisoformat(str(raw_filed))
        except (ValueError, TypeError):
            pass

    significance = score_filing(
        ticker=ticker,
        cik=cik,
        form_type=form_type,
        accession_number=accession,
        description=description,
        filed_at=filed_at,
    )

    _mark_seen(accession)

    if not significance.alert_triggered:
        return None

    metrics = extract_8k_metrics(payload)
    event_type = metrics.get("event_type", "filing")
    alert_type = f"filing_{event_type}" if form_type in ("8-K", "8-K/A") else "filing_significance"

    summary = (
        f"{form_type} filing for {ticker} — significance score {significance.significance_score}/100"
        + (f" [{event_type}]" if event_type else "")
    )

    alert = EdgarAlert(
        alert_id=_new_uuid(),
        ticker=ticker,
        alert_type=alert_type,
        significance_score=significance.significance_score,
        summary=summary,
        filing_url=filing_url,
        payload={
            "filing": payload,
            "significance": significance.model_dump(),
            "metrics": metrics,
        },
    )

    _emit_alert(alert, conn)
    return alert


# ── Insider cluster alert logic ────────────────────────────────────────────────

def process_insider_payload(payload: dict, conn=None) -> Optional[EdgarAlert]:
    """Check a new insider trade payload for cluster patterns.

    Builds a minimal trade list from the payload (single trade) and the recently
    seen trades cache, then calls detect_clusters.

    Note: With only one trade available from the Redis key, single-trade clusters
    cannot form. Full cluster detection requires querying edgar_filings_log —
    implemented in run_monitor_cycle() which passes a richer trade list.

    Args:
        payload: Insider dict from intel:edgar_insider.
        conn:    Optional psycopg2 connection.

    Returns:
        EdgarAlert for the cluster if detected, else None.
    """
    ticker = payload.get("ticker", "")
    accession = payload.get("accession_number", "")

    if not accession or _is_seen(accession):
        return None

    _mark_seen(accession)

    # Build a single InsiderTrade from the payload
    raw_filed = payload.get("filed_at")
    filed_at = datetime.now(tz=timezone.utc)
    if raw_filed:
        try:
            if isinstance(raw_filed, (int, float)):
                filed_at = datetime.fromtimestamp(raw_filed, tz=timezone.utc)
            else:
                filed_at = datetime.fromisoformat(str(raw_filed))
        except (ValueError, TypeError):
            pass

    trade = InsiderTrade(
        ticker=ticker,
        cik=payload.get("cik", ""),
        insider_name=payload.get("insider_name", "Unknown"),
        title=payload.get("title", ""),
        transaction_type=payload.get("transaction_type", "P"),
        shares=float(payload.get("shares", 0)),
        price_per_share=float(payload.get("price_per_share") or 0),
        total_value=float(payload.get("total_value") or 0),
        filed_at=filed_at,
    )

    # For single-trade calls, cluster cannot be detected without historical context
    # The caller (run_monitor_cycle) should pass the full recent trade list.
    return None  # Cluster detection happens in run_monitor_cycle()


def emit_cluster_alert(cluster: InsiderCluster, conn=None) -> EdgarAlert:
    """Build and emit an EdgarAlert for a detected insider cluster."""
    title_note = " (incl. CEO/CFO)" if cluster.includes_ceo_cfo else ""
    summary = (
        f"Insider buying cluster: {cluster.insider_count} insiders at {cluster.ticker}"
        f"{title_note} — ${cluster.total_value:,.0f} total — score {cluster.cluster_score}/100"
    )

    alert = EdgarAlert(
        alert_id=_new_uuid(),
        ticker=cluster.ticker,
        alert_type="insider_cluster",
        significance_score=cluster.cluster_score,
        summary=summary,
        payload=cluster.model_dump(mode="json"),
    )

    _emit_alert(alert, conn)
    return alert


# ── Main monitor cycle ─────────────────────────────────────────────────────────

def run_monitor_cycle(conn=None) -> dict:
    """One monitor cycle: poll both intel channels and process events.

    Returns a summary dict with counts of alerts fired.
    """
    filing_alerts = 0
    cluster_alerts = 0

    # ── Process latest filing ──────────────────────────────────────────────
    filing_envelope = _read_intel("intel:edgar_filing")
    if filing_envelope:
        payload = filing_envelope.get("value", {})
        if isinstance(payload, dict):
            alert = process_filing_payload(payload, conn=conn)
            if alert:
                filing_alerts += 1

    # ── Process latest insider trade + cluster scan ────────────────────────
    insider_envelope = _read_intel("intel:edgar_insider")
    if insider_envelope:
        payload = insider_envelope.get("value", {})
        if isinstance(payload, dict) and payload.get("accession_number"):
            accession = payload["accession_number"]
            if not _is_seen(accession):
                _mark_seen(accession)

                # Build trade from payload for cluster scan
                raw_filed = payload.get("filed_at")
                filed_at = datetime.now(tz=timezone.utc)
                if raw_filed:
                    try:
                        if isinstance(raw_filed, (int, float)):
                            filed_at = datetime.fromtimestamp(raw_filed, tz=timezone.utc)
                        else:
                            filed_at = datetime.fromisoformat(str(raw_filed))
                    except (ValueError, TypeError):
                        pass

                new_trade = InsiderTrade(
                    ticker=payload.get("ticker", ""),
                    cik=payload.get("cik", ""),
                    insider_name=payload.get("insider_name", "Unknown"),
                    title=payload.get("title", ""),
                    transaction_type=payload.get("transaction_type", "P"),
                    shares=float(payload.get("shares", 0)),
                    price_per_share=float(payload.get("price_per_share") or 0),
                    total_value=float(payload.get("total_value") or 0),
                    filed_at=filed_at,
                )

                # Gather recent trades from Postgres if available
                recent_trades = _fetch_recent_insider_trades(payload.get("ticker", ""), conn)
                all_trades = recent_trades + [new_trade]

                clusters = detect_clusters(all_trades)
                for cluster in clusters:
                    emit_cluster_alert(cluster, conn=conn)
                    cluster_alerts += 1

    return {"filing_alerts": filing_alerts, "cluster_alerts": cluster_alerts}


def _fetch_recent_insider_trades(ticker: str, conn) -> list[InsiderTrade]:
    """Query edgar_filings_log for recent Form 4 purchases (last 14 days)."""
    if conn is None or not ticker:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ticker, cik, filing_url, filed_at
                FROM edgar_filings_log
                WHERE ticker = %s AND form_type = '4'
                  AND filed_at >= NOW() - INTERVAL '14 days'
                ORDER BY filed_at ASC
                LIMIT 50
                """,
                (ticker,),
            )
            rows = cur.fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.debug("Recent insider query failed: %s", exc)
        return []

    trades = []
    for row in rows:
        ticker_r, cik_r, url_r, filed_at_r = row
        # Build minimal InsiderTrade — name is accession (sufficient for cluster key)
        trades.append(InsiderTrade(
            ticker=ticker_r,
            cik=cik_r or "",
            insider_name=url_r or "db_record",
            title="",
            transaction_type="P",
            shares=0.0,
            price_per_share=0.0,
            total_value=0.0,
            filed_at=filed_at_r if filed_at_r else datetime.now(tz=timezone.utc),
        ))
    return trades
