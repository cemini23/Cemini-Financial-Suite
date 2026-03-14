# Virtual Data Room Overview

The Cemini Financial Suite Virtual Data Room (VDR) is a complete due diligence
package assembled for prospective buyers of the platform's intellectual property.

---

## What's In the VDR

The `vdr/` directory at the repository root contains 13 files:

| File | Type | Description |
|------|------|-------------|
| `README.md` | Static | Navigation guide and regeneration instructions |
| `01_executive_summary.md` | Static | Non-technical platform overview |
| `02_sbom.md` | Generated | Software Bill of Materials with license classification |
| `03_license_flags.json` | Generated | Machine-readable LGPL/GPL flags |
| `04_isolation_report.md` | Generated | Copyleft isolation analysis per dependency |
| `05_cve_report.md` | Generated | CVE vulnerability scan (pip-audit) |
| `06_authorship_proof.md` | Generated | Git authorship for Section 1235 |
| `07_git_stats.json` | Generated | Raw git statistics |
| `08_test_evidence.md` | Static | Test suite summary |
| `09_audit_trail_guide.md` | Static | Buyer verification instructions |
| `10_architecture_reference.md` | Static | Architecture reference |
| `11_known_issues.md` | Static | Transparent technical debt |
| `12_deployment_guide.md` | Static | Clean-room deployment |

---

## How to Use This Package

### For Non-Technical Buyers

Start with `vdr/01_executive_summary.md` for a plain-language overview of what
the platform does and why it has value.

### For Technical Buyers

1. Read `vdr/12_deployment_guide.md` to verify the platform is reproducible on
   fresh hardware.
2. Run the test suite: `python3 -m pytest tests/ -v -n auto`
3. Verify the audit trail: `python3 scripts/verify.py --archive-root /mnt/archive/audit/`
4. Review `vdr/11_known_issues.md` for a transparent list of remaining work.

### For Legal Due Diligence

1. Read `vdr/04_isolation_report.md` for the GPL/LGPL isolation analysis.
2. Read `vdr/06_authorship_proof.md` for the Section 1235 authorship statement.
3. Obtain independent legal counsel before closing any transaction.

---

## How to Regenerate Reports

Dynamic reports (SBOM, CVE, authorship) must be regenerated periodically as
dependencies change:

```bash
cd /opt/cemini
python3 scripts/generate_vdr.py
```

This runs three audit scripts sequentially:

1. `scripts/license_audit.py` — pip-licenses scan → `02_sbom.md`, `03_license_flags.json`, `04_isolation_report.md`
2. `scripts/cve_audit.py` — pip-audit scan → `05_cve_report.md`
3. `scripts/authorship_proof.py` — git log analysis → `06_authorship_proof.md`, `07_git_stats.json`

---

## Integration with CI/CD

The CVE report is kept current via the CI pipeline:

```yaml
# .github/workflows/deploy.yml
- name: Run pip-audit (all requirements files)
  run: |
    pip-audit -r requirements.txt
    pip-audit -r QuantOS/requirements.txt
    pip-audit -r "Kalshi by Cemini/requirements.txt"
    --strict
```

pip-audit runs on every push to `main`. A failed audit blocks deployment.
