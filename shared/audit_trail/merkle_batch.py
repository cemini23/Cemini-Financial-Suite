"""Cemini Financial Suite — Daily Merkle Batch Builder (Step 43).

Layer 2: RFC 6962-style Merkle tree via pymerkle.
Runs as an APScheduler cron job at 23:55 UTC.

Steps:
  1. Read today's JSONL chain from /mnt/archive/audit/chains/YYYY-MM-DD.jsonl
  2. Build InmemoryTree from pymerkle using each entry's payload_hash
  3. Write batches.json to /mnt/archive/audit/batches/YYYY-MM-DD/
  4. Insert BatchCommitment into audit_batch_commitments table
  5. Optionally stamp with OpenTimestamps (best-effort)
  6. Publish intel:audit_batch_complete

All methods fail silently where possible.
"""

import json
import logging
import os
import shutil
import subprocess
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from shared.audit_trail.models import BatchCommitment

logger = logging.getLogger("audit_trail.merkle_batch")

_ARCHIVE_ROOT_DEFAULT = "/mnt/archive/audit"
INTEL_KEY = "intel:audit_batch_complete"
INTEL_TTL = 86400  # 24h


def _archive_root() -> str:
    return os.getenv("AUDIT_ARCHIVE_DIR", _ARCHIVE_ROOT_DEFAULT)

_INSERT_SQL = """
INSERT INTO audit_batch_commitments
    (id, batch_date, merkle_root, entry_count,
     first_entry_id, last_entry_id, first_sequence, last_sequence, created_at)
VALUES (%s, %s::date, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (batch_date) DO UPDATE
SET merkle_root = EXCLUDED.merkle_root,
    entry_count = EXCLUDED.entry_count,
    last_entry_id = EXCLUDED.last_entry_id,
    last_sequence = EXCLUDED.last_sequence;
"""

# ── optional deps ──────────────────────────────────────────────────────────────
try:
    from pymerkle import InmemoryTree
    _PYMERKLE_AVAILABLE = True
except ImportError:
    _PYMERKLE_AVAILABLE = False
    logger.warning("[MerkleBatch] pymerkle not installed — Merkle batching disabled")

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


def _redis_client():
    host = os.getenv("REDIS_HOST", "redis")
    password = os.getenv("REDIS_PASSWORD", "cemini_redis_2026")
    return _redis_lib.Redis(
        host=host, port=6379, password=password,
        decode_responses=True, socket_connect_timeout=2,
    )


def _read_chain_jsonl(batch_date: str) -> list[dict]:
    """Read all entries from the day's JSONL chain file."""
    jsonl_path = Path(_archive_root()) / "chains" / f"{batch_date}.jsonl"
    if not jsonl_path.exists():
        logger.info("[MerkleBatch] No chain file for %s", batch_date)
        return []
    entries = []
    with jsonl_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    logger.warning("[MerkleBatch] Skipping malformed JSONL line: %s", exc)
    return entries


def build_merkle_root(entries: list[dict]) -> Optional[str]:
    """Build a Merkle tree from entries and return the root hex string."""
    if not _PYMERKLE_AVAILABLE or not entries:
        return None
    tree = InmemoryTree(algorithm="sha256")
    for entry in entries:
        payload_hash = entry.get("payload_hash", "")
        tree.append_entry(payload_hash.encode("utf-8"))
    root_bytes = tree.get_state()
    return root_bytes.hex() if root_bytes else None


