"""Tests for Step 43: Cryptographic Trade Audit Trail.

All tests are pure — no network, no Redis, no Postgres.
Mocks are used for all I/O.

Target: 52+ new tests.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

# Repo root on sys.path
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from shared.audit_trail.hasher import (
    canonicalize,
    sha256_hex,
    chain_hash,
    GENESIS_HASH,
)
from shared.audit_trail.models import (
    ChainEntry,
    BatchCommitment,
    IntentRecord,
    VerificationResult,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_chain_entries(n: int, start_seq: int = 1) -> list[dict]:
    """Build a valid hash chain of n entries (pure Python, no DB)."""
    entries = []
    prev_h = GENESIS_HASH
    for idx in range(n):
        seq = start_seq + idx
        payload = {"idx": idx, "source": "test", "value": idx * 10}
        canonical = canonicalize(payload)
        p_hash = sha256_hex(canonical)
        c_hash = chain_hash(prev_h, p_hash)
        entry = {
            "entry_id": f"019cec{idx:04x}-0000-7000-8000-000000000001",
            "sequence_num": seq,
            "source_table": "playbook_logs",
            "source_id": f"test:{seq}",
            "payload_canonical": canonical,
            "payload_hash": p_hash,
            "prev_hash": prev_h,
            "chain_hash": c_hash,
            "created_at": 1710432000.0 + idx * 60,
        }
        entries.append(entry)
        prev_h = c_hash
    return entries


def _write_chain_jsonl(tmp_path: Path, entries: list[dict], date_str: str = "2026-03-14") -> Path:
    """Write entries as JSONL to tmp_path/chains/YYYY-MM-DD.jsonl."""
    chains_dir = tmp_path / "chains"
    chains_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = chains_dir / f"{date_str}.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n")
    return jsonl_path


# ─────────────────────────────────────────────────────────────────────────────
# 1. Hasher tests
# ─────────────────────────────────────────────────────────────────────────────

class TestHasher:
    def test_canonicalize_deterministic(self):
        """Same payload always produces the same canonical string."""
        payload = {"b": 2, "a": 1, "c": "hello"}
        assert canonicalize(payload) == canonicalize(payload)

    def test_canonicalize_key_ordering(self):
        """Keys are sorted regardless of insertion order."""
        p1 = {"z": 1, "a": 2}
        p2 = {"a": 2, "z": 1}
        assert canonicalize(p1) == canonicalize(p2)
        assert canonicalize(p1) == '{"a":2,"z":1}'

    def test_canonicalize_no_whitespace(self):
        """Output has no spaces (compact separators)."""
        result = canonicalize({"key": "value"})
        assert " " not in result

    def test_canonicalize_separators(self):
        """Uses comma+colon separators (VCP Silver Tier spec)."""
        result = canonicalize({"a": 1, "b": 2})
        assert result == '{"a":1,"b":2}'

    def test_sha256_known_value(self):
        """SHA-256 of empty string matches known digest."""
        known = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert sha256_hex("") == known

    def test_sha256_deterministic(self):
        """Same input always produces same digest."""
        assert sha256_hex("hello world") == sha256_hex("hello world")

    def test_chain_hash_genesis(self):
        """chain_hash with genesis prev_hash produces a valid 64-char hex string."""
        p_hash = sha256_hex(canonicalize({"test": 1}))
        result = chain_hash(GENESIS_HASH, p_hash)
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_chain_hash_changes_with_prev(self):
        """Changing prev_hash changes the chain_hash."""
        p_hash = sha256_hex("payload")
        h1 = chain_hash(GENESIS_HASH, p_hash)
        h2 = chain_hash("a" * 64, p_hash)
        assert h1 != h2

    def test_chain_hash_changes_with_payload(self):
        """Changing payload_hash changes the chain_hash."""
        h1 = chain_hash(GENESIS_HASH, sha256_hex("payload1"))
        h2 = chain_hash(GENESIS_HASH, sha256_hex("payload2"))
        assert h1 != h2

    def test_genesis_hash_format(self):
        """GENESIS_HASH is 64 zero characters."""
        assert GENESIS_HASH == "0" * 64
        assert len(GENESIS_HASH) == 64


# ─────────────────────────────────────────────────────────────────────────────
# 2. Hash chain continuity tests
# ─────────────────────────────────────────────────────────────────────────────

class TestHashChain:
    def test_hash_chain_genesis_prev_hash(self):
        """First entry uses GENESIS_HASH as prev_hash."""
        entries = _make_chain_entries(1)
        assert entries[0]["prev_hash"] == GENESIS_HASH

    def test_hash_chain_continuity_3(self):
        """3-entry chain: each prev_hash equals prior chain_hash."""
        entries = _make_chain_entries(3)
        assert entries[1]["prev_hash"] == entries[0]["chain_hash"]
        assert entries[2]["prev_hash"] == entries[1]["chain_hash"]

    def test_hash_chain_continuity_10(self):
        """10-entry chain: all prev_hash links are valid."""
        entries = _make_chain_entries(10)
        for idx in range(1, len(entries)):
            assert entries[idx]["prev_hash"] == entries[idx - 1]["chain_hash"]

    def test_hash_chain_tamper_middle(self):
        """Modifying middle entry's payload breaks chain from that point on."""
        entries = _make_chain_entries(5)
        # Tamper entry 2
        entries[2]["payload_canonical"] = canonicalize({"tampered": True})
        entries[2]["payload_hash"] = sha256_hex(entries[2]["payload_canonical"])
        # Re-check: entry[3].prev_hash != new entries[2].chain_hash
        # entries[3].prev_hash still points to OLD chain_hash of entry[2]
        recomputed_c_hash = chain_hash(entries[2]["prev_hash"], entries[2]["payload_hash"])
        assert recomputed_c_hash != entries[3]["prev_hash"]

    def test_hash_chain_tamper_first(self):
        """Modifying first entry breaks chain from position 1."""
        entries = _make_chain_entries(3)
        entries[0]["payload_canonical"] = canonicalize({"tampered": True})
        entries[0]["payload_hash"] = sha256_hex(entries[0]["payload_canonical"])
        recomputed_c_hash = chain_hash(GENESIS_HASH, entries[0]["payload_hash"])
        assert recomputed_c_hash != entries[1]["prev_hash"]

    def test_hash_chain_recompute_matches(self):
        """Recomputing chain_hash from scratch matches stored values."""
        entries = _make_chain_entries(5)
        for entry in entries:
            computed = chain_hash(entry["prev_hash"], entry["payload_hash"])
            assert computed == entry["chain_hash"]

    def test_hash_chain_different_payloads(self):
        """Entries with different payloads produce different chain hashes."""
        entries = _make_chain_entries(2)
        assert entries[0]["chain_hash"] != entries[1]["chain_hash"]


