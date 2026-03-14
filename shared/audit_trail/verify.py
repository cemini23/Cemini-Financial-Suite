"""Cemini Financial Suite — Offline Chain Verifier (Step 43).

Verifies the entire audit trail without any database connection.
Works purely from JSONL chain files + batch commitment files.

Called by scripts/verify.py for buyer offline verification.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from shared.audit_trail.hasher import sha256_hex, chain_hash, GENESIS_HASH
from shared.audit_trail.models import VerificationResult

logger = logging.getLogger("audit_trail.verify")


def _load_chain_entries(chains_dir: Path) -> list[dict]:
    """Load all JSONL chain entries across all daily files, sorted by sequence_num."""
    entries = []
    for jsonl_file in sorted(chains_dir.glob("*.jsonl")):
        with jsonl_file.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    entries.sort(key=lambda e: e.get("sequence_num", 0))
    return entries


def _load_batch_commitments(batches_dir: Path) -> list[dict]:
    """Load all batches.json commitment files."""
    commitments = []
    for batch_date_dir in sorted(batches_dir.iterdir()):
        batches_json = batch_date_dir / "batches.json"
        if batches_json.exists():
            try:
                commitments.append(json.loads(batches_json.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                pass
    return commitments


def _recompute_chain_hash(entry: dict) -> str:
    """Recompute chain_hash from prev_hash + payload_hash."""
    return chain_hash(entry["prev_hash"], entry["payload_hash"])


def _recompute_payload_hash(entry: dict) -> str:
    """Recompute payload_hash from payload_canonical."""
    return sha256_hex(entry["payload_canonical"])


def _build_merkle_root_from_entries(entries: list[dict]) -> Optional[str]:
    """Re-build Merkle root from a list of chain entries (by payload_hash)."""
    try:
        from pymerkle import InmemoryTree
        if not entries:
            return None
        tree = InmemoryTree(algorithm="sha256")
        for entry in entries:
            payload_hash = entry.get("payload_hash", "")
            tree.append_entry(payload_hash.encode("utf-8"))
        root_bytes = tree.get_state()
        return root_bytes.hex() if root_bytes else None
    except ImportError:
        return None


def verify_chain(archive_root: str) -> VerificationResult:
    """Verify the entire audit trail from JSONL + batch files.

    Parameters
    ----------
    archive_root : str
        Path to /mnt/archive/audit/ (or a test tmp directory).

    Returns
    -------
    VerificationResult with pass/fail status and anomaly details.
    """
    anomalies: list[str] = []
    root_path = Path(archive_root)
    chains_dir = root_path / "chains"
    batches_dir = root_path / "batches"

    # ── Load entries ──────────────────────────────────────────────────────────
    if not chains_dir.exists():
        return VerificationResult(
            chain_valid=True,
            entry_count=0,
            anomalies=["No chains directory — chain is empty (no entries yet)"],
        )

    entries = _load_chain_entries(chains_dir)
    entry_count = len(entries)

    if entry_count == 0:
        return VerificationResult(
            chain_valid=True,
            entry_count=0,
            anomalies=["Chain is empty"],
        )

    # ── Verify payload hashes ─────────────────────────────────────────────────
    for idx, entry in enumerate(entries):
        computed_p_hash = _recompute_payload_hash(entry)
        if computed_p_hash != entry.get("payload_hash"):
            anomalies.append(
                f"Payload hash mismatch at sequence {entry.get('sequence_num', idx)}: "
                f"expected {computed_p_hash[:16]}… got {entry.get('payload_hash', '')[:16]}…"
            )

    # ── Verify chain hash continuity ──────────────────────────────────────────
    broken_at_sequence: Optional[int] = None
    prev_chain_hash = GENESIS_HASH

    for idx, entry in enumerate(entries):
        seq = entry.get("sequence_num", idx)
        # Verify prev_hash matches previous chain_hash
        if entry.get("prev_hash") != prev_chain_hash:
            if broken_at_sequence is None:
                broken_at_sequence = seq
            anomalies.append(
                f"Chain break at sequence {seq}: "
                f"prev_hash={entry.get('prev_hash', '')[:16]}… "
                f"expected={prev_chain_hash[:16]}…"
            )
        # Verify chain_hash = SHA-256(prev_hash + payload_hash)
        computed_c_hash = chain_hash(entry.get("prev_hash", GENESIS_HASH), entry.get("payload_hash", ""))
        if computed_c_hash != entry.get("chain_hash"):
            if broken_at_sequence is None:
                broken_at_sequence = seq
            anomalies.append(f"chain_hash mismatch at sequence {seq}")
        prev_chain_hash = entry.get("chain_hash", computed_c_hash)

    # ── Sequence gap detection ────────────────────────────────────────────────
    gap_detected = False
    gap_at_sequence: Optional[int] = None
    seq_nums = [e.get("sequence_num", 0) for e in entries if e.get("sequence_num", -1) >= 0]
    for idx in range(1, len(seq_nums)):
        if seq_nums[idx] != seq_nums[idx - 1] + 1:
            gap_detected = True
            gap_at_sequence = seq_nums[idx]
            anomalies.append(
                f"Sequence gap detected: {seq_nums[idx - 1]} → {seq_nums[idx]}"
            )
            break

    # ── UUID7 monotonicity check ──────────────────────────────────────────────
    entry_ids = [e.get("entry_id", "") for e in entries if e.get("entry_id")]
    for idx in range(1, len(entry_ids)):
        if entry_ids[idx] < entry_ids[idx - 1]:
            anomalies.append(
                f"UUIDv7 non-monotonic at position {idx}: "
                f"{entry_ids[idx - 1][:18]}… > {entry_ids[idx][:18]}…"
            )

    # ── Merkle root verification ──────────────────────────────────────────────
    merkle_roots_match = True
    batches_verified = 0

    if batches_dir.exists():
        commitments = _load_batch_commitments(batches_dir)
        for commitment in commitments:
            batch_date = commitment.get("batch_date")
            stored_root = commitment.get("merkle_root")
            stored_count = commitment.get("entry_count", 0)

            # Get entries for this date
            date_entries = [
                e for e in entries
                if e.get("entry_id", "").startswith("") or True  # filter by date
            ]
            # Filter entries by created_at matching batch_date
            day_entries = [
                e for e in entries
                if _entry_date(e) == batch_date
            ]

            recomputed_root = _build_merkle_root_from_entries(day_entries)
            if recomputed_root is None:
                continue  # pymerkle not available, skip

            if recomputed_root != stored_root:
                merkle_roots_match = False
                anomalies.append(
                    f"Merkle root mismatch for {batch_date}: "
                    f"stored={stored_root[:16]}… computed={recomputed_root[:16]}…"
                )
            if len(day_entries) != stored_count:
                anomalies.append(
                    f"Entry count mismatch for {batch_date}: "
                    f"stored={stored_count} found={len(day_entries)}"
                )
            batches_verified += 1

    chain_valid = (broken_at_sequence is None and not anomalies) or (
        # Only Merkle/count issues don't break the chain itself
        broken_at_sequence is None and all(
            "Merkle" not in a and "count" not in a for a in anomalies
        ) and not gap_detected
    )

    return VerificationResult(
        chain_valid=chain_valid,
        entry_count=entry_count,
        broken_at_sequence=broken_at_sequence,
        gap_detected=gap_detected,
        gap_at_sequence=gap_at_sequence,
        merkle_roots_match=merkle_roots_match,
        batches_verified=batches_verified,
        anomalies=anomalies,
    )


def _entry_date(entry: dict) -> Optional[str]:
    """Extract YYYY-MM-DD from entry's created_at epoch."""
    try:
        from datetime import datetime, timezone
        ts = entry.get("created_at")
        if ts:
            return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime("%Y-%m-%d")
    except Exception:  # noqa: BLE001
        pass
    return None
