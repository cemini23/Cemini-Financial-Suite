"""VCR.py cassette tests for FRED API HTTP interactions (Step 42d).

All tests replay static cassette YAML files — no network or API key needed.
Cassettes are stored in tests/fixtures/vcr_cassettes/.

To re-record cassettes (requires FRED_API_KEY + network):
    VCR_RECORD_MODE=new_episodes python3 -m pytest tests/test_vcr_fred.py -m cassette

CI default: record_mode='none' (replay only).
"""

import os

import pytest

pytestmark = [pytest.mark.cassette]

CASSETTE_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "vcr_cassettes")

try:
    import vcr as vcrpy
    _VCR = vcrpy.VCR(
        cassette_library_dir=CASSETTE_DIR,
        record_mode=os.getenv("VCR_RECORD_MODE", "none"),
        match_on=["method", "scheme", "host", "port", "path"],
        filter_query_parameters=["api_key", "apikey"],
        decode_compressed_response=True,
    )
    HAS_VCR = True
except ImportError:
    HAS_VCR = False


def _skip_if_no_vcr():
    if not HAS_VCR:
        pytest.skip("vcrpy not installed")


# ── T10Y2Y cassette tests ──────────────────────────────────────────────────────

class TestFredT10Y2YCassette:
    """Replay cassette for T10Y2Y (10Y-2Y yield spread) series."""

    def test_t10y2y_fetch_parses_correctly(self):
        """_fetch_series returns correctly parsed observations from cassette."""
        _skip_if_no_vcr()
        from scrapers.fred_monitor import _fetch_series

        with _VCR.use_cassette("fred_t10y2y.yaml"):
            result = _fetch_series("T10Y2Y", "REDACTED", limit=5)

        assert len(result) == 3
        assert result[0]["date"] == "2026-03-12"
        assert result[0]["value"] == pytest.approx(0.42)
        assert result[1]["value"] == pytest.approx(0.38)

    def test_t10y2y_missing_value_sentinel(self):
        """Third observation has '.' value — must parse to None."""
        _skip_if_no_vcr()
        from scrapers.fred_monitor import _fetch_series

        with _VCR.use_cassette("fred_t10y2y.yaml"):
            result = _fetch_series("T10Y2Y", "REDACTED", limit=5)

        # Third record has value "." in cassette
        dot_records = [r for r in result if r["value"] is None]
        assert len(dot_records) == 1, "Expected exactly one '.' value → None"

    def test_t10y2y_observations_sorted_desc(self):
        """FRED sort_order=desc — newest observation is first."""
        _skip_if_no_vcr()
        from scrapers.fred_monitor import _fetch_series

        with _VCR.use_cassette("fred_t10y2y.yaml"):
            result = _fetch_series("T10Y2Y", "REDACTED", limit=5)

        dates = [r["date"] for r in result]
        assert dates == sorted(dates, reverse=True), "Observations not in descending date order"

    def test_t10y2y_channel_config(self):
        """T10Y2Y must map to intel:fred_yield_curve channel."""
        from scrapers.fred_monitor import FRED_SERIES

        assert FRED_SERIES["T10Y2Y"]["channel"] == "intel:fred_yield_curve"
        assert FRED_SERIES["T10Y2Y"]["field"] == "spread_10y2y"

    def test_t10y2y_group_by_channel(self):
        """Observations from cassette group correctly into yield_curve payload."""
        _skip_if_no_vcr()
        from scrapers.fred_monitor import _fetch_series, _group_by_channel

        with _VCR.use_cassette("fred_t10y2y.yaml"):
            obs = _fetch_series("T10Y2Y", "REDACTED", limit=5)

        channels = _group_by_channel({"T10Y2Y": obs})
        assert "intel:fred_yield_curve" in channels
        assert channels["intel:fred_yield_curve"]["spread_10y2y"] == pytest.approx(0.42)


# ── DFF cassette tests ─────────────────────────────────────────────────────────

class TestFredDFFCassette:
    """Replay cassette for DFF (effective fed funds rate) series."""

    def test_dff_fetch_parses_correctly(self):
        """_fetch_series returns DFF observations from cassette."""
        _skip_if_no_vcr()
        from scrapers.fred_monitor import _fetch_series

        with _VCR.use_cassette("fred_dff.yaml"):
            result = _fetch_series("DFF", "REDACTED", limit=5)

        assert len(result) == 3
        assert result[0]["value"] == pytest.approx(5.33)

    def test_dff_channel_config(self):
        """DFF must map to intel:fred_fed_policy channel with fed_funds_rate field."""
        from scrapers.fred_monitor import FRED_SERIES

        assert FRED_SERIES["DFF"]["channel"] == "intel:fred_fed_policy"
        assert FRED_SERIES["DFF"]["field"] == "fed_funds_rate"

    def test_dff_all_values_numeric(self):
        """All DFF cassette observations have numeric values (no '.' sentinel)."""
        _skip_if_no_vcr()
        from scrapers.fred_monitor import _fetch_series

        with _VCR.use_cassette("fred_dff.yaml"):
            result = _fetch_series("DFF", "REDACTED", limit=5)

        none_values = [r for r in result if r["value"] is None]
        assert len(none_values) == 0, "Unexpected None values in DFF cassette"


# ── VCR infrastructure tests ───────────────────────────────────────────────────

class TestVCRInfrastructure:
    """Verify VCR.py cassette infrastructure is correctly set up."""

    def test_cassette_dir_exists(self):
        """Cassette directory must exist."""
        assert os.path.isdir(CASSETTE_DIR), f"Cassette dir missing: {CASSETTE_DIR}"

    def test_cassettes_present(self):
        """At least 2 cassette files must exist."""
        yaml_files = [f for f in os.listdir(CASSETTE_DIR) if f.endswith(".yaml")]
        assert len(yaml_files) >= 2, f"Expected >=2 cassettes, found: {yaml_files}"

    def test_vcr_module_importable(self):
        """vcrpy must be importable."""
        import vcr  # noqa: F401

    def test_cassette_yaml_valid(self):
        """Each cassette must be parseable YAML with required interaction fields."""
        try:
            import yaml
        except ImportError:
            pytest.skip("pyyaml not installed")

        for fname in ["fred_t10y2y.yaml", "fred_dff.yaml"]:
            path = os.path.join(CASSETTE_DIR, fname)
            with open(path) as fh:
                data = yaml.safe_load(fh)
            assert "interactions" in data, f"{fname}: missing 'interactions' key"
            assert len(data["interactions"]) >= 1
            interaction = data["interactions"][0]
            assert "request" in interaction
            assert "response" in interaction
            assert interaction["response"]["status"]["code"] == 200