def run_batch(batch_date: Optional[str] = None) -> Optional[BatchCommitment]:
    """Build and persist the daily Merkle batch commitment.

    Parameters
    ----------
    batch_date : str, optional
        Date string YYYY-MM-DD. Defaults to today (UTC).

    Returns
    -------
    BatchCommitment on success, None on error.
    """
    if batch_date is None:
        batch_date = date.today().isoformat()

    logger.info("[MerkleBatch] Starting batch for %s", batch_date)

    try:
        entries = _read_chain_jsonl(batch_date)
        if not entries:
            logger.warning("[MerkleBatch] No entries for %s — skipping", batch_date)
            return None

        merkle_root = build_merkle_root(entries)
        if merkle_root is None:
            logger.warning("[MerkleBatch] Could not build Merkle root for %s", batch_date)
            return None

        commitment = BatchCommitment(
            commitment_id=_new_uuid7(),
            batch_date=batch_date,
            merkle_root=merkle_root,
            entry_count=len(entries),
            first_entry_id=entries[0].get("entry_id"),
            last_entry_id=entries[-1].get("entry_id"),
            first_sequence=entries[0].get("sequence_num"),
            last_sequence=entries[-1].get("sequence_num"),
        )

        batch_dir = Path(_archive_root()) / "batches" / batch_date
        batch_dir.mkdir(parents=True, exist_ok=True)
        batches_json_path = batch_dir / "batches.json"
        batches_json_path.write_text(
            json.dumps(commitment.model_dump(), sort_keys=True, indent=2),
            encoding="utf-8",
        )
        logger.info("[MerkleBatch] Wrote %s (root=%s…)", batches_json_path, merkle_root[:16])

        _pg_insert_commitment(commitment)
        _try_ots_stamp(batches_json_path, batch_date)
        _redis_publish(commitment)

        return commitment

    except Exception as exc:  # noqa: BLE001
        logger.error("[MerkleBatch] batch failed for %s: %s", batch_date, exc)
        return None


def _pg_insert_commitment(commitment: BatchCommitment) -> None:
    if not _PG_AVAILABLE:
        return
    try:
        conn = _pg_conn()
        cur = conn.cursor()
        created_ts = datetime.fromtimestamp(commitment.created_at, tz=timezone.utc)
        cur.execute(_INSERT_SQL, (
            commitment.commitment_id,
            commitment.batch_date,
            commitment.merkle_root,
            commitment.entry_count,
            commitment.first_entry_id,
            commitment.last_entry_id,
            commitment.first_sequence,
            commitment.last_sequence,
            created_ts,
        ))
        conn.commit()
        conn.close()
        logger.info("[MerkleBatch] Committed to DB: batch_date=%s", commitment.batch_date)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[MerkleBatch] DB insert failed: %s", exc)


def _try_ots_stamp(batches_json_path: Path, batch_date: str) -> None:
    """Best-effort OpenTimestamps stamp. Skips gracefully if ots binary unavailable."""
    ots_binary = shutil.which("ots")
    if not ots_binary:
        logger.info("[MerkleBatch] ots binary not found — Layer 3 anchoring skipped for %s", batch_date)
        return
    try:
        ots_dir = Path(_archive_root()) / "ots"
        ots_dir.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(  # noqa: S603
            [ots_binary, "stamp", str(batches_json_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            ots_proof = Path(str(batches_json_path) + ".ots")
            if ots_proof.exists():
                dest = ots_dir / f"{batch_date}-batches.json.ots"
                ots_proof.rename(dest)
            logger.info("[MerkleBatch] OTS stamp created for %s", batch_date)
        else:
            logger.warning("[MerkleBatch] ots stamp returned %d: %s", result.returncode, result.stderr[:200])
    except Exception as exc:  # noqa: BLE001
        logger.warning("[MerkleBatch] OTS stamp failed (non-blocking): %s", exc)


def _redis_publish(commitment: BatchCommitment) -> None:
    if not _REDIS_AVAILABLE:
        return
    try:
        rc = _redis_client()
        payload = {
            "value": {
                "batch_date": commitment.batch_date,
                "merkle_root": commitment.merkle_root,
                "entry_count": commitment.entry_count,
            },
            "source_system": "audit_trail",
            "timestamp": time.time(),
            "confidence": 1.0,
        }
        rc.set(INTEL_KEY, json.dumps(payload), ex=INTEL_TTL)
    except Exception as exc:  # noqa: BLE001
        logger.debug("[MerkleBatch] Redis publish failed: %s", exc)


async def daily_merkle_batch_job() -> None:
    """APScheduler cron job — runs at 23:55 UTC daily."""
    batch_date = date.today().isoformat()
    logger.info("[MerkleBatch] APScheduler job triggered for %s", batch_date)
    run_batch(batch_date)
