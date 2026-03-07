"""
opportunity_screener/discovery_logger.py — Discovery Audit Logger (Step 26.1f)

Writes every conviction update/promotion/demotion to:
  1. Postgres (batched, flush every 30s or 100 entries)
  2. JSONL archive at /mnt/archive/discovery/discovery_YYYYMMDD.jsonl

This is critical infrastructure for Step 7 (RL Training Loop).
"""
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from beartype import beartype

from opportunity_screener.config import (
    SCREENER_AUDIT_FLUSH_BATCH_SIZE,
    SCREENER_AUDIT_FLUSH_SECONDS,
)

logger = logging.getLogger("screener.discovery_logger")

_ARCHIVE_DIR = Path(os.getenv("ARCHIVE_DIR", "/mnt/archive/discovery"))
_POSTGRES_INSERT = """
INSERT INTO discovery_audit_log (
    timestamp, ticker, action, conviction_before, conviction_after,
    source_channel, extraction_confidence, likelihood_ratio,
    multi_source_bonus, payload, watchlist_size
) VALUES (
    to_timestamp(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s
)
"""


class DiscoveryLogger:
    """
    Buffered audit logger.

    Flushes to Postgres + JSONL:
      - when buffer reaches SCREENER_AUDIT_FLUSH_BATCH_SIZE entries
      - when SCREENER_AUDIT_FLUSH_SECONDS seconds have elapsed since last flush
    """

    def __init__(self, db_conn=None):
        self._db = db_conn  # psycopg2 connection or None
        self._buffer: list[dict[str, Any]] = []
        self._last_flush = time.time()

    @beartype
    def log(
        self,
        ticker: str,
        action: str,
        conviction_before: Optional[float] = None,
        conviction_after: Optional[float] = None,
        source_channel: Optional[str] = None,
        extraction_confidence: Optional[float] = None,
        likelihood_ratio: Optional[float] = None,
        multi_source_bonus: bool = False,
        payload: Optional[dict] = None,
        watchlist_size: Optional[int] = None,
    ) -> None:
        """Buffer one audit record. Flushes if thresholds exceeded."""
        record = {
            "timestamp": time.time(),
            "ticker": ticker,
            "action": action,
            "conviction_before": conviction_before,
            "conviction_after": conviction_after,
            "source_channel": source_channel,
            "extraction_confidence": extraction_confidence,
            "likelihood_ratio": likelihood_ratio,
            "multi_source_bonus": multi_source_bonus,
            "payload": payload,
            "watchlist_size": watchlist_size,
        }
        self._buffer.append(record)
        if self._should_flush():
            self.flush()

    def _should_flush(self) -> bool:
        if len(self._buffer) >= SCREENER_AUDIT_FLUSH_BATCH_SIZE:
            return True
        if time.time() - self._last_flush >= SCREENER_AUDIT_FLUSH_SECONDS:
            return True
        return False

    def flush(self) -> int:
        """Write buffered records to Postgres + JSONL. Returns count written."""
        if not self._buffer:
            return 0
        batch = self._buffer[:]
        self._buffer = []
        self._last_flush = time.time()

        written = 0
        # Write JSONL first (lower risk of data loss)
        try:
            written += self._write_jsonl(batch)
        except Exception as exc:
            logger.warning("JSONL flush failed: %s", exc)

        # Write Postgres
        try:
            self._write_postgres(batch)
        except Exception as exc:
            logger.warning("Postgres flush failed: %s", exc)

        logger.debug("Audit flush: %d records written", written)
        return written

    def _write_jsonl(self, batch: list[dict]) -> int:
        _ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        path = _ARCHIVE_DIR / f"discovery_{date_str}.jsonl"
        count = 0
        with open(path, "a") as f:
            for record in batch:
                line = json.dumps(record, default=str)
                f.write(line + "\n")
                count += 1
        return count

    def _write_postgres(self, batch: list[dict]) -> None:
        if self._db is None:
            return
        cur = self._db.cursor()
        try:
            for r in batch:
                cur.execute(
                    _POSTGRES_INSERT,
                    (
                        r["timestamp"],
                        r["ticker"],
                        r["action"],
                        r["conviction_before"],
                        r["conviction_after"],
                        r["source_channel"],
                        r["extraction_confidence"],
                        r["likelihood_ratio"],
                        r["multi_source_bonus"],
                        json.dumps(r["payload"]) if r["payload"] else None,
                        r["watchlist_size"],
                    ),
                )
            self._db.commit()
        except Exception as exc:
            self._db.rollback()
            raise exc
        finally:
            cur.close()