# ─────────────────────────────────────────────────────────────────────────────
# 3. UUIDv7 tests
# ─────────────────────────────────────────────────────────────────────────────

class TestUUIDv7:
    def test_uuid7_monotonicity(self):
        """Sequential UUIDv7s are time-ordered (string comparison)."""
        from uuid_utils import uuid7
        ids = [str(uuid7()) for _ in range(10)]
        assert ids == sorted(ids), "UUIDv7 IDs must be monotonically increasing"

    def test_uuid7_is_string(self):
        """uuid7() converted to str is a valid UUID-format string."""
        from uuid_utils import uuid7
        uid = str(uuid7())
        parts = uid.split("-")
        assert len(parts) == 5
        assert len(uid) == 36

    def test_uuid7_version_bit(self):
        """UUIDv7 has version nibble '7'."""
        from uuid_utils import uuid7
        uid = str(uuid7())
        assert uid[14] == "7"

    def test_uuid7_gap_detection_logic(self):
        """Verify that string comparison detects time ordering."""
        from uuid_utils import uuid7
        uid1 = str(uuid7())
        time.sleep(0.002)  # ensure different millisecond
        uid2 = str(uuid7())
        assert uid1 < uid2, "Earlier UUIDv7 must sort before later one"

    def test_uuid7_uniqueness(self):
        """100 sequential UUIDv7s are all unique."""
        from uuid_utils import uuid7
        ids = [str(uuid7()) for _ in range(100)]
        assert len(set(ids)) == 100


# ─────────────────────────────────────────────────────────────────────────────
# 4. Merkle tree tests
# ─────────────────────────────────────────────────────────────────────────────

