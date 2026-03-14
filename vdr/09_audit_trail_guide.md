# Audit Trail Buyer Verification Guide

This guide explains how to independently verify the cryptographic audit trail
that ensures trade history has not been tampered with.

---

## What Is the Audit Trail?

Cemini implements a 3-layer cryptographic audit trail (Step 43) that makes it
provably difficult to alter trade history after the fact:

**Layer 1: SHA-256 Hash Chain**
Every trade entry is hashed with SHA-256, and each hash includes the previous
entry's hash (chain linkage). The chain is stored in:
- PostgreSQL table `audit_hash_chain`
- JSONL mirror: `/mnt/archive/audit/chains/YYYY-MM-DD.jsonl`

**Layer 2: Daily Merkle Tree**
At 23:55 UTC each day, all entries are assembled into a Merkle tree. The Merkle
root commits to the entire day's trade data in a single 32-byte value.
- Output: `/mnt/archive/audit/batches/YYYY-MM-DD/batches.json`

**Layer 3: Bitcoin OpenTimestamps**
The daily Merkle root is submitted to the Bitcoin blockchain via OpenTimestamps,
creating a publicly verifiable third-party timestamp. This proves the data existed
before the block was mined.
- OTS file: `/mnt/archive/audit/batches/YYYY-MM-DD/batches.json.ots`

---

## Step-by-Step Verification

### Prerequisites

```bash
# Clone the repository
git clone https://github.com/cemini23/Cemini-Financial-Suite.git
cd Cemini-Financial-Suite

# Install Python dependencies
pip install -r requirements.txt

# (Optional) Install OpenTimestamps client for Layer 3 verification
pip install opentimestamps-client
```

### Step 1: Navigate to the archive

```bash
ls /mnt/archive/audit/
# Expected:
#   chains/   — daily JSONL chain files
#   batches/  — daily Merkle batch files
```

### Step 2: Run the offline verifier

```bash
python3 scripts/verify.py --archive-root /mnt/archive/audit/
```

**Expected output for a clean chain (exit code 0):**

```
Cemini Financial Suite — Audit Trail Verifier
============================================================
Scanning chain files...
  2026-03-01.jsonl: 47 entries — PASS
  2026-03-02.jsonl: 52 entries — PASS
  ...
Chain integrity: ALL PASS
Merkle batches: ALL PASS
============================================================
AUDIT TRAIL VERIFIED — EXIT 0
```

**Expected output for tampered data (exit code 1):**

```
ERROR: Hash mismatch at entry 23 in 2026-03-07.jsonl
  Expected: a3f9...
  Got:      7b2c...
AUDIT TRAIL FAILED — EXIT 1
```

### Step 3: Manually inspect chain continuity

Open a JSONL chain file and verify:

```python
import json, hashlib

with open("/mnt/archive/audit/chains/2026-03-01.jsonl") as f:
    entries = [json.loads(line) for line in f if line.strip()]

# Verify the hash chain
prev_hash = "0" * 64  # Genesis
for entry in entries:
    # Recompute the expected hash
    payload = json.dumps(entry["payload"], sort_keys=True).encode()
    chain_input = (prev_hash + payload.decode()).encode()
    expected_hash = hashlib.sha256(chain_input).hexdigest()
    assert entry["chain_hash"] == expected_hash, f"Hash mismatch at {entry['entry_id']}"
    prev_hash = expected_hash

print(f"Chain valid: {len(entries)} entries verified")
```

### Step 4: Verify Merkle root consistency

```bash
cat /mnt/archive/audit/batches/2026-03-01/batches.json | python3 -m json.tool
```

Check that the `merkle_root` field matches a commitment stored in the
`audit_batch_commitments` PostgreSQL table.

### Step 5: Verify OpenTimestamps (Layer 3)

```bash
# Install OTS client if not present
pip install opentimestamps-client

# Verify a batch file against the Bitcoin blockchain
ots verify /mnt/archive/audit/batches/2026-03-01/batches.json.ots

# Expected output (after Bitcoin confirmation):
# Success! Bitcoin block [HEIGHT] attests data existed before [DATE]
```

Note: OTS verification requires an internet connection to a Bitcoin node or
public calendar. The `.ots` file can be verified by anyone, anywhere.

### Step 6: Check UUIDv7 monotonicity

All `entry_id` and `commitment_id` fields use UUIDv7, which embeds a millisecond
timestamp in the most significant bits. Verify monotonicity:

```python
import uuid

# UUIDv7 IDs should be lexicographically monotone
ids = [entry["entry_id"] for entry in entries]
assert ids == sorted(ids), "UUIDv7 monotonicity violated"
print("UUIDv7 monotonicity: PASS")
```

### Step 7: Verify intent logs

Intent logs are written BEFORE signal evaluation, proving trades were not
cherry-picked from historical data:

```sql
-- Check that intent_timestamp < evaluation_timestamp for all entries
SELECT entry_id, intent_timestamp, evaluation_timestamp,
       evaluation_timestamp - intent_timestamp AS latency
FROM audit_intent_log
ORDER BY intent_timestamp DESC
LIMIT 20;
```

All `intent_timestamp` values should be earlier than `evaluation_timestamp`,
confirming pre-evaluation logging.

---

## What This Proves

1. **No retroactive insertion**: The hash chain makes it computationally infeasible
   to insert trades into the historical record without breaking every subsequent hash.

2. **No deletion without detection**: Removing any entry breaks the chain from that
   point forward.

3. **Pre-evaluation logging**: Intent logs prove signals were recorded before the
   algorithm evaluated them, ruling out backtest contamination.

4. **Third-party timestamping**: Bitcoin OTS anchors prove the data existed at a
   specific point in time, verifiable by anyone with internet access.

---

## Limitations

- Layer 3 (OTS) requires internet access and Bitcoin confirmation (~1-6 hours)
- OTS verification is best-effort; system continues without it if `ots` binary is absent
- The JSONL archives are on `/mnt/archive/` (separate mount from the OS volume)
- Historical data (pre-gate archives) is quarantined and excluded from the audit trail
