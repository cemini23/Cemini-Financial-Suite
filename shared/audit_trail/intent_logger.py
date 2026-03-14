"""Cemini Financial Suite — Pre-Evaluation Intent Logger (Step 43).

Logs the INTENT to evaluate a signal BEFORE processing it.
This proves the system is not cherry-picking profitable trades —
every evaluation attempt is recorded, win or lose.

Writes to:
  1. Postgres ``audit_intent_log`` table
  2. JSONL at /mnt/archive/audit/intents/YYYY-MM-DD.jsonl

Fail-silent — never raises, never blocks the caller.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from shared.audit_trail.hasher import canonicalize, sha256_hex
from shared.audit_trail.models import IntentRecord

logger = logging.getLogger("audit_trail.intent_logger")

_ARCHIVE_ROOT_DEFAULT = "/mnt/archive/audit"


def _archive_root() -> str:
    return os.getenv("AUDIT_ARCHIVE_DIR", _ARCHIVE_ROOT_DEFAULT)

_INSERT_SQL = """
INSERT INTO audit_intent_log (id, signal_source, signal_type, ticker, intent_hash, created_at)
VALUES (%s, %s, %s, %s, %s, %s)
"""

# ── optional deps ──────────────────────────────────────────────────────────────
try:
    import psycopg2
    _PG_AVAILABLE = True
except ImportError:
    _PG_AVAILABLE = False

try:
    from uuid_utils import uuid7 as _uuid7
    _UUID7_AVAILABLE = True
except ImportError:
    import uuid as _uuid_std
    _UUID7_AVAILABLE = False


def _new_uuid7() -> str:
    if _UUID7_AVAILABLE:
        return str(_uuid7())
    return str(_uuid_std.uuid1())  # type: ignore[attr-defined]


def _pg_conn():
    import psycopg2 as pg
    return pg.connect(
        host=os.getenv("DB_HOST", "postgres"),
        port=5432,
        user=os.getenv("POSTGRES_USER", "admin"),
        password=os.getenv("POSTGRES_PASSWORD", "quest"),
        dbname=os.getenv("POSTGRES_DB", "qdb"),
        connect_timeout=3,
    )


def log_intent(
    signal_source: str,
    signal_type: str,
    ticker: Optional[str] = None,
    extra: Optional[dict] = None,
) -> Optional[IntentRecord]:
    """Log pre-evaluation intent.  Returns IntentRecord on success, None on error.

    Call this BEFORE running the detector — the timestamp proves evaluation order.
    """
    try:
        intent_payload: dict = {
            "signal_source": signal_source,
            "signal_type": signal_type,
            "ticker": ticker,
        }
        if extra:
            intent_payload["extra"] = extra
        canonical = canonicalize(intent_payload)
        i_hash = sha256_hex(canonical)
        intent_id = _new_uuid7()
        created_at = time.time()
        created_ts = datetime.fromtimestamp(created_at, tz=timezone.utc)

        record = IntentRecord(
            intent_id=intent_id,
            signal_source=signal_source,
            signal_type=signal_type,
            ticker=ticker,
            intent_hash=i_hash,
            created_at=created_at,
        )

        _pg_write(record, created_ts)
        _jsonl_write(record)
        return record

    except Exception as exc:  # noqa: BLE001
        logger.debug("[IntentLogger] log_intent failed silently: %s", exc)
        return None


def _pg_write(record: IntentRecord, created_ts) -> None:
    if not _PG_AVAILABLE:
        return
    try:
        conn = _pg_conn()
        cur = conn.cursor()
        cur.execute(_INSERT_SQL, (
            record.intent_id,
            record.signal_source,
            record.signal_type,
            record.ticker,
            record.intent_hash,
            created_ts,
        ))
        conn.commit()
        conn.close()
    except Exception as exc:  # noqa: BLE001
        logger.debug("[IntentLogger] Postgres write failed: %s", exc)


def _jsonl_write(record: IntentRecord) -> None:
    try:
        date_str = datetime.fromtimestamp(record.created_at, tz=timezone.utc).strftime("%Y-%m-%d")
        intents_dir = Path(_archive_root()) / "intents"
        intents_dir.mkdir(parents=True, exist_ok=True)
        jsonl_path = intents_dir / f"{date_str}.jsonl"
        line = json.dumps(record.model_dump(), sort_keys=True, separators=(",", ":"))
        with jsonl_path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception as exc:  # noqa: BLE001
        logger.debug("[IntentLogger] JSONL write failed: %s", exc)