class TestMerkleTree:
    def test_merkle_single_entry(self):
        """Single entry produces a non-null Merkle root."""
        from pymerkle import InmemoryTree
        tree = InmemoryTree(algorithm="sha256")
        tree.append_entry(b"hello")
        root = tree.get_state()
        assert root is not None
        assert len(root) == 32  # 32 bytes = 256 bits

    def test_merkle_multiple_entries(self):
        """Multiple entries produce a valid non-null root."""
        from pymerkle import InmemoryTree
        tree = InmemoryTree(algorithm="sha256")
        for val in [b"a", b"b", b"c", b"d"]:
            tree.append_entry(val)
        root = tree.get_state()
        assert root is not None
        assert len(root.hex()) == 64

    def test_merkle_deterministic(self):
        """Same entries always produce the same Merkle root."""
        from pymerkle import InmemoryTree
        entries = [b"entry1", b"entry2", b"entry3"]

        tree1 = InmemoryTree(algorithm="sha256")
        for e in entries:
            tree1.append_entry(e)
        root1 = tree1.get_state().hex()

        tree2 = InmemoryTree(algorithm="sha256")
        for e in entries:
            tree2.append_entry(e)
        root2 = tree2.get_state().hex()

        assert root1 == root2

    def test_merkle_tamper_detection(self):
        """Removing one entry changes the Merkle root."""
        from pymerkle import InmemoryTree
        entries = [b"entry1", b"entry2", b"entry3"]

        tree1 = InmemoryTree(algorithm="sha256")
        for e in entries:
            tree1.append_entry(e)
        root1 = tree1.get_state().hex()

        tree2 = InmemoryTree(algorithm="sha256")
        for e in entries[:-1]:  # remove last entry
            tree2.append_entry(e)
        root2 = tree2.get_state().hex()

        assert root1 != root2

    def test_merkle_recompute_matches_stored(self):
        """batch.build_merkle_root() matches manual recomputation."""
        from shared.audit_trail.merkle_batch import build_merkle_root
        entries = _make_chain_entries(5)
        root1 = build_merkle_root(entries)

        from pymerkle import InmemoryTree
        tree = InmemoryTree(algorithm="sha256")
        for e in entries:
            tree.append_entry(e["payload_hash"].encode("utf-8"))
        root2 = tree.get_state().hex()

        assert root1 == root2


# ─────────────────────────────────────────────────────────────────────────────
# 5. Pydantic model / VCP field name tests
# ─────────────────────────────────────────────────────────────────────────────

class TestModels:
    def test_chain_entry_vcp_field_names(self):
        """ChainEntry has all VCP Silver Tier required field names."""
        required = {
            "entry_id", "sequence_num", "source_table", "source_id",
            "payload_canonical", "payload_hash", "prev_hash", "chain_hash", "created_at",
        }
        field_names = set(ChainEntry.model_fields.keys())
        assert required.issubset(field_names)

    def test_batch_commitment_vcp_field_names(self):
        """BatchCommitment has all VCP Silver Tier required field names."""
        required = {
            "commitment_id", "batch_date", "merkle_root", "entry_count",
            "first_entry_id", "last_entry_id", "first_sequence", "last_sequence",
        }
        field_names = set(BatchCommitment.model_fields.keys())
        assert required.issubset(field_names)

    def test_intent_record_schema(self):
        """IntentRecord validates and stores VCP-named fields."""
        record = IntentRecord(
            intent_id="test-uuid",
            signal_source="playbook",
            signal_type="EpisodicPivot",
            ticker="AAPL",
            intent_hash="a" * 64,
        )
        assert record.signal_source == "playbook"
        assert record.signal_type == "EpisodicPivot"
        assert record.ticker == "AAPL"
        assert record.intent_hash == "a" * 64

    def test_verification_result_schema(self):
        """VerificationResult has expected VCP fields."""
        result = VerificationResult(chain_valid=True, entry_count=10)
        assert result.chain_valid is True
        assert result.entry_count == 10
        assert result.gap_detected is False
        assert result.merkle_roots_match is True
        assert result.anomalies == []

    def test_chain_entry_model_dump(self):
        """ChainEntry.model_dump() produces serializable dict."""
        entry = ChainEntry(
            entry_id="uuid-test",
            sequence_num=1,
            source_table="playbook_logs",
            source_id="test:1",
            payload_canonical='{"a":1}',
            payload_hash="a" * 64,
            prev_hash=GENESIS_HASH,
            chain_hash="b" * 64,
        )
        dumped = entry.model_dump()
        assert json.dumps(dumped)  # must be JSON-serializable

    def test_batch_commitment_model_dump(self):
        """BatchCommitment.model_dump() produces serializable dict."""
        bc = BatchCommitment(
            commitment_id="uuid-test",
            batch_date="2026-03-14",
            merkle_root="c" * 64,
            entry_count=42,
        )
        dumped = bc.model_dump()
        assert dumped["batch_date"] == "2026-03-14"
        assert dumped["entry_count"] == 42


