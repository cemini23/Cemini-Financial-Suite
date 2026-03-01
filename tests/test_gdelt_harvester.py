"""
Tests for scrapers/gdelt_harvester.py — pure unit tests.

All tests are pure (no network, no Redis, no Postgres) and run in < 2 s.
"""

from datetime import datetime, timezone

import pytest

from scrapers.gdelt_harvester import (
    MARKET_RELEVANT_COUNTRIES,
    classify_risk_level,
    compute_regional_risk,
    compute_risk_score,
    get_cameo_root,
    is_trusted_source,
    score_event_row,
)


# ── compute_risk_score ────────────────────────────────────────────────────────

class TestComputeRiskScore:
    def test_extreme_conflict_scores_high(self):
        """Military action + many sources + very recent → should score ≥ 80."""
        score = compute_risk_score(goldstein=-9.0, num_sources=40, cameo_code="19", age_hours=0.5)
        assert score >= 80

    def test_cooperation_scores_low(self):
        """Cooperative event with few sources → should score < 40."""
        score = compute_risk_score(goldstein=7.0, num_sources=5, cameo_code="06", age_hours=2.0)
        assert score < 40

    def test_output_bounded_0_100(self):
        """Score must always be in [0, 100] regardless of extreme inputs."""
        assert 0 <= compute_risk_score(-10.0, 200, "20", 0.0) <= 100
        assert 0 <= compute_risk_score(10.0, 0, "01", 48.0) <= 100

    def test_recency_decay(self):
        """A recent event must score higher than the same event 12 hours later."""
        recent = compute_risk_score(-7.0, 20, "17", 0.5)
        old = compute_risk_score(-7.0, 20, "17", 12.0)
        assert recent > old

    def test_more_sources_raises_score(self):
        """Holding everything else constant, more sources → higher score."""
        few = compute_risk_score(-5.0, 1, "13", 1.0)
        many = compute_risk_score(-5.0, 50, "13", 1.0)
        assert many > few

    def test_zero_sources_does_not_crash(self):
        score = compute_risk_score(-5.0, 0, "15", 1.0)
        assert isinstance(score, float)
        assert 0 <= score <= 100

    def test_returns_float_with_one_decimal(self):
        score = compute_risk_score(-3.0, 10, "14", 2.0)
        assert score == round(score, 1)

    def test_high_goldstein_lowers_score(self):
        """Positive Goldstein (cooperative) should give a lower score than negative."""
        conflictual = compute_risk_score(-8.0, 10, "13", 1.0)
        cooperative = compute_risk_score(8.0, 10, "13", 1.0)
        assert conflictual > cooperative


# ── classify_risk_level ───────────────────────────────────────────────────────

class TestClassifyRiskLevel:
    def test_critical_boundary(self):
        assert classify_risk_level(80.0) == "CRITICAL"
        assert classify_risk_level(85.0) == "CRITICAL"
        assert classify_risk_level(100.0) == "CRITICAL"

    def test_high_boundary(self):
        assert classify_risk_level(79.9) == "HIGH"
        assert classify_risk_level(60.0) == "HIGH"

    def test_elevated_boundary(self):
        assert classify_risk_level(59.9) == "ELEVATED"
        assert classify_risk_level(40.0) == "ELEVATED"

    def test_low_boundary(self):
        assert classify_risk_level(39.9) == "LOW"
        assert classify_risk_level(0.0) == "LOW"

    def test_exact_thresholds(self):
        """Boundary values must fall in the correct bucket (≥, not >)."""
        assert classify_risk_level(80) == "CRITICAL"
        assert classify_risk_level(60) == "HIGH"
        assert classify_risk_level(40) == "ELEVATED"


# ── get_cameo_root ────────────────────────────────────────────────────────────

class TestGetCameoRoot:
    def test_two_digit_returned_unchanged(self):
        assert get_cameo_root("17") == "17"
        assert get_cameo_root("10") == "10"

    def test_longer_code_truncated(self):
        assert get_cameo_root("171") == "17"
        assert get_cameo_root("1412") == "14"

    def test_single_digit_left_padded(self):
        assert get_cameo_root("6") == "06"
        assert get_cameo_root("1") == "01"

    def test_empty_string_returns_default(self):
        assert get_cameo_root("") == "01"

    def test_none_returns_default(self):
        assert get_cameo_root(None) == "01"

    def test_numeric_input(self):
        assert get_cameo_root(19) == "19"


# ── is_trusted_source ─────────────────────────────────────────────────────────

class TestIsTrustedSource:
    def test_known_wire_services(self):
        assert is_trusted_source("reuters.com")
        assert is_trusted_source("apnews.com")

    def test_known_specialist_outlets(self):
        assert is_trusted_source("ft.com")
        assert is_trusted_source("cfr.org")
        assert is_trusted_source("rand.org")

    def test_bbc_variants(self):
        assert is_trusted_source("bbc.co.uk")
        assert is_trusted_source("bbc.com")

    def test_unknown_domains_rejected(self):
        assert not is_trusted_source("example.com")
        assert not is_trusted_source("fake-blog.xyz")
        assert not is_trusted_source("notreuters.com")

    def test_empty_and_none_rejected(self):
        assert not is_trusted_source("")
        assert not is_trusted_source(None)

    def test_case_insensitive(self):
        assert is_trusted_source("Reuters.com")
        assert is_trusted_source("BBC.CO.UK")
        assert is_trusted_source("BLOOMBERG.COM")

    def test_subdomain_accepted(self):
        """Subdomains of trusted domains should also be trusted."""
        assert is_trusted_source("world.reuters.com")
        assert is_trusted_source("news.bbc.co.uk")


