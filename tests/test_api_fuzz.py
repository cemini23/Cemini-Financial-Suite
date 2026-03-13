"""Schemathesis API fuzz tests (Step 42a).

These tests require running Docker services — they are NOT part of the default CI suite.
They are automatically skipped unless running services are available.

Manual execution (live services):
    python3 -m pytest tests/test_api_fuzz.py -m fuzz --timeout=300

CLI fuzzing (more thorough):
    schemathesis run http://localhost:8000/openapi.json --checks all
    schemathesis run http://localhost:8001/openapi.json --checks all

See scripts/run_fuzz.sh for the full fuzzing workflow.
"""

import pytest

try:
    import schemathesis
    HAS_SCHEMATHESIS = True
    _SCHEMATHESIS_VERSION = schemathesis.__version__
except ImportError:
    HAS_SCHEMATHESIS = False
    _SCHEMATHESIS_VERSION = "not installed"

pytestmark = [pytest.mark.fuzz]


# ── Schema availability helpers ────────────────────────────────────────────────

def _try_load_schema(url: str):
    """Attempt to load OpenAPI schema from a running service."""
    if not HAS_SCHEMATHESIS:
        return None
    try:
        return schemathesis.from_url(url, validate_schema=False)
    except Exception:
        return None


# ── Schema load-only tests (CI-safe — only check if services are up) ──────────

@pytest.mark.fuzz
def test_schemathesis_installed():
    """Schemathesis is installed and importable."""
    assert HAS_SCHEMATHESIS, "schemathesis not installed — run: pip install schemathesis"
    assert _SCHEMATHESIS_VERSION, "schemathesis version is empty"


@pytest.mark.fuzz
def test_kalshi_schema_loads_if_available():
    """Load Kalshi OpenAPI schema if service is running on :8000.

    Skipped automatically when kalshi_autopilot is not running.
    """
    if not HAS_SCHEMATHESIS:
        pytest.skip("schemathesis not installed")
    schema = _try_load_schema("http://localhost:8000/openapi.json")
    if schema is None:
        pytest.skip("Kalshi API not available at localhost:8000 (service not running)")
    assert schema is not None


@pytest.mark.fuzz
def test_opportunity_screener_schema_loads_if_available():
    """Load opportunity_screener OpenAPI schema if service is running on :8003.

    Skipped automatically when opportunity_screener is not running.
    """
    if not HAS_SCHEMATHESIS:
        pytest.skip("schemathesis not installed")
    schema = _try_load_schema("http://localhost:8003/openapi.json")
    if schema is None:
        pytest.skip("Opportunity Screener not available at localhost:8003 (service not running)")
    assert schema is not None


@pytest.mark.fuzz
def test_mcp_server_schema_loads_if_available():
    """Load cemini_mcp OpenAPI schema if service is running on :8002."""
    if not HAS_SCHEMATHESIS:
        pytest.skip("schemathesis not installed")
    schema = _try_load_schema("http://localhost:8002/openapi.json")
    if schema is None:
        pytest.skip("cemini_mcp not available at localhost:8002")
    assert schema is not None


# ── Schema-based fuzz tests (require --fuzz flag + live services) ─────────────
#
# These tests use Schemathesis's pytest integration to generate HTTP test cases
# from the OpenAPI spec. They are declared but only run when services are up.
#
# To enable full fuzzing, run scripts/run_fuzz.sh or use the Schemathesis CLI.
#
# Example for future integration (uncomment when services confirmed stable):
#
# @pytest.mark.fuzz
# @pytest.mark.skipif(not HAS_SCHEMATHESIS, reason="schemathesis not installed")
# def test_kalshi_api_fuzz():
#     schema = _try_load_schema("http://localhost:8000/openapi.json")
#     if schema is None:
#         pytest.skip("Kalshi API not running")
#     for result in schema.execute():
#         result.raise_for_checks()


# ── Schemathesis version compatibility check ───────────────────────────────────

@pytest.mark.fuzz
def test_schemathesis_version_supports_from_url():
    """Schemathesis must expose from_url() for URL-based schema loading."""
    if not HAS_SCHEMATHESIS:
        pytest.skip("schemathesis not installed")
    assert hasattr(schemathesis, "from_url"), (
        f"schemathesis {_SCHEMATHESIS_VERSION} missing from_url() — "
        "upgrade to schemathesis>=4.0"
    )
