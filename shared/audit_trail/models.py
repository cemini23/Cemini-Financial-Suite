"""Cemini Financial Suite — Audit Trail Pydantic Models (Step 43).

VCP Silver Tier field naming conventions:
  ChainEntry        — one row in audit_hash_chain
  BatchCommitment   — one row in audit_batch_commitments (daily Merkle root)
  IntentRecord      — one row in audit_intent_log (pre-evaluation intent)
  VerificationResult — output of offline verification script
"""

import time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ChainEntry(BaseModel):
    """One entry in the SHA-256 hash chain. VCP Silver Tier schema."""

    model_config = ConfigDict(extra="forbid")

    # VCP Silver Tier identifiers
    entry_id: str                       # UUIDv7 string (time-sortable)
    sequence_num: int                   # BIGSERIAL — gap-detectable
    source_table: str                   # trade_history | ai_trade_logs | playbook_logs
    source_id: str                      # PK or identifier from source table

    # Payload fingerprints
    payload_canonical: str              # JSON with sort_keys=True, no spaces
    payload_hash: str                   # SHA-256 of payload_canonical
    prev_hash: str                      # chain_hash of previous entry ('0'*64 for genesis)
    chain_hash: str                     # SHA-256(prev_hash + payload_hash)

    created_at: float = Field(default_factory=time.time)


class BatchCommitment(BaseModel):
    """Daily Merkle tree batch commitment. VCP Silver Tier schema."""

    model_config = ConfigDict(extra="forbid")

    # VCP Silver Tier identifiers
    commitment_id: str                  # UUIDv7 string
    batch_date: str                     # YYYY-MM-DD

    # Merkle proof
    merkle_root: str                    # hex root of the day's Merkle tree
    entry_count: int

    # Range anchors (UUIDv7 are time-sortable)
    first_entry_id: Optional[str] = None
    last_entry_id: Optional[str] = None
    first_sequence: Optional[int] = None
    last_sequence: Optional[int] = None

    created_at: float = Field(default_factory=time.time)


class IntentRecord(BaseModel):
    """Pre-evaluation intent log entry. Proves no cherry-picking. VCP Silver Tier schema."""

    model_config = ConfigDict(extra="forbid")

    intent_id: str                      # UUIDv7
    signal_source: str                  # e.g. 'playbook', 'screener'
    signal_type: str                    # e.g. 'EpisodicPivot', 'MomentumBurst'
    ticker: Optional[str] = None

    intent_hash: str                    # SHA-256 of canonicalized intent payload
    created_at: float = Field(default_factory=time.time)


class VerificationResult(BaseModel):
    """Output of the offline verification pass. VCP Silver Tier schema."""

    model_config = ConfigDict(extra="allow")

    # Overall verdict
    chain_valid: bool
    entry_count: int

    # Hash chain integrity
    broken_at_sequence: Optional[int] = None

    # Sequence gap detection
    gap_detected: bool = False
    gap_at_sequence: Optional[int] = None

    # Merkle verification
    merkle_roots_match: bool = True
    batches_verified: int = 0

    # Any anomalies
    anomalies: list[str] = Field(default_factory=list)