# ── compute_regional_risk ─────────────────────────────────────────────────────

class TestComputeRegionalRisk:
    def _make_event(self, action_geo, actor1, score):
        return {"risk_score": score, "action_geo": action_geo, "actor1_country": actor1}

    def test_middle_east_events_mapped(self):
        events = [self._make_event("IR", "US", 80.0), self._make_event("IL", "", 70.0)]
        result = compute_regional_risk(events)
        assert result["middle_east"] == pytest.approx(75.0, abs=0.1)

    def test_americas_events_mapped(self):
        events = [self._make_event("US", "", 50.0), self._make_event("MX", "", 30.0)]
        result = compute_regional_risk(events)
        assert result["americas"] == pytest.approx(40.0, abs=0.1)

    def test_empty_events_returns_zeros(self):
        result = compute_regional_risk([])
        assert all(v == 0.0 for v in result.values())

    def test_unknown_country_ignored(self):
        events = [self._make_event("ZZ", "XQ", 90.0)]
        result = compute_regional_risk(events)
        assert all(v == 0.0 for v in result.values())

    def test_action_geo_preferred_over_actor(self):
        """When action_geo is set it should take priority over actor1_country."""
        events = [self._make_event("JP", "US", 70.0)]  # action in Asia, actor in Americas
        result = compute_regional_risk(events)
        assert result["asia_pacific"] > 0
        assert result["americas"] == 0.0


# ── score_event_row ───────────────────────────────────────────────────────────

class TestScoreEventRow:
    """Test the event scoring pipeline with synthetic GDELT-like row dicts."""

    _NOW = datetime(2026, 3, 1, 14, 0, tzinfo=timezone.utc)

    def _row(self, **overrides):
        defaults = {
            "Actor1CountryCode": "US",
            "Actor2CountryCode": "IR",
            "ActionGeo_CountryCode": "IR",
            "EventCode": "14",
            "GoldsteinScale": "-5.0",
            "NumSources": "20",
            "NumArticles": "45",
            "AvgTone": "-3.5",
            "SQLDATE": "20260301",
            "SOURCEURL": "https://reuters.com/article/sanctions",
        }
        defaults.update(overrides)
        return defaults

    def test_market_relevant_event_returned(self):
        result = score_event_row(self._row(), self._NOW)
        assert result is not None
        assert 0 <= result["risk_score"] <= 100
        assert result["risk_level"] in ("CRITICAL", "HIGH", "ELEVATED", "LOW")
        assert result["cameo_code"] == "14"
        assert result["actor1_country"] == "US"
        assert result["actor2_country"] == "IR"

    def test_non_relevant_countries_filtered_out(self):
        row = self._row(Actor1CountryCode="ZW", Actor2CountryCode="MG", ActionGeo_CountryCode="TZ")
        assert score_event_row(row, self._NOW) is None

    def test_low_cameo_code_filtered_out(self):
        """CAMEO 01 (statements) is not in HIGH_IMPACT_CAMEO_ROOTS → None."""
        assert score_event_row(self._row(EventCode="01"), self._NOW) is None

    def test_cooperation_code_filtered_out(self):
        """CAMEO 06 (cooperation) is below the high-impact threshold → None."""
        assert score_event_row(self._row(EventCode="06"), self._NOW) is None

    def test_military_action_scores_high(self):
        row = self._row(EventCode="19", GoldsteinScale="-9.0", NumSources="40")
        result = score_event_row(row, self._NOW)
        assert result is not None
        assert result["risk_score"] >= 70

    def test_bad_numeric_fields_handled_gracefully(self):
        row = self._row(GoldsteinScale="", NumSources="N/A", AvgTone="", NumArticles="")
        result = score_event_row(row, self._NOW)
        assert result is not None
        assert result["goldstein_scale"] == 0.0
        assert result["num_sources"] == 0

    def test_missing_actor2_produces_valid_title(self):
        row = self._row(Actor2CountryCode="")
        result = score_event_row(row, self._NOW)
        assert result is not None
        assert "US" in result["title"]

    def test_result_contains_all_required_keys(self):
        result = score_event_row(self._row(), self._NOW)
        assert result is not None
        required_keys = {
            "event_date", "source_url", "source_domain", "title", "cameo_code",
            "cameo_category", "goldstein_scale", "avg_tone", "num_sources",
            "num_articles", "actor1_country", "actor2_country", "action_geo",
            "risk_score", "risk_level", "themes", "payload",
        }
        assert required_keys.issubset(result.keys())

    def test_all_relevant_countries_in_set(self):
        """Spot-check a sample of market-relevant countries."""
        for country in ("US", "CN", "RU", "SA", "UA", "TW"):
            assert country in MARKET_RELEVANT_COUNTRIES
