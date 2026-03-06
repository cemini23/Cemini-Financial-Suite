"""cemini_mcp — pytest tests.

Pure tests: no real Redis, no real Postgres.
All I/O mocked via unittest.mock.patch.
"""
import json
import time
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REDIS_PASS = "cemini_redis_2026"

_NOW = 1772831685.0  # fixed epoch for determinism


def _intel_payload(value, source="test", confidence=1.0, ts_offset=0):
    """Build a canonical IntelPayload JSON string."""
    return json.dumps({
        "value": value,
        "source_system": source,
        "timestamp": _NOW - ts_offset,
        "confidence": confidence,
    })


def _playbook_regime_payload(regime="GREEN"):
    return _intel_payload({
        "regime": regime,
        "detail": {
            "regime": regime,
            "spy_price": 672.3,
            "ema21": 685.0,
            "sma50": 688.0,
            "jnk_tlt_flag": False,
            "confidence": 0.8,
            "timestamp": _NOW,
            "reason": f"SPY below SMA50 → {regime}",
        },
    })


def _playbook_signal_payload():
    return _intel_payload({
        "latest_signal": {
            "symbol": "AAPL",
            "pattern_name": "EpisodicPivot",
            "detected": True,
            "rsi": 28.5,
        },
    })


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def freeze_time(monkeypatch):
    """Freeze time.time() so staleness checks are deterministic."""
    monkeypatch.setattr("cemini_mcp.readers.time.time", lambda: _NOW + 10)
    monkeypatch.setattr("cemini_mcp.server.time.time", lambda: _NOW + 10)


def _make_redis_mock(data: dict):
    """Return a mock Redis client with .get() and .ttl() backed by data."""
    mock = MagicMock()
    mock.get.side_effect = lambda key: data.get(key)
    mock.ttl.side_effect = lambda key: 250 if key in data else -2
    mock.close.return_value = None
    return mock


# ---------------------------------------------------------------------------
# readers.read_intel
# ---------------------------------------------------------------------------

class TestReadIntel:
    def test_returns_dict_on_valid_key(self):
        data = {"intel:spy_trend": _intel_payload("bullish")}
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock(data)):
            from cemini_mcp import readers
            result = readers.read_intel("intel:spy_trend")
        assert result["value"] == "bullish"
        assert result["stale"] is False

    def test_missing_key_returns_stale(self):
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock({})):
            from cemini_mcp import readers
            result = readers.read_intel("intel:nonexistent")
        assert result["stale"] is True
        assert "error" in result

    def test_stale_signal_flagged(self):
        old_ts = _NOW - 700  # older than STALE_THRESHOLD_SEC=600
        stale_payload = json.dumps({
            "value": "bearish",
            "source_system": "analyzer",
            "timestamp": old_ts,
            "confidence": 0.5,
        })
        data = {"intel:spy_trend": stale_payload}
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock(data)):
            with patch("cemini_mcp.readers.STALE_THRESHOLD_SEC", 600):
                from cemini_mcp import readers
                result = readers.read_intel("intel:spy_trend")
        assert result["stale"] is True
        assert result["age_seconds"] > 600

    def test_redis_exception_returns_missing(self):
        mock = MagicMock()
        mock.get.side_effect = Exception("connection refused")
        with patch("cemini_mcp.readers._client", return_value=mock):
            from cemini_mcp import readers
            result = readers.read_intel("intel:spy_trend")
        assert result["stale"] is True


# ---------------------------------------------------------------------------
# Tool: get_regime_status
# ---------------------------------------------------------------------------

class TestGetRegimeStatus:
    def test_returns_regime_on_fresh_data(self):
        data = {"intel:playbook_snapshot": _playbook_regime_payload("RED")}
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock(data)):
            from cemini_mcp.server import get_regime_status
            result = get_regime_status()
        assert result["regime"] == "RED"
        assert "detail" in result
        assert result["stale"] is False

    def test_returns_unknown_when_missing(self):
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock({})):
            from cemini_mcp.server import get_regime_status
            result = get_regime_status()
        assert result["regime"] == "UNKNOWN"

    def test_returns_note_when_snapshot_has_signal(self):
        data = {"intel:playbook_snapshot": _playbook_signal_payload()}
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock(data)):
            from cemini_mcp.server import get_regime_status
            result = get_regime_status()
        assert "note" in result


# ---------------------------------------------------------------------------
# Tool: get_signal_detections
# ---------------------------------------------------------------------------

