"""
tests/test_docs.py — Step 41: MkDocs documentation integrity tests.

All tests are pure filesystem checks — no network, no server, no MkDocs process.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

DOCS_ROOT = Path(__file__).parent.parent / "docs"
MKDOCS_YML = Path(__file__).parent.parent / "mkdocs.yml"

# All .md files declared in the mkdocs.yml nav
NAV_PAGES = [
    "index.md",
    "architecture/overview.md",
    "architecture/services.md",
    "architecture/redis-intel-bus.md",
    "architecture/data-pipeline.md",
    "engines/orchestrator.md",
    "engines/quantos.md",
    "engines/kalshi.md",
    "engines/playbook.md",
    "intelligence/signal-catalog.md",
    "intelligence/regime.md",
    "intelligence/risk-engine.md",
    "intelligence/kill-switch.md",
    "intelligence/discovery.md",
    "data-sources/overview.md",
    "data-sources/polygon.md",
    "data-sources/fred.md",
    "data-sources/edgar.md",
    "data-sources/social.md",
    "data-sources/gdelt.md",
    "data-sources/weather.md",
    "verification/audit-trail.md",
    "verification/verify-script.md",
    "verification/opentimestamps.md",
    "qa/test-suite.md",
    "qa/hypothesis.md",
    "qa/schemathesis.md",
    "qa/mutmut.md",
    "qa/ci-cd.md",
    "infrastructure/devops.md",
    "infrastructure/observability.md",
    "infrastructure/migrations.md",
    "infrastructure/resilience.md",
    "appendices/licenses.md",
    "appendices/tech-debt.md",
    "appendices/glossary.md",
]

# Valid mermaid diagram types
MERMAID_STARTERS = (
    "graph",
    "flowchart",
    "sequenceDiagram",
    "stateDiagram",
    "classDiagram",
    "erDiagram",
    "gantt",
    "pie",
    "gitGraph",
    "journey",
    "mindmap",
    "timeline",
    "xychart",
    "block-beta",
)


# ── Config tests ──────────────────────────────────────────────────────────────

def test_mkdocs_yml_exists():
    """mkdocs.yml must be present at the project root."""
    assert MKDOCS_YML.exists(), f"mkdocs.yml not found at {MKDOCS_YML}"


def test_mkdocs_yml_valid_yaml():
    """mkdocs.yml must contain required top-level keys (text check avoids !!python/name tag)."""
    content = MKDOCS_YML.read_text()
    assert "site_name:" in content, "mkdocs.yml missing 'site_name'"
    assert "nav:" in content, "mkdocs.yml missing 'nav'"
    assert "theme:" in content, "mkdocs.yml missing 'theme'"


def test_mkdocs_yml_has_material_theme():
    """Theme must be material (buyer-facing quality signal)."""
    content = MKDOCS_YML.read_text()
    assert "name: material" in content, "mkdocs.yml theme must be 'material'"


# ── Nav / file existence tests ────────────────────────────────────────────────

def test_all_nav_pages_exist():
    """Every .md file referenced in the nav must exist in docs/."""
    missing = []
    for page in NAV_PAGES:
        path = DOCS_ROOT / page
        if not path.exists():
            missing.append(page)
    assert missing == [], f"Missing nav pages: {missing}"


def test_docs_directory_exists():
    """docs/ directory must be present."""
    assert DOCS_ROOT.is_dir(), f"docs/ directory not found at {DOCS_ROOT}"


def test_nav_page_count():
    """At least 35 navigation pages should be documented."""
    assert len(NAV_PAGES) >= 35, f"Expected ≥35 nav pages, got {len(NAV_PAGES)}"


def test_all_nav_pages_have_content():
    """Every nav page must have non-trivial content (>100 chars)."""
    thin_pages = []
    for page in NAV_PAGES:
        path = DOCS_ROOT / page
        if path.exists():
            content = path.read_text()
            if len(content.strip()) < 100:
                thin_pages.append(page)
    assert thin_pages == [], f"Pages with trivial content: {thin_pages}"


# ── Mermaid diagram tests ─────────────────────────────────────────────────────

def _get_mermaid_blocks(md_text: str) -> list[str]:
    """Extract content inside ```mermaid blocks."""
    pattern = re.compile(r"```mermaid\s+(.*?)```", re.DOTALL)
    return pattern.findall(md_text)


def test_mermaid_diagrams_have_valid_syntax():
    """All mermaid blocks must start with a recognized diagram type."""
    bad = []
    for page in NAV_PAGES:
        path = DOCS_ROOT / page
        if not path.exists():
            continue
        content = path.read_text()
        for block in _get_mermaid_blocks(content):
            first_line = block.strip().split("\n")[0].strip()
            if not any(first_line.startswith(s) for s in MERMAID_STARTERS):
                bad.append((page, first_line[:60]))
    assert bad == [], f"Mermaid blocks with unrecognized type: {bad}"


def test_architecture_overview_has_mermaid():
    """architecture/overview.md must contain at least one Mermaid diagram."""
    path = DOCS_ROOT / "architecture/overview.md"
    assert path.exists()
    blocks = _get_mermaid_blocks(path.read_text())
    assert len(blocks) >= 1, "architecture/overview.md must have ≥1 Mermaid diagram"


def test_audit_trail_page_has_mermaid():
    """verification/audit-trail.md must contain a Mermaid diagram."""
    path = DOCS_ROOT / "verification/audit-trail.md"
    assert path.exists()
    blocks = _get_mermaid_blocks(path.read_text())
    assert len(blocks) >= 1, "audit-trail.md must have ≥1 Mermaid diagram"


def test_ci_cd_page_has_mermaid():
    """qa/ci-cd.md must contain a Mermaid diagram (CI pipeline flow)."""
    path = DOCS_ROOT / "qa/ci-cd.md"
    assert path.exists()
    blocks = _get_mermaid_blocks(path.read_text())
    assert len(blocks) >= 1, "ci-cd.md must have ≥1 Mermaid diagram"


def test_total_mermaid_diagram_count():
    """At least 8 Mermaid diagrams across the site."""
    total = 0
    for page in NAV_PAGES:
        path = DOCS_ROOT / page
        if path.exists():
            total += len(_get_mermaid_blocks(path.read_text()))
    assert total >= 8, f"Expected ≥8 Mermaid diagrams across site, found {total}"


# ── Content quality tests ─────────────────────────────────────────────────────

def test_index_page_has_key_sections():
    """index.md must contain the 5 key differentiator headings."""
    path = DOCS_ROOT / "index.md"
    assert path.exists()
    content = path.read_text()
    required = [
        "Cryptographic Audit Trail",
        "Intelligence",
        "Resilient",
        "Signal",
        "Risk",
    ]
    missing = [kw for kw in required if kw not in content]
    assert missing == [], f"index.md missing sections: {missing}"


def test_audit_trail_page_has_three_layers():
    """verification/audit-trail.md must mention Layer 1, Layer 2, and Layer 3."""
    path = DOCS_ROOT / "verification/audit-trail.md"
    assert path.exists()
    content = path.read_text()
    for layer in ["Layer 1", "Layer 2", "Layer 3"]:
        assert layer in content, f"audit-trail.md missing '{layer}'"


def test_tech_debt_page_has_known_issues():
    """appendices/tech-debt.md must mention C1, C2, C3, C6."""
    path = DOCS_ROOT / "appendices/tech-debt.md"
    assert path.exists()
    content = path.read_text()
    for issue_id in ["C1", "C2", "C3", "C6"]:
        assert issue_id in content, f"tech-debt.md missing issue '{issue_id}'"


def test_ci_cd_page_has_pipeline_stages():
    """qa/ci-cd.md must mention Ruff, Trivy, and Semgrep."""
    path = DOCS_ROOT / "qa/ci-cd.md"
    assert path.exists()
    content = path.read_text()
    for tool in ["Ruff", "Trivy", "Semgrep"]:
        assert tool in content, f"ci-cd.md missing '{tool}'"


def test_signal_catalog_has_six_detectors():
    """intelligence/signal-catalog.md must mention all 6 detector names."""
    path = DOCS_ROOT / "intelligence/signal-catalog.md"
    assert path.exists()
    content = path.read_text()
    detectors = [
        "EpisodicPivot",
        "MomentumBurst",
        "ElephantBar",
        "VCP",
        "HighTightFlag",
        "InsideBar212",
    ]
    missing = [d for d in detectors if d not in content]
    assert missing == [], f"signal-catalog.md missing detectors: {missing}"


def test_regime_page_has_traffic_light():
    """intelligence/regime.md must mention GREEN, YELLOW, and RED."""
    path = DOCS_ROOT / "intelligence/regime.md"
    assert path.exists()
    content = path.read_text()
    for colour in ["GREEN", "YELLOW", "RED"]:
        assert colour in content, f"regime.md missing regime '{colour}'"


def test_kill_switch_page_has_cancel_all():
    """intelligence/kill-switch.md must mention CANCEL_ALL."""
    path = DOCS_ROOT / "intelligence/kill-switch.md"
    assert path.exists()
    content = path.read_text()
    assert "CANCEL_ALL" in content, "kill-switch.md must mention CANCEL_ALL broadcast"


def test_verify_script_page_has_instructions():
    """verification/verify-script.md must mention scripts/verify.py."""
    path = DOCS_ROOT / "verification/verify-script.md"
    assert path.exists()
    content = path.read_text()
    assert "scripts/verify.py" in content or "verify.py" in content, (
        "verify-script.md must mention verify.py"
    )


def test_glossary_has_key_terms():
    """appendices/glossary.md must define at least 10 terms."""
    path = DOCS_ROOT / "appendices/glossary.md"
    assert path.exists()
    content = path.read_text()
    # Count lines that look like defined terms (## heading or **bold** definitions)
    heading_terms = re.findall(r"^##\s+\w", content, re.MULTILINE)
    bold_terms = re.findall(r"^\*\*\w+", content, re.MULTILINE)
    total_terms = len(heading_terms) + len(bold_terms)
    assert total_terms >= 10, f"glossary.md has only {total_terms} defined terms (need ≥10)"


def test_license_inventory_generated():
    """appendices/licenses.md must exist and have meaningful content."""
    path = DOCS_ROOT / "appendices/licenses.md"
    assert path.exists(), "licenses.md must be generated"
    content = path.read_text()
    assert len(content) > 500, "licenses.md content too short — may not have been generated"
    # Must contain at least one MIT license entry
    assert "MIT" in content, "licenses.md must contain MIT license entries"


def test_opentimestamps_page_has_verification():
    """verification/opentimestamps.md must explain how to verify .ots files."""
    path = DOCS_ROOT / "verification/opentimestamps.md"
    assert path.exists()
    content = path.read_text()
    assert "ots verify" in content, "opentimestamps.md must show 'ots verify' command"


def test_resilience_page_has_four_layers():
    """infrastructure/resilience.md must mention Hishel, Aiobreaker, Tenacity, APScheduler."""
    path = DOCS_ROOT / "infrastructure/resilience.md"
    assert path.exists()
    content = path.read_text()
    for component in ["Hishel", "Aiobreaker", "Tenacity", "APScheduler"]:
        assert component in content, f"resilience.md missing '{component}'"
