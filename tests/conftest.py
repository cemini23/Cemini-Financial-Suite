"""Cemini Financial Suite — pytest configuration and shared fixtures.

Step 42: Advanced Test Suite
Adds markers, VCR.py configuration, and shared test utilities.
"""

import os
import pytest

# ── Marker registration ────────────────────────────────────────────────────────

def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Pure unit tests (no I/O)")
    config.addinivalue_line("markers", "property: Hypothesis property-based tests")
    config.addinivalue_line("markers", "fuzz: Schemathesis API fuzz tests (requires live services)")
    config.addinivalue_line("markers", "cassette: VCR.py recorded HTTP tests")
    config.addinivalue_line("markers", "slow: Tests that take >5 seconds")


# ── VCR.py shared fixture ─────────────────────────────────────────────────────

CASSETTE_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "vcr_cassettes")


@pytest.fixture
def vcr_instance():
    """Pre-configured VCR instance that filters sensitive data.

    record_mode='none'  in CI  (replay only — cassettes committed to repo)
    record_mode='new_episodes'  locally when FRED API key is present and
    the cassette does not yet exist.
    """
    try:
        import vcr as vcrpy
    except ImportError:
        pytest.skip("vcrpy not installed")

    import re

    def _scrub_request(request):
        if "api_key=" in request.uri:
            request.uri = re.sub(r"api_key=[^&]+", "api_key=REDACTED", request.uri)
        return request

    record_mode = os.getenv("VCR_RECORD_MODE", "none")

    return vcrpy.VCR(
        cassette_library_dir=CASSETTE_DIR,
        record_mode=record_mode,
        match_on=["method", "scheme", "host", "port", "path", "query"],
        filter_headers=["authorization", "x-api-key", "cookie"],
        filter_query_parameters=["api_key", "apikey"],
        decode_compressed_response=True,
        before_record_request=_scrub_request,
    )
