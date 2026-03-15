"""
Tests for core/discord_notifier.py (Step 36 — Discord Alert Enrichment).

All tests are pure — no network, no Redis, no DB.
requests.post and IntelReader.read are mocked throughout.
"""
from __future__ import annotations

import os
import time
from unittest.mock import MagicMock, patch

import pytest

from core.discord_notifier import (
    ALERT_COLORS,
    DiscordNotifier,
    _alerts_enabled,
    get_notifier,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_response(status_code: int = 204) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    return resp


def _notifier(webhook: str = "https://discord.test/hook") -> DiscordNotifier:
    return DiscordNotifier(webhook_url=webhook)


# ---------------------------------------------------------------------------
# _alerts_enabled
# ---------------------------------------------------------------------------


class TestAlertsEnabled:
    def test_default_enabled(self, monkeypatch):
        monkeypatch.delenv("DISCORD_ALERTS_ENABLED", raising=False)
        assert _alerts_enabled() is True

    def test_false_string(self, monkeypatch):
        monkeypatch.setenv("DISCORD_ALERTS_ENABLED", "false")
        assert _alerts_enabled() is False

    def test_zero_string(self, monkeypatch):
        monkeypatch.setenv("DISCORD_ALERTS_ENABLED", "0")
        assert _alerts_enabled() is False

    def test_no_string(self, monkeypatch):
        monkeypatch.setenv("DISCORD_ALERTS_ENABLED", "no")
        assert _alerts_enabled() is False

    def test_true_string(self, monkeypatch):
        monkeypatch.setenv("DISCORD_ALERTS_ENABLED", "true")
        assert _alerts_enabled() is True

    def test_one_string(self, monkeypatch):
        monkeypatch.setenv("DISCORD_ALERTS_ENABLED", "1")
        assert _alerts_enabled() is True


# ---------------------------------------------------------------------------
# send_alert — guard conditions
# ---------------------------------------------------------------------------


class TestSendAlertGuards:
    def test_returns_false_when_alerts_disabled(self, monkeypatch):
        monkeypatch.setenv("DISCORD_ALERTS_ENABLED", "false")
        dn = _notifier()
        assert dn.send_alert("T", "M") is False

    def test_returns_false_when_no_webhook(self, monkeypatch):
        monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
        dn = DiscordNotifier(webhook_url=None)
        assert dn.send_alert("T", "M") is False

    def test_returns_false_when_rate_limited(self):
        dn = _notifier()
        dn._last_sent = time.monotonic()  # just sent
        with patch("core.discord_notifier.IntelReader.read", return_value=None):
            result = dn.send_alert("T", "M", enrich=False)
        assert result is False

    def test_rate_limit_clears_after_gap(self):
        dn = _notifier()
        dn._last_sent = 0.0  # never sent
        with patch("requests.post", return_value=_mock_response(204)):
            with patch("core.discord_notifier.IntelReader.read", return_value=None):
                result = dn.send_alert("T", "M", enrich=False)
        assert result is True


# ---------------------------------------------------------------------------
# send_alert — HTTP success / failure
# ---------------------------------------------------------------------------


class TestSendAlertHttp:
    def test_returns_true_on_204(self):
        dn = _notifier()
        with patch("requests.post", return_value=_mock_response(204)):
            with patch("core.discord_notifier.IntelReader.read", return_value=None):
                assert dn.send_alert("Title", "Msg", enrich=False) is True

    def test_returns_true_on_200(self):
        dn = _notifier()
        with patch("requests.post", return_value=_mock_response(200)):
            with patch("core.discord_notifier.IntelReader.read", return_value=None):
                assert dn.send_alert("Title", "Msg", enrich=False) is True

    def test_returns_false_on_400(self):
        dn = _notifier()
        with patch("requests.post", return_value=_mock_response(400)):
            with patch("core.discord_notifier.IntelReader.read", return_value=None):
                assert dn.send_alert("Title", "Msg", enrich=False) is False

    def test_returns_false_on_exception(self):
        dn = _notifier()
        with patch("requests.post", side_effect=ConnectionError("timeout")):
            with patch("core.discord_notifier.IntelReader.read", return_value=None):
                assert dn.send_alert("Title", "Msg", enrich=False) is False

    def test_updates_last_sent_on_success(self):
        dn = _notifier()
        before = dn._last_sent
        with patch("requests.post", return_value=_mock_response(204)):
            with patch("core.discord_notifier.IntelReader.read", return_value=None):
                dn.send_alert("T", "M", enrich=False)
        assert dn._last_sent > before


# ---------------------------------------------------------------------------
# _build_embed — colour and field construction
# ---------------------------------------------------------------------------


class TestBuildEmbed:
    def test_signal_color(self):
        dn = _notifier()
        embed = dn._build_embed("T", "M", "SIGNAL", {})
        assert embed["color"] == ALERT_COLORS["SIGNAL"]

    def test_critical_color(self):
        dn = _notifier()
        embed = dn._build_embed("T", "M", "CRITICAL", {})
        assert embed["color"] == ALERT_COLORS["CRITICAL"]

    def test_unknown_type_defaults_to_info(self):
        dn = _notifier()
        embed = dn._build_embed("T", "M", "DOES_NOT_EXIST", {})
        assert embed["color"] == ALERT_COLORS["INFO"]

    def test_ticker_field_present(self):
        dn = _notifier()
        embed = dn._build_embed("T", "M", "TRADE", {}, ticker="NVDA")
        names = [f["name"] for f in embed["fields"]]
        assert "Ticker" in names
        assert any(f["value"] == "NVDA" for f in embed["fields"])

    def test_regime_field_from_context(self):
        dn = _notifier()
        embed = dn._build_embed("T", "M", "INFO", {"regime": "GREEN"})
        names = [f["name"] for f in embed["fields"]]
        assert "Regime" in names

    def test_rotation_field_from_context(self):
        dn = _notifier()
        embed = dn._build_embed("T", "M", "INFO", {"rotation_bias": "RISK_ON"})
        names = [f["name"] for f in embed["fields"]]
        assert "Rotation" in names

    def test_vix_field_from_context(self):
        dn = _notifier()
        embed = dn._build_embed("T", "M", "INFO", {"vix_level": 28.5})
        names = [f["name"] for f in embed["fields"]]
        assert "VIX" in names
        vix_field = next(f for f in embed["fields"] if f["name"] == "VIX")
        assert "28.5" in vix_field["value"]

    def test_earnings_cluster_field(self):
        dn = _notifier()
        embed = dn._build_embed("T", "M", "WARNING", {"earnings_cluster": True})
        names = [f["name"] for f in embed["fields"]]
        assert any("Earnings" in n for n in names)

    def test_near_earnings_field(self):
        dn = _notifier()
        embed = dn._build_embed("T", "M", "WARNING", {"ticker_near_earnings": True}, ticker="AAPL")
        names = [f["name"] for f in embed["fields"]]
        assert any("Near Earnings" in n for n in names)

    def test_extra_fields_appended(self):
        dn = _notifier()
        extra = [{"name": "Order ID", "value": "abc123", "inline": False}]
        embed = dn._build_embed("T", "M", "TRADE", {}, extra_fields=extra)
        names = [f["name"] for f in embed["fields"]]
        assert "Order ID" in names

    def test_footer_present(self):
        dn = _notifier()
        embed = dn._build_embed("T", "M", "INFO", {})
        assert "footer" in embed
        assert "Cemini" in embed["footer"]["text"]


# ---------------------------------------------------------------------------
# _gather_context — Intel Bus reads
# ---------------------------------------------------------------------------


class TestGatherContext:
    def _make_intel(self, value):
        return {"value": value, "source_system": "test", "timestamp": 0.0, "confidence": 1.0}

    def test_regime_read_from_snapshot(self):
        dn = _notifier()
        snap = self._make_intel({"regime": "GREEN", "spy_price": 520.0})
        with patch("core.discord_notifier.IntelReader.read", side_effect=lambda k: snap if "snapshot" in k else None):
            ctx = dn._gather_context()
        assert ctx.get("regime") == "GREEN"

    def test_rotation_bias_read(self):
        dn = _notifier()
        sr = self._make_intel({"rotation_bias": "RISK_OFF"})
        with patch("core.discord_notifier.IntelReader.read", side_effect=lambda k: sr if "sector" in k else None):
            ctx = dn._gather_context()
        assert ctx.get("rotation_bias") == "RISK_OFF"

    def test_vix_level_read(self):
        dn = _notifier()
        vix = self._make_intel(25.3)
        with patch("core.discord_notifier.IntelReader.read", side_effect=lambda k: vix if "vix" in k else None):
            ctx = dn._gather_context()
        assert ctx.get("vix_level") == pytest.approx(25.3)

    def test_earnings_cluster_read(self):
        dn = _notifier()
        ec = self._make_intel({"earnings_cluster": True, "reporting_this_week": ["AAPL"], "reporting_soon": []})
        with patch("core.discord_notifier.IntelReader.read", side_effect=lambda k: ec if "earnings" in k else None):
            ctx = dn._gather_context(ticker="AAPL")
        assert ctx.get("earnings_cluster") is True
        assert ctx.get("ticker_near_earnings") is True

    def test_ticker_not_near_earnings(self):
        dn = _notifier()
        ec = self._make_intel({"earnings_cluster": False, "reporting_this_week": [], "reporting_soon": []})
        with patch("core.discord_notifier.IntelReader.read", side_effect=lambda k: ec if "earnings" in k else None):
            ctx = dn._gather_context(ticker="MSFT")
        assert ctx.get("ticker_near_earnings") is False

    def test_intel_bus_failure_returns_empty_context(self):
        dn = _notifier()
        with patch("core.discord_notifier.IntelReader.read", side_effect=Exception("redis down")):
            ctx = dn._gather_context()
        assert ctx == {}


# ---------------------------------------------------------------------------
# get_notifier — singleton
# ---------------------------------------------------------------------------


class TestGetNotifier:
    def test_returns_discord_notifier_instance(self):
        notifier = get_notifier()
        assert isinstance(notifier, DiscordNotifier)

    def test_singleton_same_object(self):
        a = get_notifier()
        b = get_notifier()
        assert a is b
