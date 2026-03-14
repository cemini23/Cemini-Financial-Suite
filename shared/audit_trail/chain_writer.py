"""Cemini Financial Suite — Audit Chain Writer (Step 43).

Dual-output: writes each audit entry to:
  1. Postgres ``audit_hash_chain`` table (durable, queryable)
  2. JSONL file at /mnt/archive/audit/chains/YYYY-MM-DD.jsonl (offline-verifiable)
  3. Redis intel:audit_chain_entry (observability)

All methods fail silently — never raises, never blocks the caller.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from shared.audit_trail.hasher import canonicalize, sha256_hex, chain_hash, GENESIS_HASH
from shared.audit_trail.models import ChainEntry

logger = logging.getLogger("audit_trail.chain_writer")

_ARCHIVE_ROOT_DEFAULT = "/mnt/archive/audit"
INTEL_KEY = "intel:audit_chain_entry"
INTEL_TTL = 300


def _archive_root() -> str:
    return os.getenv("AUDIT_ARCHIVE_DIR", _ARCHIVE_ROOT_DEFAULT)

# ── optional deps ──────────────────────────────────────────────────────────────
try:
    import psycopg2
    _PG_AVAILABLE = True
except ImportError:
    _PG_AVAILABLE = False

try:
    import redis as _redis_lib
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False

import uuid as _uuid_std  # always imported for fallback

try:
    from uuid_utils import uuid7 as _uuid7
    _UUID7_AVAILABLE = True
except ImportError:
    _UUID7_AVAILABLE = False


def _new_uuid7() -> str:
    """Return a new UUIDv7 string. Falls back to uuid1 if uuid-utils unavailable."""
    if _UUID7_AVAILABLE:
        return str(_uuid7())
    return str(_uuid_std.uuid1())


def _pg_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        port=5432,
        user=os.getenv("POSTGRES_USER", "admin"),
        password=os.getenv("POSTGRES_PASSWORD", "quest"),
        dbname=os.getenv("POSTGRES_DB", "qdb"),
        connect_timeout=3,
    )


def _redis_client():
    host = os.getenv("REDIS_HOST", "redis")
    password = os.getenv("REDIS_PASSWORD", "cemini_redis_2026")
    return _redis_lib.Redis(
        host=host, port=6379, password=password,
        decode_responses=True, socket_connect_timeout=2,
    )


_INSERT_SQL = """
INSERT INTO audit_hash_chain
    (id, source_table, source_id, payload_canonical, payload_hash, prev_hash, chain_hash, created_at)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