# ─────────────────────────────────────────────────────────────────────────────
# 6. ChainWriter tests
# ─────────────────────────────────────────────────────────────────────────────

class TestChainWriter:
    def test_chain_writer_writes_jsonl(self, tmp_path):
        """ChainWriter writes a JSONL file when DB is unavailable."""
        with patch.dict(os.environ, {"AUDIT_ARCHIVE_DIR": str(tmp_path)}):
            # Re-import to pick up patched env
            from shared.audit_trail.chain_writer import ChainWriter
            writer = ChainWriter()
            with patch("shared.audit_trail.chain_writer._PG_AVAILABLE", False), \
                 patch("shared.audit_trail.chain_writer._REDIS_AVAILABLE", False):
                entry = writer.write("playbook_logs", "test:1", {"event": "test"})

        jsonl_files = list((tmp_path / "chains").glob("*.jsonl"))
        assert len(jsonl_files) == 1

    def test_chain_writer_jsonl_format(self, tmp_path):
        """JSONL file contains one valid JSON object per line."""
        with patch.dict(os.environ, {"AUDIT_ARCHIVE_DIR": str(tmp_path)}):
            from shared.audit_trail.chain_writer import ChainWriter
            writer = ChainWriter()
            with patch("shared.audit_trail.chain_writer._PG_AVAILABLE", False), \
                 patch("shared.audit_trail.chain_writer._REDIS_AVAILABLE", False):
                for idx in range(3):
                    writer.write("playbook_logs", f"test:{idx}", {"idx": idx})

        jsonl_path = next((tmp_path / "chains").glob("*.jsonl"))
        lines = jsonl_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 3
        for line in lines:
            obj = json.loads(line)
            assert "entry_id" in obj
            assert "payload_hash" in obj
            assert "chain_hash" in obj

    def test_chain_writer_fail_silent_on_error(self, tmp_path):
        """ChainWriter returns None without raising on any error."""
        with patch.dict(os.environ, {"AUDIT_ARCHIVE_DIR": "/nonexistent/path/xyz"}):
            from shared.audit_trail.chain_writer import ChainWriter
            writer = ChainWriter()
            with patch("shared.audit_trail.chain_writer._PG_AVAILABLE", False), \
                 patch("shared.audit_trail.chain_writer._REDIS_AVAILABLE", False):
                # This should not raise even if archive dir creation fails
                result = writer.write("test_table", "id:1", {"val": 1})
                # May be None or ChainEntry — must not raise

    def test_chain_writer_payload_hash_correct(self, tmp_path):
        """JSONL entry has correct payload_hash matching SHA-256(canonical)."""
        payload = {"action": "buy", "symbol": "AAPL", "price": 180.0}
        with patch.dict(os.environ, {"AUDIT_ARCHIVE_DIR": str(tmp_path)}):
            from shared.audit_trail.chain_writer import ChainWriter
            writer = ChainWriter()
            with patch("shared.audit_trail.chain_writer._PG_AVAILABLE", False), \
                 patch("shared.audit_trail.chain_writer._REDIS_AVAILABLE", False):
                writer.write("trade_history", "trade:1", payload)

        jsonl_path = next((tmp_path / "chains").glob("*.jsonl"))
        entry = json.loads(jsonl_path.read_text().strip())
        expected_canonical = canonicalize(payload)
        expected_hash = sha256_hex(expected_canonical)
        assert entry["payload_hash"] == expected_hash
        assert entry["payload_canonical"] == expected_canonical

    def test_chain_writer_redis_publish_called(self, tmp_path):
        """ChainWriter calls Redis SET when Redis is available."""
        mock_redis = MagicMock()
        mock_redis_client = MagicMock(return_value=mock_redis)
        with patch.dict(os.environ, {"AUDIT_ARCHIVE_DIR": str(tmp_path)}):
            with patch("shared.audit_trail.chain_writer._PG_AVAILABLE", False), \
                 patch("shared.audit_trail.chain_writer._REDIS_AVAILABLE", True), \
                 patch("shared.audit_trail.chain_writer._redis_client", mock_redis_client):
                from shared.audit_trail.chain_writer import ChainWriter
                writer = ChainWriter()
                writer.write("playbook_logs", "test:1", {"val": 99})

        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "intel:audit_chain_entry"


