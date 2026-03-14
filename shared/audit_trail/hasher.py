"""Cemini Financial Suite — Cryptographic Hasher (Step 43).

Canonical JSON serialization + SHA-256 hash chain primitives.
VCP Silver Tier canonicalization spec: sort_keys=True, separators=(',',':').
"""

import hashlib
import json


def canonicalize(payload: dict) -> str:
    """Return a canonical JSON string for deterministic hashing.

    Rules (VCP Silver Tier):
    - Keys sorted alphabetically (sort_keys=True)
    - No whitespace (compact separators)
    - UTF-8 safe
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def sha256_hex(data: str) -> str:
    """Return the SHA-256 hex digest of a UTF-8 string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def chain_hash(prev_hash: str, payload_hash: str) -> str:
    """Compute the chain hash: SHA-256(prev_hash || payload_hash).

    Modifying any historical entry invalidates all subsequent chain hashes.
    Genesis entry uses prev_hash = '0' * 64.
    """
    return sha256_hex(prev_hash + payload_hash)


GENESIS_HASH = "0" * 64
