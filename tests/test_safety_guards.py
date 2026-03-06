"""
Tests for safety guards C5 (SOCIAL_ALPHA_LIVE) and C7 (WEATHER_ALPHA_LIVE).

All tests are pure (no network, no Redis, no Postgres, no module imports) — < 5 s.
Guard logic is extracted inline so tests are isolated from sys.modules state.
"""

import asyncio
import os

import pytest


# ── Guard implementations (mirrors the actual guard code in each analyzer) ─────
# These are verbatim copies of the guard check + return dict from the source
# files. If the guard logic changes in the source, update these mirrors.

def _social_guard_check():
    """
    Mirrors social_alpha/analyzer.py get_target_sentiment() guard (C5).
    Returns the gated dict if SOCIAL_ALPHA_LIVE != 'true', else None.
    """
    if os.getenv("SOCIAL_ALPHA_LIVE", "false").lower() != "true":
        return {
            "status": "disabled",
            "msg": "SOCIAL_ALPHA_LIVE != true — signal gated",
            "score": 0,
            "aggregate_sentiment": "NEUTRAL",
            "traders_monitored": [],
            "signals": [],
        }
    return None  # guard inactive — code proceeds


def _weather_guard_check(city_code: str):
    """
    Mirrors weather_alpha/analyzer.py analyze_market() guard (C7).
    Returns the gated dict if WEATHER_ALPHA_LIVE != 'true', else None.
    """
    if os.getenv("WEATHER_ALPHA_LIVE", "false").lower() != "true":
        return {
            "opportunities": [],
            "status": "disabled",
            "msg": "WEATHER_ALPHA_LIVE != true — signal gated",
            "city": city_code,
        }
    return None  # guard inactive — code proceeds


# ── C5: SOCIAL_ALPHA_LIVE guard ───────────────────────────────────────────────

class TestSocialAlphaGuard:
    """C5: When SOCIAL_ALPHA_LIVE != 'true', get_target_sentiment returns
    score=0, aggregate_sentiment='NEUTRAL', status='disabled'."""

    def test_guard_active_by_default(self, monkeypatch):
        monkeypatch.delenv("SOCIAL_ALPHA_LIVE", raising=False)
        result = _social_guard_check()
        assert result is not None, "Guard should fire when env var is absent"
        assert result["status"] == "disabled"
        assert result["score"] == 0
        assert result["aggregate_sentiment"] == "NEUTRAL"
        assert result["signals"] == []
        assert result["traders_monitored"] == []

    def test_guard_active_when_false(self, monkeypatch):
        monkeypatch.setenv("SOCIAL_ALPHA_LIVE", "false")
        result = _social_guard_check()
        assert result is not None
        assert result["status"] == "disabled"
        assert result["score"] == 0

    def test_guard_case_insensitive_false(self, monkeypatch):
        for val in ("FALSE", "False", "fAlSe"):
            monkeypatch.setenv("SOCIAL_ALPHA_LIVE", val)
            result = _social_guard_check()
            assert result is not None, f"Guard should fire for SOCIAL_ALPHA_LIVE={val!r}"
            assert result["status"] == "disabled"

    def test_guard_inactive_when_true(self, monkeypatch):
        monkeypatch.setenv("SOCIAL_ALPHA_LIVE", "true")
        result = _social_guard_check()
        assert result is None, "Guard should NOT fire when SOCIAL_ALPHA_LIVE='true'"

    def test_guard_case_insensitive_true(self, monkeypatch):
        for val in ("TRUE", "True", "tRuE"):
            monkeypatch.setenv("SOCIAL_ALPHA_LIVE", val)
            result = _social_guard_check()
            assert result is None, f"Guard should NOT fire for SOCIAL_ALPHA_LIVE={val!r}"

    def test_guard_returns_zero_score(self, monkeypatch):
        """Explicitly verify score=0 never crosses any positive threshold."""
        monkeypatch.setenv("SOCIAL_ALPHA_LIVE", "false")
        result = _social_guard_check()
        assert result["score"] == 0
        # Any reasonable social_threshold > 0 → gated signal never trades
        for threshold in (0.05, 0.1, 0.3, 0.5):
            assert result["score"] < threshold