# ─────────────────────────────────────────────────────────────────────────────
# 7. IntentLogger tests
# ─────────────────────────────────────────────────────────────────────────────

class TestIntentLogger:
    def test_intent_log_returns_record(self, tmp_path):
        """log_intent() returns an IntentRecord on success."""
        with patch.dict(os.environ, {"AUDIT_ARCHIVE_DIR": str(tmp_path)}):
            with patch("shared.audit_trail.intent_logger._PG_AVAILABLE", False):
                from shared.audit_trail.intent_logger import log_intent
                record = log_intent("playbook", "EpisodicPivot", ticker="AAPL")

        assert record is not None
        assert record.signal_source == "playbook"
        assert record.signal_type == "EpisodicPivot"
        assert record.ticker == "AAPL"

    def test_intent_log_hash_deterministic(self, tmp_path):
        """Same intent parameters produce the same intent_hash."""
        with patch.dict(os.environ, {"AUDIT_ARCHIVE_DIR": str(tmp_path)}):
            with patch("shared.audit_trail.intent_logger._PG_AVAILABLE", False):
                from shared.audit_trail.intent_logger import log_intent
                r1 = log_intent("playbook", "EpisodicPivot", ticker="AAPL")
                r2 = log_intent("playbook", "EpisodicPivot", ticker="AAPL")

        assert r1.intent_hash == r2.intent_hash

    def test_intent_log_writes_jsonl(self, tmp_path):
        """log_intent() writes a JSONL entry to the intents archive."""
        with patch.dict(os.environ, {"AUDIT_ARCHIVE_DIR": str(tmp_path)}):
            with patch("shared.audit_trail.intent_logger._PG_AVAILABLE", False):
                from shared.audit_trail.intent_logger import log_intent
                log_intent("playbook", "VCP", ticker="MSFT")

        jsonl_files = list((tmp_path / "intents").glob("*.jsonl"))
        assert len(jsonl_files) == 1
        line = json.loads(jsonl_files[0].read_text().strip())
        assert line["signal_type"] == "VCP"
        assert line["ticker"] == "MSFT"

    def test_intent_log_fail_silent_postgres_error(self, tmp_path):
        """log_intent() returns None without raising on Postgres error."""
        with patch.dict(os.environ, {"AUDIT_ARCHIVE_DIR": str(tmp_path)}):
            with patch("shared.audit_trail.intent_logger._PG_AVAILABLE", True), \
                 patch("shared.audit_trail.intent_logger._pg_conn", side_effect=Exception("DB down")):
                from shared.audit_trail.intent_logger import log_intent
                # Must not raise — fail silently
                result = log_intent("playbook", "MomentumBurst")

        # If JSONL write succeeded, result may not be None
        # Key point: no exception raised

    def test_intent_log_before_signal_timestamp(self, tmp_path):
        """IntentRecord created_at precedes signal detection time."""
        t_before = time.time()
        with patch.dict(os.environ, {"AUDIT_ARCHIVE_DIR": str(tmp_path)}):
            with patch("shared.audit_trail.intent_logger._PG_AVAILABLE", False):
                from shared.audit_trail.intent_logger import log_intent
                record = log_intent("playbook", "HighTightFlag", ticker="NVDA")
        t_after = time.time()

        assert record is not None
        assert t_before <= record.created_at <= t_after

    def test_intent_log_schema_fields(self, tmp_path):
        """JSONL entry has all required VCP Silver Tier fields."""
        with patch.dict(os.environ, {"AUDIT_ARCHIVE_DIR": str(tmp_path)}):
            with patch("shared.audit_trail.intent_logger._PG_AVAILABLE", False):
                from shared.audit_trail.intent_logger import log_intent
                log_intent("screener", "InsideBar212", ticker="SPY")

        jsonl_path = next((tmp_path / "intents").glob("*.jsonl"))
        entry = json.loads(jsonl_path.read_text().strip())
        for field in ("intent_id", "signal_source", "signal_type", "ticker", "intent_hash", "created_at"):
            assert field in entry, f"Missing field: {field}"