class TestGetSignalDetections:
    def test_returns_signal_when_present(self):
        data = {"intel:playbook_snapshot": _playbook_signal_payload()}
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock(data)):
            from cemini_mcp.server import get_signal_detections
            result = get_signal_detections()
        assert result["signal"]["pattern_name"] == "EpisodicPivot"
        assert result["signal"]["symbol"] == "AAPL"

    def test_ticker_filter_match(self):
        data = {"intel:playbook_snapshot": _playbook_signal_payload()}
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock(data)):
            from cemini_mcp.server import get_signal_detections
            result = get_signal_detections(ticker="AAPL")
        assert result["signal"] is not None

    def test_ticker_filter_no_match(self):
        data = {"intel:playbook_snapshot": _playbook_signal_payload()}
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock(data)):
            from cemini_mcp.server import get_signal_detections
            result = get_signal_detections(ticker="TSLA")
        assert result["signal"] is None

    def test_returns_note_when_snapshot_has_regime(self):
        data = {"intel:playbook_snapshot": _playbook_regime_payload()}
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock(data)):
            from cemini_mcp.server import get_signal_detections
            result = get_signal_detections()
        assert result["signal"] is None
        assert "note" in result

    def test_no_crash_on_missing_key(self):
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock({})):
            from cemini_mcp.server import get_signal_detections
            result = get_signal_detections()
        assert result["signal"] is None


# ---------------------------------------------------------------------------
# Tool: get_risk_metrics
# ---------------------------------------------------------------------------

class TestGetRiskMetrics:
    def test_returns_risk_from_postgres(self):
        mock_row = (
            json.dumps({"cvar_99": -0.025, "kelly_size": 0.15, "nav": 10000.0, "drawdown_snapshot": {}}),
            _NOW - 30,
        )
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = mock_row
        mock_conn.cursor.return_value = mock_cur
        with patch("cemini_mcp.readers.psycopg2") as mock_pg:
            mock_pg.connect.return_value = mock_conn
            from cemini_mcp.server import get_risk_metrics
            result = get_risk_metrics()
        assert result["cvar_99"] == -0.025
        assert result["kelly_size"] == 0.15
        assert result["stale"] is False

    def test_graceful_on_no_data(self):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cur
        with patch("cemini_mcp.readers.psycopg2") as mock_pg:
            mock_pg.connect.return_value = mock_conn
            from cemini_mcp.server import get_risk_metrics
            result = get_risk_metrics()
        assert result["stale"] is True
        assert "error" in result

    def test_graceful_on_postgres_error(self):
        with patch("cemini_mcp.readers.psycopg2") as mock_pg:
            mock_pg.connect.side_effect = Exception("connection refused")
            from cemini_mcp.server import get_risk_metrics
            result = get_risk_metrics()
        assert result["stale"] is True


# ---------------------------------------------------------------------------
# Tool: get_kalshi_intel
# ---------------------------------------------------------------------------

class TestGetKalshiIntel:
    def _kalshi_payload(self):
        return _intel_payload({
            "active_markets": 796,
            "category_breakdown": {"weather": 28, "crypto": 15, "unmatched": 753},
            "orderbook_tickers": ["TICKER_A", "TICKER_B"],
        })

    def test_returns_full_summary(self):
        data = {"intel:kalshi_orderbook_summary": self._kalshi_payload()}
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock(data)):
            from cemini_mcp.server import get_kalshi_intel
            result = get_kalshi_intel()
        assert result["summary"]["active_markets"] == 796
        assert result["stale"] is False

    def test_category_filter(self):
        data = {"intel:kalshi_orderbook_summary": self._kalshi_payload()}
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock(data)):
            from cemini_mcp.server import get_kalshi_intel
            result = get_kalshi_intel(category="weather")
        assert result["count"] == 28
        assert result["category"] == "weather"

    def test_missing_key_graceful(self):
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock({})):
            from cemini_mcp.server import get_kalshi_intel
            result = get_kalshi_intel()
        assert result["summary"] is None


# ---------------------------------------------------------------------------
# Tool: get_geopolitical_risk
# ---------------------------------------------------------------------------