RETURNING sequence_num;
"""


class ChainWriter:
    """Writes audit entries to Postgres + JSONL.  Fail-silent."""

    def write(
        self,
        source_table: str,
        source_id: str,
        payload: dict,
        pg_conn=None,
    ) -> Optional[ChainEntry]:
        """Write one audit entry.  Returns the ChainEntry on success, None on any error."""
        try:
            canonical = canonicalize(payload)
            p_hash = sha256_hex(canonical)
            entry_id = _new_uuid7()
            created_at = time.time()
            created_ts = datetime.fromtimestamp(created_at, tz=timezone.utc)

            # prev_hash and chain_hash are computed by the DB trigger.
            # We use GENESIS_HASH as a placeholder here; the trigger overwrites prev_hash.
            # chain_hash is also computed by the trigger — we pass the same placeholder
            # so the DB row is self-consistent after the trigger fires.
            # For the JSONL mirror we read back sequence_num from the DB RETURNING clause.
            sequence_num = self._pg_write(
                entry_id, source_table, source_id, canonical, p_hash, created_ts, pg_conn
            )

            if sequence_num is None:
                # If DB unavailable, still write JSONL with placeholder hashes
                sequence_num = -1
                prev_h = GENESIS_HASH
                c_hash = chain_hash(prev_h, p_hash)
            else:
                # Fetch the actual prev_hash + chain_hash the trigger computed
                prev_h, c_hash = self._fetch_hashes(entry_id, pg_conn)

            entry = ChainEntry(
                entry_id=entry_id,
                sequence_num=sequence_num,
                source_table=source_table,
                source_id=source_id,
                payload_canonical=canonical,
                payload_hash=p_hash,
                prev_hash=prev_h,
                chain_hash=c_hash,
                created_at=created_at,
            )

            self._jsonl_write(entry)
            self._redis_publish(entry)
            return entry

        except Exception as exc:  # noqa: BLE001
            logger.debug("[ChainWriter] write failed silently: %s", exc)
            return None

    def _pg_write(
        self,
        entry_id: str,
        source_table: str,
        source_id: str,
        canonical: str,
        p_hash: str,
        created_ts,
        pg_conn=None,
    ) -> Optional[int]:
        if not _PG_AVAILABLE:
            return None
        try:
            conn = pg_conn or _pg_conn()
            own_conn = pg_conn is None
            cur = conn.cursor()
            # prev_hash and chain_hash are filled by the BEFORE INSERT trigger
            cur.execute(_INSERT_SQL, (
                entry_id, source_table, source_id, canonical, p_hash,
                GENESIS_HASH,  # trigger overwrites this
                GENESIS_HASH,  # trigger overwrites this
                created_ts,
            ))
            row = cur.fetchone()
            if own_conn:
                conn.commit()
                conn.close()
            return row[0] if row else None
        except Exception as exc:  # noqa: BLE001
            logger.debug("[ChainWriter] Postgres write failed: %s", exc)
            return None

    def _fetch_hashes(self, entry_id: str, pg_conn=None):
        """Fetch trigger-computed prev_hash + chain_hash for this entry."""
        if not _PG_AVAILABLE:
            return GENESIS_HASH, GENESIS_HASH
        try:
            conn = pg_conn or _pg_conn()
            own_conn = pg_conn is None
            cur = conn.cursor()
            cur.execute(
                "SELECT prev_hash, chain_hash FROM audit_hash_chain WHERE id = %s",
                (entry_id,),
            )
            row = cur.fetchone()
            if own_conn:
                conn.close()
            if row:
                return row[0], row[1]
        except Exception as exc:  # noqa: BLE001
            logger.debug("[ChainWriter] fetch_hashes failed: %s", exc)
        return GENESIS_HASH, GENESIS_HASH

    def _jsonl_write(self, entry: ChainEntry) -> None:
        try:
            date_str = datetime.fromtimestamp(entry.created_at, tz=timezone.utc).strftime("%Y-%m-%d")
            chains_dir = Path(_archive_root()) / "chains"
            chains_dir.mkdir(parents=True, exist_ok=True)
            jsonl_path = chains_dir / f"{date_str}.jsonl"
            line = json.dumps(entry.model_dump(), sort_keys=True, separators=(",", ":"))
            with jsonl_path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except Exception as exc:  # noqa: BLE001
            logger.debug("[ChainWriter] JSONL write failed: %s", exc)

    def _redis_publish(self, entry: ChainEntry) -> None:
        if not _REDIS_AVAILABLE:
            return
        try:
            rc = _redis_client()
            payload = {
                "value": {
                    "entry_id": entry.entry_id,
                    "source_table": entry.source_table,
                    "sequence_num": entry.sequence_num,
                    "chain_hash": entry.chain_hash,
                },
                "source_system": "audit_trail",
                "timestamp": time.time(),
                "confidence": 1.0,
            }
            rc.set(INTEL_KEY, json.dumps(payload), ex=INTEL_TTL)
        except Exception as exc:  # noqa: BLE001
            logger.debug("[ChainWriter] Redis publish failed: %s", exc)


# Module-level singleton — import and call write() directly
_writer = ChainWriter()


def write_audit_entry(
    source_table: str,
    source_id: str,
    payload: dict,
    pg_conn=None,
) -> Optional[ChainEntry]:
    """Convenience wrapper around ChainWriter.write()."""
    return _writer.write(source_table, source_id, payload, pg_conn=pg_conn)