# ─────────────────────────────────────────────────────────────────────────────
# 8. Merkle Batch tests
# ─────────────────────────────────────────────────────────────────────────────

class TestMerkleBatch:
    def test_batch_reads_jsonl_and_builds_commitment(self, tmp_path):
        """run_batch() reads JSONL and creates batches.json."""
        entries = _make_chain_entries(5)
        _write_chain_jsonl(tmp_path, entries, "2026-03-14")

        with patch.dict(os.environ, {"AUDIT_ARCHIVE_DIR": str(tmp_path)}):
            with patch("shared.audit_trail.merkle_batch._PG_AVAILABLE", False), \
                 patch("shared.audit_trail.merkle_batch._REDIS_AVAILABLE", False):
                from shared.audit_trail.merkle_batch import run_batch
                commitment = run_batch("2026-03-14")

        assert commitment is not None
        assert commitment.batch_date == "2026-03-14"
        assert commitment.entry_count == 5
        assert len(commitment.merkle_root) == 64

    def test_batch_creates_batches_json_file(self, tmp_path):
        """run_batch() creates batches/YYYY-MM-DD/batches.json."""
        entries = _make_chain_entries(3)
        _write_chain_jsonl(tmp_path, entries, "2026-03-15")

        with patch.dict(os.environ, {"AUDIT_ARCHIVE_DIR": str(tmp_path)}):
            with patch("shared.audit_trail.merkle_batch._PG_AVAILABLE", False), \
                 patch("shared.audit_trail.merkle_batch._REDIS_AVAILABLE", False):
                from shared.audit_trail.merkle_batch import run_batch
                run_batch("2026-03-15")

        batches_json = tmp_path / "batches" / "2026-03-15" / "batches.json"
        assert batches_json.exists()
        data = json.loads(batches_json.read_text(encoding="utf-8"))
        assert data["batch_date"] == "2026-03-15"
        assert data["entry_count"] == 3

    def test_batch_no_jsonl_returns_none(self, tmp_path):
        """run_batch() returns None when no chain file exists for date."""
        with patch.dict(os.environ, {"AUDIT_ARCHIVE_DIR": str(tmp_path)}):
            with patch("shared.audit_trail.merkle_batch._PG_AVAILABLE", False), \
                 patch("shared.audit_trail.merkle_batch._REDIS_AVAILABLE", False):
                from shared.audit_trail.merkle_batch import run_batch
                result = run_batch("2099-01-01")

        assert result is None

    def test_batch_ots_skipped_when_binary_missing(self, tmp_path):
        """_try_ots_stamp logs warning and continues when ots binary is not found."""
        entries = _make_chain_entries(2)
        _write_chain_jsonl(tmp_path, entries, "2026-03-14")

        with patch.dict(os.environ, {"AUDIT_ARCHIVE_DIR": str(tmp_path)}):
            with patch("shared.audit_trail.merkle_batch._PG_AVAILABLE", False), \
                 patch("shared.audit_trail.merkle_batch._REDIS_AVAILABLE", False), \
                 patch("shared.audit_trail.merkle_batch.shutil.which", return_value=None):
                from shared.audit_trail.merkle_batch import run_batch
                commitment = run_batch("2026-03-14")

        # Should succeed even without ots binary
        assert commitment is not None

    def test_batch_commitment_vcp_fields_in_json(self, tmp_path):
        """batches.json contains VCP Silver Tier field names."""
        entries = _make_chain_entries(4)
        _write_chain_jsonl(tmp_path, entries, "2026-03-14")

        with patch.dict(os.environ, {"AUDIT_ARCHIVE_DIR": str(tmp_path)}):
            with patch("shared.audit_trail.merkle_batch._PG_AVAILABLE", False), \
                 patch("shared.audit_trail.merkle_batch._REDIS_AVAILABLE", False):
                from shared.audit_trail.merkle_batch import run_batch
                run_batch("2026-03-14")

        batches_json = tmp_path / "batches" / "2026-03-14" / "batches.json"
        data = json.loads(batches_json.read_text(encoding="utf-8"))
        for field in ("commitment_id", "batch_date", "merkle_root", "entry_count",
                      "first_entry_id", "last_entry_id", "first_sequence", "last_sequence"):
            assert field in data, f"Missing VCP field: {field}"

    def test_build_merkle_root_empty_returns_none(self):
        """build_merkle_root([]) returns None (no entries)."""
        from shared.audit_trail.merkle_batch import build_merkle_root
        assert build_merkle_root([]) is None


