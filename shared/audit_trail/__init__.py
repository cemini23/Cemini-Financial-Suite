"""Cemini Financial Suite — Cryptographic Audit Trail (Step 43).

Three-layer tamper-evident audit trail:
  Layer 1: SHA-256 hash chain (PL/pgSQL + JSONL)
  Layer 2: pymerkle daily Merkle tree batch commitments
  Layer 3: OpenTimestamps Bitcoin anchoring (best-effort)

VCP Silver Tier naming conventions used throughout.
"""

from shared.audit_trail.hasher import canonicalize, sha256_hex, chain_hash  # noqa: F401
from shared.audit_trail.models import ChainEntry, BatchCommitment, IntentRecord, VerificationResult  # noqa: F401
