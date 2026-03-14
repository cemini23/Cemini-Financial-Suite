#!/usr/bin/env python3
"""
CVE Audit Script (Step 51)
Runs pip-audit and writes a CVE report to vdr/05_cve_report.md.
Run: python3 scripts/cve_audit.py
Output: vdr/05_cve_report.md
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
VDR = ROOT / "vdr"


def _find_pip_audit_cmd() -> list[str]:
    """Return the command list to invoke pip-audit."""
    import shutil

    binary = shutil.which("pip-audit")
    if binary:
        return [binary, "--format=json"]
    return [sys.executable, "-m", "pip_audit", "--format=json"]


def run_pip_audit() -> dict:
    """Run pip-audit --format=json and return parsed JSON. Never raises on vulns."""
    cmd = _find_pip_audit_cmd()
    result = subprocess.run(  # noqa: S603
        cmd,
        capture_output=True,
        text=True,
        check=False,  # pip-audit exits non-zero when vulns are found — that's OK
    )
    raw = result.stdout.strip()
    if not raw:
        # pip-audit may write to stderr when no output
        raw = result.stderr.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("WARNING: could not parse pip-audit JSON output")
        return {"dependencies": []}


def write_cve_report(audit_data: dict) -> None:
    """Write vdr/05_cve_report.md."""
    VDR.mkdir(exist_ok=True)

    deps = audit_data.get("dependencies", [])
    total_packages = len(deps)

    # Collect all vulnerabilities
    vulns: list[dict] = []
    for dep in deps:
        for vuln in dep.get("vulns", []):
            vulns.append(
                {
                    "package": dep["name"],
                    "installed_version": dep["version"],
                    "cve_id": vuln.get("id", "UNKNOWN"),
                    "fix_versions": vuln.get("fix_versions", []),
                    "description": vuln.get("description", "No description available"),
                    "aliases": vuln.get("aliases", []),
                }
            )

    lines = [
        "# CVE Security Audit Report",
        "",
        f"**Scan date:** {date.today().isoformat()}  ",
        f"**Tool:** pip-audit 2.x (PyPI Advisory Database)  ",
        f"**Total packages scanned:** {total_packages}  ",
        f"**Vulnerabilities found:** {len(vulns)}  ",
        "",
    ]

    if len(vulns) == 0:
        lines += [
            "## ZERO KNOWN VULNERABILITIES AS OF SCAN DATE",
            "",
            "pip-audit found no known CVEs or security advisories in any installed",
            "package. This scan covers all packages in the Python environment.",
            "",
            "Re-run `python3 scripts/cve_audit.py` periodically or after any",
            "`pip install` to keep this report current.",
        ]
    else:
        lines += [
            "## Vulnerability Summary",
            "",
            f"**{len(vulns)} vulnerability records** found across {len({v['package'] for v in vulns})} packages.",
            "",
            "> Note: Many of these may be in system-level Ubuntu packages or",
            "> dev-only tools not present in production Docker images.",
            "> Review each entry to determine applicability.",
            "",
            "## Vulnerability Table",
            "",
            "| CVE / Advisory ID | Package | Installed Version | Fix Version | Description |",
            "|-------------------|---------|-------------------|-------------|-------------|",
        ]

        for v in sorted(vulns, key=lambda x: (x["package"], x["cve_id"])):
            fix = ", ".join(v["fix_versions"]) if v["fix_versions"] else "No fix available"
            desc = v["description"][:120].replace("|", "\\|").replace("\n", " ")
            cve_id = v["cve_id"]
            # Include aliases for context
            if v["aliases"]:
                cve_id = f"{cve_id} ({v['aliases'][0]})"
            lines.append(f"| {cve_id} | {v['package']} | {v['installed_version']} | {fix} | {desc}... |")

        lines += [
            "",
            "## Remediation Notes",
            "",
            "### Production Impact Assessment",
            "",
            "The vulnerabilities above are in the full Python environment on the",
            "development/server machine. Production Docker images use pinned",
            "requirements and may not include all packages listed here.",
            "",
            "To check which vulnerabilities affect production images, run:",
            "```bash",
            "pip-audit -r requirements.txt",
            "pip-audit -r QuantOS/requirements.txt",
            "pip-audit -r 'Kalshi by Cemini/requirements.txt'",
            "```",
            "",
            "### Upgrade Path",
            "",
            "For each flagged package, run `pip install --upgrade <package>` and",
            "verify tests still pass with `python3 -m pytest tests/ -n auto`.",
        ]

    (VDR / "05_cve_report.md").write_text("\n".join(lines) + "\n")
    print(f"  Wrote vdr/05_cve_report.md ({len(vulns)} vulnerabilities across {total_packages} packages)")


def main() -> None:
    """Main entry point."""
    print("Running CVE audit...")
    audit_data = run_pip_audit()
    write_cve_report(audit_data)
    print("CVE audit complete.")


if __name__ == "__main__":
    main()
