#!/usr/bin/env python3
"""Cemini Financial Suite — Offline Audit Trail Verifier (Step 43).

Buyer verification script. Runs fully offline — no database connection required.
Works purely from JSONL chain files and batch commitment files.

Usage:
    python3 scripts/verify.py [--archive-root /mnt/archive/audit]

Exit codes:
    0 — Chain is valid (PASS)
    1 — Tamper detected or anomalies found (FAIL)

Buyer instructions:
    1. Copy /mnt/archive/audit/ to your local machine
    2. Run: python3 verify.py --archive-root /path/to/audit/
    3. If .ots files are present, also run:
       ots verify /path/to/audit/ots/YYYY-MM-DD-batches.json.ots
"""

import argparse
import os
import sys

# Allow running from repo root or scripts/ dir
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from shared.audit_trail.verify import verify_chain  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cemini Financial Suite — Offline Audit Trail Verifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--archive-root",
        default=os.getenv("AUDIT_ARCHIVE_DIR", "/mnt/archive/audit"),
        help="Path to audit archive root (default: /mnt/archive/audit)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("  Cemini Financial Suite — Cryptographic Audit Trail Verifier")
    print("  VCP Silver Tier | SHA-256 Hash Chain + Merkle Batch Commitments")
    print("=" * 70)
    print(f"\nArchive root : {args.archive_root}")
    print("Running verification...\n")

    result = verify_chain(args.archive_root)

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"Entries verified   : {result.entry_count}")
    print(f"Batches verified   : {result.batches_verified}")
    print(f"Chain valid        : {'YES' if result.chain_valid else 'NO  ⚠ TAMPER DETECTED'}")
    print(f"Sequence gaps      : {'NONE' if not result.gap_detected else f'GAP AT {result.gap_at_sequence}'}")
    print(f"Merkle roots match : {'YES' if result.merkle_roots_match else 'NO  ⚠'}")

    if result.broken_at_sequence is not None:
        print(f"Chain breaks at    : sequence {result.broken_at_sequence}")

    if result.anomalies:
        print(f"\nAnomalies ({len(result.anomalies)}):")
        for anomaly in result.anomalies:
            print(f"  ⚠  {anomaly}")

    # ── OTS instructions ──────────────────────────────────────────────────────
    import pathlib
    ots_dir = pathlib.Path(args.archive_root) / "ots"
    ots_files = list(ots_dir.glob("*.ots")) if ots_dir.exists() else []
    if ots_files:
        print(f"\nOpenTimestamps proofs found ({len(ots_files)}):")
        for ots_file in sorted(ots_files):
            batches_json = str(ots_file).replace(".ots", "").replace(
                str(ots_dir), str(pathlib.Path(args.archive_root) / "batches")
            )
            print(f"  Run: ots verify {ots_file}")
    else:
        print("\nNote: No .ots OpenTimestamps proofs found.")
        print("  Layer 1 (hash chain) + Layer 2 (Merkle tree) are sufficient for verification.")
        print("  Layer 3 (Bitcoin timestamping) requires the `ots` binary to generate proofs.")

    # ── Final verdict ─────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    if result.chain_valid and result.merkle_roots_match:
        print("  RESULT: PASS — Audit trail integrity verified")
        print("=" * 70)
        return 0
    else:
        print("  RESULT: FAIL — Audit trail integrity check failed")
        print("  The trade history may have been tampered with.")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
