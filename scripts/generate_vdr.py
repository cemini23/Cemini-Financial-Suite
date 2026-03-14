#!/usr/bin/env python3
"""
VDR Assembler (Step 51)
One-command Virtual Data Room generator.
Run: python3 scripts/generate_vdr.py
Runs license_audit.py, cve_audit.py, authorship_proof.py, then verifies all files.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
VDR = ROOT / "vdr"
SCRIPTS = ROOT / "scripts"

# All VDR files that must exist after generation
EXPECTED_FILES = [
    "README.md",
    "01_executive_summary.md",
    "02_sbom.md",
    "03_license_flags.json",
    "04_isolation_report.md",
    "05_cve_report.md",
    "06_authorship_proof.md",
    "07_git_stats.json",
    "08_test_evidence.md",
    "09_audit_trail_guide.md",
    "10_architecture_reference.md",
    "11_known_issues.md",
    "12_deployment_guide.md",
]


def run_script(script_name: str) -> bool:
    """Run a script via subprocess. Return True on success."""
    script_path = SCRIPTS / script_name
    if not script_path.exists():
        print(f"  ERROR: {script_path} not found")
        return False

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(script_path)],
        capture_output=False,  # Let output stream to terminal
        check=False,
        cwd=str(ROOT),
    )
    if result.returncode != 0:
        print(f"  ERROR: {script_name} exited with code {result.returncode}")
        return False
    return True


def verify_files() -> tuple[list[str], list[str]]:
    """Check which VDR files exist and which are missing."""
    present = []
    missing = []
    for fname in EXPECTED_FILES:
        path = VDR / fname
        if path.exists() and path.stat().st_size > 0:
            present.append(fname)
        else:
            missing.append(fname)
    return present, missing


def main() -> None:
    """Main entry point — runs all audit scripts and verifies output."""
    print("=" * 60)
    print("Cemini Financial Suite — VDR Generator (Step 51)")
    print("=" * 60)

    VDR.mkdir(exist_ok=True)

    # Run each audit script
    scripts = [
        ("license_audit.py", "License Compliance Audit"),
        ("cve_audit.py", "CVE Security Audit"),
        ("authorship_proof.py", "Authorship Proof"),
    ]

    all_ok = True
    for script_name, description in scripts:
        print(f"\n[{description}]")
        ok = run_script(script_name)
        if not ok:
            all_ok = False

    # Verify all expected files exist
    print("\n[Verifying VDR completeness]")
    present, missing = verify_files()

    for fname in present:
        size = (VDR / fname).stat().st_size
        print(f"  OK  {fname} ({size:,} bytes)")

    for fname in missing:
        print(f"  MISSING  {fname}")

    print("\n" + "=" * 60)
    print(f"VDR files present:  {len(present)} / {len(EXPECTED_FILES)}")

    if missing:
        print(f"Missing files ({len(missing)}):")
        for fname in missing:
            print(f"  - {fname}")
        print("\nWARNING: VDR is incomplete. Check errors above.")
        all_ok = False
    else:
        print("All VDR files present and non-empty.")

    if not all_ok:
        sys.exit(1)

    print("\nVDR generation complete.")
    print(f"Output directory: {VDR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
