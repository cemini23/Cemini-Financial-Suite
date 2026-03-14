# Virtual Data Room (VDR) — Cemini Financial Suite

This directory contains the complete due diligence package for prospective buyers of
the Cemini Financial Suite intellectual property.

## Table of Contents

| File | Description |
|------|-------------|
| [01_executive_summary.md](01_executive_summary.md) | Non-technical platform overview for buyers |
| [02_sbom.md](02_sbom.md) | Software Bill of Materials — all dependencies with license classification |
| [03_license_flags.json](03_license_flags.json) | Machine-readable LGPL/GPL isolation data |
| [04_isolation_report.md](04_isolation_report.md) | Detailed GPL/LGPL isolation analysis per dependency |
| [05_cve_report.md](05_cve_report.md) | CVE vulnerability scan results (pip-audit) |
| [06_authorship_proof.md](06_authorship_proof.md) | Git authorship proof for IRC Section 1235 |
| [07_git_stats.json](07_git_stats.json) | Raw git statistics JSON |
| [08_test_evidence.md](08_test_evidence.md) | Test suite summary and quality metrics |
| [09_audit_trail_guide.md](09_audit_trail_guide.md) | Step-by-step buyer verification instructions |
| [10_architecture_reference.md](10_architecture_reference.md) | Technical architecture reference |
| [11_known_issues.md](11_known_issues.md) | Transparent technical debt register |
| [12_deployment_guide.md](12_deployment_guide.md) | Clean-room deployment instructions |

## How to Regenerate Reports

Dynamic reports (SBOM, CVE, authorship) are generated from live data:

```bash
cd /opt/cemini
python3 scripts/generate_vdr.py
```

This runs all three audit scripts in sequence and verifies all 13 VDR files exist.

Individual scripts:

```bash
python3 scripts/license_audit.py   # Generates 02_sbom.md, 03_license_flags.json, 04_isolation_report.md
python3 scripts/cve_audit.py       # Generates 05_cve_report.md
python3 scripts/authorship_proof.py  # Generates 06_authorship_proof.md, 07_git_stats.json
```

## How to Browse the Full Documentation Site

The complete MkDocs documentation site includes architecture diagrams, engine
documentation, verification guides, and this VDR in a searchable HTML format.

```bash
cd /opt/cemini

# Build the static site
mkdocs build --strict

# Serve locally (opens at http://localhost:8000)
mkdocs serve

# The Due Diligence section is at:
# http://localhost:8000/due-diligence/vdr-overview/
```

## Navigation Guide for Buyers

**Start here for a quick overview:** [01_executive_summary.md](01_executive_summary.md)

**Verify the intellectual property is genuine:**
1. Read [06_authorship_proof.md](06_authorship_proof.md) for the Section 1235 statement
2. Run `python3 scripts/verify.py --archive-root /mnt/archive/audit/` to verify the cryptographic audit trail

**Understand license risks:**
1. Read [03_license_flags.json](03_license_flags.json) for machine-readable flags
2. Read [04_isolation_report.md](04_isolation_report.md) for isolation analysis
3. Obtain independent legal counsel before commercialization

**Verify security posture:**
1. Read [05_cve_report.md](05_cve_report.md) for CVE status
2. Check [08_test_evidence.md](08_test_evidence.md) for test coverage

**Understand technical debt:**
1. Read [11_known_issues.md](11_known_issues.md) for all known issues
2. Read [12_deployment_guide.md](12_deployment_guide.md) to verify reproducibility
