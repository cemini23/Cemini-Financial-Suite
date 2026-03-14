"""tests/test_vdr.py — Step 51: VDR integrity tests."""
from __future__ import annotations

import json
from pathlib import Path

VDR_ROOT = Path(__file__).parent.parent / "vdr"
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
DOCS_ROOT = Path(__file__).parent.parent / "docs"
MKDOCS_YML = Path(__file__).parent.parent / "mkdocs.yml"


# ── Directory and README ────────────────────────────────────────────────────


def test_vdr_directory_exists() -> None:
    assert VDR_ROOT.is_dir(), "vdr/ directory must exist"


def test_vdr_readme_exists() -> None:
    readme = VDR_ROOT / "README.md"
    assert readme.exists(), "vdr/README.md must exist"
    assert readme.stat().st_size > 100, "vdr/README.md must have content"


# ── All numbered VDR files ──────────────────────────────────────────────────


def test_vdr_all_numbered_files_exist() -> None:
    """01 through 12 must all be present."""
    expected = [
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
    missing = [f for f in expected if not (VDR_ROOT / f).exists()]
    assert not missing, f"Missing VDR files: {missing}"


# ── SBOM (02_sbom.md) ───────────────────────────────────────────────────────


def test_sbom_has_packages() -> None:
    """SBOM must contain table rows (pipe characters)."""
    content = (VDR_ROOT / "02_sbom.md").read_text()
    table_rows = [ln for ln in content.splitlines() if ln.startswith("| ") and "---" not in ln]
    assert len(table_rows) >= 5, "02_sbom.md must have at least 5 table rows"


def test_sbom_has_classification_columns() -> None:
    """SBOM must mention Green, Yellow, and Red classification."""
    content = (VDR_ROOT / "02_sbom.md").read_text()
    assert "Green" in content, "02_sbom.md must mention 'Green' classification"
    assert "Yellow" in content, "02_sbom.md must mention 'Yellow' classification"
    assert "Red" in content, "02_sbom.md must mention 'Red' classification"


# ── License flags JSON (03_license_flags.json) ─────────────────────────────


def test_license_flags_valid_json() -> None:
    """03_license_flags.json must parse as valid JSON."""
    content = (VDR_ROOT / "03_license_flags.json").read_text()
    data = json.loads(content)
    assert isinstance(data, dict), "03_license_flags.json must be a JSON object"


def test_license_flags_has_scan_date() -> None:
    """03_license_flags.json must have a scan_date key."""
    data = json.loads((VDR_ROOT / "03_license_flags.json").read_text())
    assert "scan_date" in data, "03_license_flags.json must have 'scan_date' key"
    assert data["scan_date"], "scan_date must not be empty"


def test_license_flags_counts_add_up() -> None:
    """green + yellow + red must equal total_dependencies."""
    data = json.loads((VDR_ROOT / "03_license_flags.json").read_text())
    total = data.get("total_dependencies", -1)
    green = data.get("green", 0)
    yellow = data.get("yellow", 0)
    red = data.get("red", 0)
    assert green + yellow + red == total, (
        f"green({green}) + yellow({yellow}) + red({red}) = {green + yellow + red} "
        f"!= total_dependencies({total})"
    )


# ── Isolation report (04_isolation_report.md) ──────────────────────────────


def test_isolation_report_covers_pymerkle() -> None:
    """04_isolation_report.md must mention pymerkle."""
    content = (VDR_ROOT / "04_isolation_report.md").read_text()
    assert "pymerkle" in content.lower(), "04_isolation_report.md must mention pymerkle"


def test_isolation_report_covers_psycopg2() -> None:
    """04_isolation_report.md must mention psycopg2."""
    content = (VDR_ROOT / "04_isolation_report.md").read_text()
    assert "psycopg2" in content.lower(), "04_isolation_report.md must mention psycopg2"


def test_isolation_report_has_replacement_options() -> None:
    """04_isolation_report.md must mention replacement options."""
    content = (VDR_ROOT / "04_isolation_report.md").read_text()
    has_replace = "replac" in content.lower()
    assert has_replace, "04_isolation_report.md must mention replacement or replaceable options"


# ── CVE report (05_cve_report.md) ──────────────────────────────────────────


def test_cve_report_exists() -> None:
    """05_cve_report.md must exist and have content."""
    cve_report = VDR_ROOT / "05_cve_report.md"
    assert cve_report.exists(), "vdr/05_cve_report.md must exist"
    assert cve_report.stat().st_size > 100, "05_cve_report.md must have content"


# ── Authorship proof (06_authorship_proof.md) ──────────────────────────────


def test_authorship_proof_exists() -> None:
    """06_authorship_proof.md must exist and have content."""
    proof = VDR_ROOT / "06_authorship_proof.md"
    assert proof.exists(), "vdr/06_authorship_proof.md must exist"
    assert proof.stat().st_size > 200, "06_authorship_proof.md must have content"


def test_authorship_proof_has_section_1235() -> None:
    """06_authorship_proof.md must mention Section 1235."""
    content = (VDR_ROOT / "06_authorship_proof.md").read_text()
    assert "1235" in content, "06_authorship_proof.md must mention 'Section 1235'"


# ── Git stats JSON (07_git_stats.json) ─────────────────────────────────────


def test_git_stats_valid_json() -> None:
    """07_git_stats.json must parse as valid JSON."""
    content = (VDR_ROOT / "07_git_stats.json").read_text()
    data = json.loads(content)
    assert isinstance(data, dict), "07_git_stats.json must be a JSON object"


def test_git_stats_has_total_commits() -> None:
    """07_git_stats.json must have total_commits key."""
    data = json.loads((VDR_ROOT / "07_git_stats.json").read_text())
    assert "total_commits" in data, "07_git_stats.json must have 'total_commits' key"
    assert data["total_commits"] > 0, "total_commits must be positive"


# ── Audit trail guide (09_audit_trail_guide.md) ────────────────────────────


def test_audit_trail_guide_has_verify_script() -> None:
    """09_audit_trail_guide.md must reference scripts/verify.py."""
    content = (VDR_ROOT / "09_audit_trail_guide.md").read_text()
    assert "scripts/verify.py" in content, "09_audit_trail_guide.md must mention scripts/verify.py"


# ── Known issues (11_known_issues.md) ──────────────────────────────────────


def test_known_issues_has_c1_through_c6() -> None:
    """11_known_issues.md must mention C1, C2, C3, and C6."""
    content = (VDR_ROOT / "11_known_issues.md").read_text()
    for issue_id in ["C1", "C2", "C3", "C6"]:
        assert issue_id in content, f"11_known_issues.md must mention {issue_id}"


# ── Deployment guide (12_deployment_guide.md) ──────────────────────────────


def test_deployment_guide_has_docker_compose() -> None:
    """12_deployment_guide.md must mention docker compose."""
    content = (VDR_ROOT / "12_deployment_guide.md").read_text()
    assert "docker compose" in content.lower(), "12_deployment_guide.md must mention docker compose"


# ── Executive summary (01_executive_summary.md) ────────────────────────────


def test_executive_summary_has_key_sections() -> None:
    """01_executive_summary.md must mention key platform differentiators."""
    content = (VDR_ROOT / "01_executive_summary.md").read_text()
    keywords = ["audit trail", "test", "docker", "redis"]
    missing = [kw for kw in keywords if kw.lower() not in content.lower()]
    assert not missing, f"01_executive_summary.md missing key sections: {missing}"


# ── Scripts ─────────────────────────────────────────────────────────────────


def test_license_audit_script_exists() -> None:
    """scripts/license_audit.py must exist."""
    script = SCRIPTS_DIR / "license_audit.py"
    assert script.exists(), "scripts/license_audit.py must exist"


def test_cve_audit_script_exists() -> None:
    """scripts/cve_audit.py must exist."""
    script = SCRIPTS_DIR / "cve_audit.py"
    assert script.exists(), "scripts/cve_audit.py must exist"


def test_authorship_proof_script_exists() -> None:
    """scripts/authorship_proof.py must exist."""
    script = SCRIPTS_DIR / "authorship_proof.py"
    assert script.exists(), "scripts/authorship_proof.py must exist"


def test_generate_vdr_script_exists() -> None:
    """scripts/generate_vdr.py must exist."""
    script = SCRIPTS_DIR / "generate_vdr.py"
    assert script.exists(), "scripts/generate_vdr.py must exist"


# ── Due diligence docs ──────────────────────────────────────────────────────


def test_due_diligence_docs_exist() -> None:
    """All docs/due-diligence/*.md files must exist."""
    dd_dir = DOCS_ROOT / "due-diligence"
    expected = [
        "vdr-overview.md",
        "license-compliance.md",
        "cve-audit.md",
        "authorship.md",
    ]
    missing = [f for f in expected if not (dd_dir / f).exists()]
    assert not missing, f"Missing docs/due-diligence/ files: {missing}"


# ── MkDocs ──────────────────────────────────────────────────────────────────


def test_mkdocs_has_due_diligence_nav() -> None:
    """mkdocs.yml must contain 'Due Diligence' navigation section."""
    content = MKDOCS_YML.read_text()
    assert "Due Diligence" in content, "mkdocs.yml must contain 'Due Diligence' nav entry"