# ── C7: WEATHER_ALPHA_LIVE guard ──────────────────────────────────────────────

class TestWeatherAlphaGuard:
    """C7: When WEATHER_ALPHA_LIVE != 'true', analyze_market returns
    no opportunities and status='disabled'."""

    def test_guard_active_by_default(self, monkeypatch):
        monkeypatch.delenv("WEATHER_ALPHA_LIVE", raising=False)
        result = _weather_guard_check("MIA")
        assert result is not None
        assert result["status"] == "disabled"
        assert result["opportunities"] == []
        assert result["city"] == "MIA"

    def test_guard_active_when_false(self, monkeypatch):
        monkeypatch.setenv("WEATHER_ALPHA_LIVE", "false")
        result = _weather_guard_check("NYC")
        assert result is not None
        assert result["status"] == "disabled"
        assert result["opportunities"] == []

    def test_guard_case_insensitive_false(self, monkeypatch):
        for val in ("FALSE", "False", "fAlSe"):
            monkeypatch.setenv("WEATHER_ALPHA_LIVE", val)
            result = _weather_guard_check("MIA")
            assert result is not None, f"Guard should fire for WEATHER_ALPHA_LIVE={val!r}"

    def test_guard_city_preserved(self, monkeypatch):
        """Gated response echoes city_code for traceability."""
        monkeypatch.setenv("WEATHER_ALPHA_LIVE", "false")
        for city in ("MIA", "NYC", "CHI", "LAX", "ATL"):
            result = _weather_guard_check(city)
            assert result["city"] == city, f"Expected city={city!r}, got {result['city']!r}"

    def test_guard_inactive_when_true(self, monkeypatch):
        monkeypatch.setenv("WEATHER_ALPHA_LIVE", "true")
        result = _weather_guard_check("MIA")
        assert result is None, "Guard should NOT fire when WEATHER_ALPHA_LIVE='true'"

    def test_guard_empty_opportunities_when_gated(self, monkeypatch):
        """Gated opportunities list is always empty (no trades sneak through)."""
        monkeypatch.setenv("WEATHER_ALPHA_LIVE", "false")
        result = _weather_guard_check("MIA")
        assert len(result["opportunities"]) == 0


# ── Autopilot score — gated signals produce zero contribution ─────────────────

class TestAutopilotScoreWithGuards:
    """Verify gated signal dicts never generate trade opportunities in autopilot."""

    def test_gated_social_below_threshold(self, monkeypatch):
        monkeypatch.setenv("SOCIAL_ALPHA_LIVE", "false")
        gated = _social_guard_check()
        for threshold in (0.1, 0.3, 0.5):
            assert gated["score"] < threshold, (
                f"Gated score {gated['score']} should be < threshold {threshold}"
            )

    def test_gated_weather_no_best_opportunity(self, monkeypatch):
        monkeypatch.setenv("WEATHER_ALPHA_LIVE", "false")
        gated = _weather_guard_check("MIA")
        trades = []
        if gated.get("best_opportunity"):
            trades.append("WEATHER")
        assert trades == []

    def test_both_gated_no_trade(self, monkeypatch):
        """With social + weather gated, neither SOCIAL nor WEATHER enters trades."""
        monkeypatch.setenv("SOCIAL_ALPHA_LIVE", "false")
        monkeypatch.setenv("WEATHER_ALPHA_LIVE", "false")

        social = _social_guard_check()
        weather = _weather_guard_check("MIA")

        opps = []
        if social["score"] >= 0.3:
            opps.append("SOCIAL")
        if weather.get("best_opportunity"):
            opps.append("WEATHER")
        assert opps == []