class TestGetGeopoliticalRisk:
    def test_returns_geo_data(self):
        geo = json.dumps({
            "score": 66.9, "level": "HIGH", "trend": "RISING",
            "top_event": "Military force", "num_high_impact_events": 73,
            "updated_at": "2026-03-06T21:12:47Z",
        })
        regional = json.dumps({"europe": 43.3, "americas": 53.2})
        events = json.dumps([
            {"title": "Event A", "risk_score": 66.9},
            {"title": "Event B", "risk_score": 45.0},
        ])
        data = {
            "intel:geopolitical_risk": geo,
            "intel:regional_risk": regional,
            "intel:conflict_events": events,
        }
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock(data)):
            from cemini_mcp.server import get_geopolitical_risk
            result = get_geopolitical_risk()
        assert result["risk_score"] == 66.9
        assert result["level"] == "HIGH"
        assert result["regional_risk"]["europe"] == 43.3
        assert len(result["top_conflict_events"]) == 2

    def test_returns_stale_when_missing(self):
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock({})):
            from cemini_mcp.server import get_geopolitical_risk
            result = get_geopolitical_risk()
        assert result["stale"] is True


# ---------------------------------------------------------------------------
# Tool: get_sentiment
# ---------------------------------------------------------------------------

class TestGetSentiment:
    def _sentiment_data(self):
        return {
            "intel:btc_sentiment": _intel_payload(-0.5, "SatoshiAnalyzer"),
            "intel:fed_bias": _intel_payload({"bias": "dovish", "confidence": 0.8}, "PowellAnalyzer"),
            "intel:spy_trend": _intel_payload("bullish", "analyzer"),
            "intel:vix_level": _intel_payload(41.0, "analyzer"),
            "intel:portfolio_heat": _intel_payload(0.0, "analyzer"),
            "intel:btc_spy_corr": "1.0",
        }

    def test_all_sources_returned(self):
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock(self._sentiment_data())):
            with patch("cemini_mcp.readers.read_raw", return_value="1.0"):
                from cemini_mcp.server import get_sentiment
                result = get_sentiment()
        assert "btc_sentiment" in result
        assert "spy_trend" in result
        assert "vix_level" in result

    def test_single_source_filter(self):
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock(self._sentiment_data())):
            from cemini_mcp.server import get_sentiment
            result = get_sentiment(source="spy_trend")
        assert "spy_trend" in result
        assert "btc_sentiment" not in result

    def test_unknown_source_returns_error(self):
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock({})):
            from cemini_mcp.server import get_sentiment
            result = get_sentiment(source="nonexistent")
        assert "error" in result


# ---------------------------------------------------------------------------
# Tool: get_strategy_mode
# ---------------------------------------------------------------------------

class TestGetStrategyMode:
    def test_returns_mode(self):
        intel_data = {
            "intel:vix_level": _intel_payload(41.0),
            "intel:spy_trend": _intel_payload("bullish"),
            "intel:portfolio_heat": _intel_payload(0.0),
        }
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock(intel_data)):
            with patch("cemini_mcp.readers.read_raw", return_value="aggressive"):
                from cemini_mcp.server import get_strategy_mode
                result = get_strategy_mode()
        assert result["mode"] == "aggressive"
        assert "supporting_signals" in result

    def test_unknown_when_key_missing(self):
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock({})):
            with patch("cemini_mcp.readers.read_raw", return_value=None):
                from cemini_mcp.server import get_strategy_mode
                result = get_strategy_mode()
        assert result["mode"] == "unknown"


# ---------------------------------------------------------------------------
# Tool: get_data_health
# ---------------------------------------------------------------------------

class TestGetDataHealth:
    def test_healthy_system(self):
        data = {
            "intel:playbook_snapshot": _playbook_regime_payload(),
            "intel:spy_trend": _intel_payload("bullish"),
            "intel:vix_level": _intel_payload(41.0),
        }
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = (5,)
        mock_conn.cursor.return_value = mock_cur
        with patch("cemini_mcp.readers._client", return_value=_make_redis_mock(data)):
            with patch("cemini_mcp.readers.psycopg2") as mock_pg:
                mock_pg.connect.return_value = mock_conn
                from cemini_mcp.server import get_data_health
                result = get_data_health()
        assert result["redis"] == "ok"
        assert result["postgres"] == "ok"
        assert result["healthy_count"] >= 1

    def test_redis_down_graceful(self):
        mock = MagicMock()
        mock.get.side_effect = Exception("connection refused")
        with patch("cemini_mcp.readers._client", side_effect=Exception("connection refused")):
            with patch("cemini_mcp.readers.psycopg2") as mock_pg:
                mock_pg.connect.side_effect = Exception("pg down")
                from cemini_mcp.server import get_data_health
                result = get_data_health()
        assert "error" in result["redis"]
        assert "error" in result["postgres"]
        assert "timestamp" in result
