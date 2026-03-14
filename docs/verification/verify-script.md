# Hash Chain Verification

The offline verifier (`scripts/verify.py`) allows a buyer to independently verify the integrity of the cryptographic audit trail without any database connection or running services.

---

## What You Need

1. A copy of `/mnt/archive/audit/` from the seller (JSONL chain files + batch files)
2. Python 3.10+ with the `cemini` package installed (or just `scripts/verify.py` + `shared/audit_trail/`)
3. Optional: `ots` binary for Bitcoin timestamp verification

No API keys. No database. No running Docker services.

---

## Running the Verifier

```bash
# From the repo root:
python3 scripts/verify.py --archive-root /path/to/audit/

# Or from the scripts/ directory:
python3 verify.py --archive-root /path/to/audit/
```

---

## Expected Output — Clean Chain

```
🔍 Cemini Financial Suite — Audit Chain Verifier
================================================
Archive root: /mnt/archive/audit/
Chain files found: 47
Total entries verified: 18,432

✅ Chain integrity: PASS
   All 18,432 hash chain entries verified
   No gaps detected in UUIDv7 sequence
   Merkle roots match batch commitments: 47/47

📋 Intent log verification:
   Total scan intentions logged: 94,218
   All intentions precede corresponding detect() calls
   No cherry-picking detected

🎉 VERIFICATION PASSED — Chain is intact and unmodified
```

---

## Expected Output — Tampered Chain

```
🔍 Cemini Financial Suite — Audit Chain Verifier
================================================
Archive root: /path/to/tampered/audit/
Chain files found: 47

❌ Chain integrity: FAIL
   Entry #8,221 (2026-03-07T14:23:11Z): hash mismatch
   Expected: a3f8c2d1...
   Got:      b9e4a0f7...
   Entries #8,221 through #18,432 are INVALID

🚨 VERIFICATION FAILED — Tampering detected at entry 8,221
```

If the chain fails, every entry from the tampered entry forward is invalidated. This is by design — the hash chain makes localized tampering impossible without invalidating the entire tail.

---

## Step-by-Step Buyer Verification Procedure

### Step 1: Copy the archive

```bash
# On the seller's server:
tar -czf audit_export.tar.gz /mnt/archive/audit/
scp user@server:/opt/cemini/audit_export.tar.gz ./

# Extract locally:
tar -xzf audit_export.tar.gz
```

### Step 2: Install verification dependencies

```bash
pip install pymerkle uuid-utils
```

### Step 3: Run the chain verifier

```bash
python3 scripts/verify.py --archive-root ./mnt/archive/audit/
```

Examine the output. A clean chain will show PASS with:
- All entries verified
- No gaps in UUIDv7 sequence
- Merkle roots matching commitments
- All intentions preceding detections

### Step 4: Spot-check specific entries

```bash
# Optional: verify a specific date range
python3 scripts/verify.py \
    --archive-root ./mnt/archive/audit/ \
    --start-date 2026-03-01 \
    --end-date 2026-03-14
```

### Step 5: Verify OpenTimestamps proof (if available)

```bash
# Install ots client
pip install opentimestamps-client

# Verify a batch file's Bitcoin timestamp
ots verify ./mnt/archive/audit/batches/2026-03-14/batches.json.ots
```

Expected output:
```
Success! Bitcoin block 883,241 attests data existed by 2026-03-14 23:47 UTC
```

---

## What the Verifier Checks

| Check | Method | What Passes |
|---|---|---|
| Hash chain integrity | Recompute SHA-256 for each entry | Computed hash == stored hash for all entries |
| Chain linkage | Check `prev_hash` links | Each entry's prev_hash matches prior entry's chain_hash |
| UUIDv7 ordering | Parse timestamp from UUID bits | UUIDs are strictly monotonically increasing |
| Merkle root match | Rebuild InmemoryTree from day's entries | Computed root == stored commitment root |
| Intent precedence | Compare timestamps | All intent entries precede detection entries for same scan |

---

## Source Code

- `scripts/verify.py` — CLI entry point
- `shared/audit_trail/verify.py` — Core verification logic
- `shared/audit_trail/hasher.py` — SHA-256 hash computation (matches database trigger)
- `shared/audit_trail/merkle_batch.py` — pymerkle tree reconstruction