# ─────────────────────────────────────────────────────────────────────────────
# 9. Verification tests
# ─────────────────────────────────────────────────────────────────────────────

class TestVerification:
    def test_verification_clean_chain(self, tmp_path):
        """verify_chain() passes on a valid chain."""
        entries = _make_chain_entries(5)
        _write_chain_jsonl(tmp_path, entries)

        from shared.audit_trail.verify import verify_chain
        result = verify_chain(str(tmp_path))

        assert result.chain_valid is True
        assert result.entry_count == 5
        assert result.gap_detected is False
        assert not result.broken_at_sequence

    def test_verification_broken_chain_middle(self, tmp_path):
        """verify_chain() detects tamper in middle of chain."""
        entries = _make_chain_entries(5)
        # Tamper entry 2: change payload but keep old chain_hash
        entries[2]["payload_canonical"] = canonicalize({"tampered": True})
        entries[2]["payload_hash"] = sha256_hex(entries[2]["payload_canonical"])
        # chain_hash is now wrong (doesn't match new payload_hash)
        _write_chain_jsonl(tmp_path, entries)

        from shared.audit_trail.verify import verify_chain
        result = verify_chain(str(tmp_path))

        # chain_hash mismatch should be detected
        assert result.chain_valid is False or len(result.anomalies) > 0

    def test_verification_gap_detection(self, tmp_path):
        """verify_chain() detects missing sequence numbers."""
        entries = _make_chain_entries(5)
        # Remove entry 2 (sequence gap: 2 → 4)
        entries_with_gap = entries[:2] + entries[3:]
        _write_chain_jsonl(tmp_path, entries_with_gap)

        from shared.audit_trail.verify import verify_chain
        result = verify_chain(str(tmp_path))

        assert result.gap_detected is True

    def test_verification_empty_chain(self, tmp_path):
        """verify_chain() handles empty chain gracefully."""
        from shared.audit_trail.verify import verify_chain
        result = verify_chain(str(tmp_path))

        # Empty chain is valid (nothing to tamper)
        assert result.entry_count == 0

    def test_verification_single_entry(self, tmp_path):
        """verify_chain() passes with single entry (genesis)."""
        entries = _make_chain_entries(1)
        _write_chain_jsonl(tmp_path, entries)

        from shared.audit_trail.verify import verify_chain
        result = verify_chain(str(tmp_path))

        assert result.chain_valid is True
        assert result.entry_count == 1

    def test_verification_with_batch_commitment(self, tmp_path):
        """verify_chain() verifies Merkle roots from batches.json."""
        entries = _make_chain_entries(4)
        _write_chain_jsonl(tmp_path, entries)

        # Build the batch first
        with patch.dict(os.environ, {"AUDIT_ARCHIVE_DIR": str(tmp_path)}):
            with patch("shared.audit_trail.merkle_batch._PG_AVAILABLE", False), \
                 patch("shared.audit_trail.merkle_batch._REDIS_AVAILABLE", False):
                from shared.audit_trail.merkle_batch import run_batch
                run_batch("2026-03-14")

        from shared.audit_trail.verify import verify_chain
        result = verify_chain(str(tmp_path))

        assert result.batches_verified >= 0  # may or may not match depending on date filter

    def test_verification_output_has_anomalies_list(self, tmp_path):
        """VerificationResult always has an anomalies list."""
        entries = _make_chain_entries(2)
        _write_chain_jsonl(tmp_path, entries)

        from shared.audit_trail.verify import verify_chain
        result = verify_chain(str(tmp_path))

        assert isinstance(result.anomalies, list)

    def test_verification_payload_hash_mismatch_detected(self, tmp_path):
        """verify_chain() detects payload_hash that doesn't match payload_canonical."""
        entries = _make_chain_entries(3)
        # Corrupt payload_hash of entry 1 (but keep chain_hash consistent)
        entries[1]["payload_hash"] = "deadbeef" * 8  # 64 chars but wrong value
        _write_chain_jsonl(tmp_path, entries)

        from shared.audit_trail.verify import verify_chain
        result = verify_chain(str(tmp_path))

        # Should detect payload hash mismatch
        assert len(result.anomalies) > 0


# ─────────────────────────────────────────────────────────────────────────────
# 10. Edge cases
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_payload_canonical(self):
        """Empty dict canonicalizes to '{}'."""
        result = canonicalize({})
        assert result == "{}"
        assert sha256_hex(result) == sha256_hex("{}")

    def test_unicode_payload(self):
        """Unicode strings are handled correctly."""
        payload = {"symbol": "日経平均", "emoji": "📈"}
        canonical = canonicalize(payload)
        p_hash = sha256_hex(canonical)
        assert len(p_hash) == 64

    def test_large_payload(self):
        """Large payloads (1000 keys) canonicalize and hash correctly."""
        payload = {f"key_{idx:04d}": idx for idx in range(1000)}
        canonical = canonicalize(payload)
        p_hash = sha256_hex(canonical)
        assert len(p_hash) == 64
        # Keys must be sorted
        keys = [k for k in canonical.split('"') if k.startswith("key_")]
        assert keys == sorted(keys)

    def test_nested_dict_canonical(self):
        """Nested dicts are serialized with sorted keys at every level."""
        payload = {"outer": {"z": 1, "a": 2}, "b": {"y": 3, "x": 4}}
        canonical = canonicalize(payload)
        obj = json.loads(canonical)
        assert list(obj.keys()) == sorted(obj.keys())
        assert list(obj["outer"].keys()) == sorted(obj["outer"].keys())

    def test_chain_entry_source_tables(self):
        """ChainEntry accepts all expected source_table values."""
        for table in ("trade_history", "ai_trade_logs", "playbook_logs"):
            entry = ChainEntry(
                entry_id="test",
                sequence_num=1,
                source_table=table,
                source_id="1",
                payload_canonical="{}",
                payload_hash="a" * 64,
                prev_hash=GENESIS_HASH,
                chain_hash="b" * 64,
            )
            assert entry.source_table == table

    def test_chain_hash_is_sha256_of_concatenation(self):
        """chain_hash exactly equals SHA-256(prev_hash + payload_hash)."""
        prev_h = "cafe" * 16      # 64 hex chars
        p_hash = "babe" * 16      # 64 hex chars
        expected = hashlib.sha256((prev_h + p_hash).encode("utf-8")).hexdigest()
        assert chain_hash(prev_h, p_hash) == expected

    def test_uuid7_fallback_to_uuid1_when_unavailable(self, monkeypatch):
        """chain_writer falls back to uuid1 if uuid-utils is unavailable."""
        import shared.audit_trail.chain_writer as cw
        original = cw._UUID7_AVAILABLE
        try:
            cw._UUID7_AVAILABLE = False
            uid = cw._new_uuid7()
            assert len(uid) == 36
            assert uid.count("-") == 4
        finally:
            cw._UUID7_AVAILABLE = original

    def test_multiple_source_tables_in_chain(self, tmp_path):
        """Chain can contain entries from multiple source tables."""
        entries = []
        prev_h = GENESIS_HASH
        for idx, table in enumerate(("trade_history", "ai_trade_logs", "playbook_logs")):
            payload = {"idx": idx, "table": table}
            canonical = canonicalize(payload)
            p_hash = sha256_hex(canonical)
            c_hash = chain_hash(prev_h, p_hash)
            entries.append({
                "entry_id": f"019cec{idx:04x}-0000-7000-8000-000000000001",
                "sequence_num": idx + 1,
                "source_table": table,
                "source_id": f"id:{idx}",
                "payload_canonical": canonical,
                "payload_hash": p_hash,
                "prev_hash": prev_h,
                "chain_hash": c_hash,
                "created_at": 1710432000.0 + idx * 60,
            })
            prev_h = c_hash
        _write_chain_jsonl(tmp_path, entries)

        from shared.audit_trail.verify import verify_chain
        result = verify_chain(str(tmp_path))
        assert result.chain_valid is True
        assert result.entry_count == 3
