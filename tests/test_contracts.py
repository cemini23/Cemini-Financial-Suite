"""Tests for cemini_contracts package.

All tests are PURE — no Redis, no Postgres, no network calls, no mocks needed.
Sample payloads are copied from actual Phase 1 audit (redis-cli GET output).

Run: pytest tests/test_contracts.py -v
"""

import json
import math
import time

import pytest

from cemini_contracts import (
    AutopilotTradeCandidate,
    BtcVolumeSpikeValue,
    CVaRResult,
    DiscoveryOpportunity,
    DrawdownSnapshot,
    FearGreedIndex,
    FedBiasValue,
    IntelPayload,
    KalshiOpportunity,
    KalshiPosition,
    KellyResult,
    KillSwitchEvent,
    MarketEvent,
    MarketTick,
    PlaybookLog,
    PlaybookSnapshot,
    RegimeClassification,
    RegimeGateDecision,
    RegimeSnapshot,
    RiskAssessment,
    RoverMarket,
    SignalCatalogScan,
    SignalDetection,
    SignalType,
    SocialScoreValue,
    StrategyMode,
    TradeAction,
    TradeResult,
    TradeSignalEnvelope,
    WatchlistEntry,
)
from cemini_contracts._compat import safe_dump, safe_validate

# ── Actual Redis payloads from Phase 1 audit ──────────────────────────────────

FIXTURE_PLAYBOOK_SNAPSHOT = {
    "value": {
        "regime": "RED",
        "detail": {
            "regime": "RED",
            "spy_price": 673.575,
            "ema21": 685.1241,
            "sma50": 688.0739,
            "jnk_tlt_flag": False,
            "confidence": 0.8,
            "timestamp": 1772810466.6269152,
            "reason": "SPY 673.58 < SMA50 688.07",
        },
    },
    "source_system": "playbook_logger",
    "timestamp": 1772810466.6290653,
    "confidence": 1.0,
}

FIXTURE_SPY_TREND = {
    "value": "bullish",
    "source_system": "analyzer",
    "timestamp": 1772810575.8584094,
    "confidence": 0.7,
}

FIXTURE_VIX_LEVEL = {
    "value": 41.0,
    "source_system": "analyzer",
    "timestamp": 1772810575.8563197,
    "confidence": 1.0,
}

FIXTURE_BTC_SENTIMENT = {
    "value": -1.0,
    "source_system": "SatoshiAnalyzer",
    "timestamp": 1772810630.0106494,
    "confidence": 1.0,
}

FIXTURE_FED_BIAS = {
    "value": {"bias": "neutral", "confidence": 0.8},
    "source_system": "PowellAnalyzer",
    "timestamp": 1772810628.8554788,
    "confidence": 0.8,
}

FIXTURE_PORTFOLIO_HEAT = {
    "value": 0.0,
    "source_system": "analyzer",
    "timestamp": 1772810575.8599057,
    "confidence": 0.9,
}

FIXTURE_TRADE_SIGNAL = {
    "pydantic_signal": {
        "target_system": "QuantOS",
        "target_brokerage": "Robinhood",
        "asset_class": "equity",
        "ticker_or_event": "SPY",
        "action": "buy",
        "confidence_score": 0.90,
        "proposed_allocation_pct": 0.02,
        "agent_reasoning": "Entry: SMA Cross RSI < 70",
    },
    "timestamp": "2026-03-06 15:10:26",
    "strategy": "Intelligence_v1",
    "price": 673.575,
    "rsi": 45.2,
}


# ── IntelPayload (generic intel:* envelope) ───────────────────────────────────

class TestIntelPayload:
    def test_playbook_snapshot_validates(self):
        p = safe_validate(IntelPayload, FIXTURE_PLAYBOOK_SNAPSHOT)
        assert p is not None
        assert p.source_system == "playbook_logger"
        assert p.confidence == 1.0
        assert isinstance(p.value, dict)

    def test_spy_trend_validates(self):
        p = safe_validate(IntelPayload, FIXTURE_SPY_TREND)
        assert p is not None
        assert p.value == "bullish"
        assert p.confidence == 0.7

    def test_vix_level_validates(self):
        p = safe_validate(IntelPayload, FIXTURE_VIX_LEVEL)
        assert p is not None
        assert p.value == 41.0

    def test_btc_sentiment_validates(self):
        p = safe_validate(IntelPayload, FIXTURE_BTC_SENTIMENT)
        assert p is not None
        assert p.value == -1.0
        assert p.source_system == "SatoshiAnalyzer"

    def test_fed_bias_validates(self):
        p = safe_validate(IntelPayload, FIXTURE_FED_BIAS)
        assert p is not None
        assert isinstance(p.value, dict)
        assert p.value["bias"] == "neutral"

    def test_portfolio_heat_validates(self):
        p = safe_validate(IntelPayload, FIXTURE_PORTFOLIO_HEAT)
        assert p is not None
        assert p.value == 0.0

    def test_extra_fields_allowed(self):
        payload = dict(FIXTURE_SPY_TREND, extra_unknown_field="surprise")
        p = safe_validate(IntelPayload, payload)
        assert p is not None

    def test_default_timestamp_set(self):
        p = IntelPayload(value=42.0, source_system="test")
        assert p.timestamp > 0
        assert p.confidence == 1.0

    def test_json_string_input(self):
        raw = json.dumps(FIXTURE_SPY_TREND)
        p = safe_validate(IntelPayload, raw)
        assert p is not None
        assert p.value == "bullish"

    def test_bytes_input(self):
        raw = json.dumps(FIXTURE_VIX_LEVEL).encode()
        p = safe_validate(IntelPayload, raw)
        assert p is not None


# ── Nested value models ───────────────────────────────────────────────────────

class TestNestedValueModels:
    def test_fed_bias_value(self):
        fv = FedBiasValue(**FIXTURE_FED_BIAS["value"])
        assert fv.bias == "neutral"
        assert fv.confidence == 0.8

    def test_btc_volume_spike_true(self):
        spike = BtcVolumeSpikeValue(detected=True, multiplier=3.5, symbol="BTC")
        assert spike.detected is True
        assert spike.multiplier == 3.5

    def test_btc_volume_spike_false(self):
        spike = BtcVolumeSpikeValue(detected=False, multiplier=0)
        assert spike.detected is False

    def test_social_score_value(self):
        sv = SocialScoreValue(score=0.35, top_ticker="BTC")
        assert sv.score == 0.35
        assert sv.top_ticker == "BTC"


# ── RegimeSnapshot ────────────────────────────────────────────────────────────

class TestRegimeSnapshot:
    def test_validates_from_actual_detail(self):
        detail = FIXTURE_PLAYBOOK_SNAPSHOT["value"]["detail"]
        rs = safe_validate(RegimeSnapshot, detail)
        assert rs is not None
        assert rs.regime == "RED"
        assert rs.spy_price == 673.575
        assert rs.jnk_tlt_flag is False
        assert rs.sma50 == 688.0739

    def test_extra_fields_allowed(self):
        detail = dict(FIXTURE_PLAYBOOK_SNAPSHOT["value"]["detail"], new_field="ok")
        rs = safe_validate(RegimeSnapshot, detail)
        assert rs is not None

    def test_default_values(self):
        rs = RegimeSnapshot(regime="GREEN")
        assert rs.spy_price == 0.0
        assert rs.jnk_tlt_flag is False
        assert rs.timestamp > 0

    def test_round_trip(self):
        rs = RegimeSnapshot(**FIXTURE_PLAYBOOK_SNAPSHOT["value"]["detail"])
        dumped = safe_dump(rs)
        restored = RegimeSnapshot.model_validate_json(dumped)
        assert restored.regime == rs.regime
        assert restored.spy_price == rs.spy_price


# ── RegimeClassification enum ─────────────────────────────────────────────────

class TestRegimeClassification:
    def test_all_members(self):
        assert RegimeClassification.GREEN == "GREEN"
        assert RegimeClassification.YELLOW == "YELLOW"
        assert RegimeClassification.RED == "RED"
        assert RegimeClassification.UNKNOWN == "UNKNOWN"

    def test_string_coercion(self):
        assert RegimeClassification("GREEN") == RegimeClassification.GREEN


# ── SignalDetection ───────────────────────────────────────────────────────────

class TestSignalDetection:
    def test_instantiates_with_required_fields(self):
        sd = SignalDetection(symbol="SPY", pattern_name="EpisodicPivot")
        assert sd.symbol == "SPY"
        assert sd.detected is True
        assert sd.timestamp > 0

    def test_extra_fields_allowed(self):
        sd = SignalDetection(
            symbol="AAPL", pattern_name="VCP",
            num_contractions=3, tightness_pct=0.05
        )
        assert sd.symbol == "AAPL"

    def test_optional_fields_nullable(self):
        sd = SignalDetection(symbol="QQQ", pattern_name="MomentumBurst")
        assert sd.rsi is None
        assert sd.regime_at_detection is None

    def test_round_trip(self):
        sd = SignalDetection(symbol="SPY", pattern_name="InsideBar212", rsi=42.5)
        dumped = safe_dump(sd)
        restored = SignalDetection.model_validate_json(dumped)
        assert restored.symbol == "SPY"
        assert restored.rsi == 42.5


# ── SignalType enum ───────────────────────────────────────────────────────────

class TestSignalType:
    def test_all_six_members(self):
        expected = {
            "EpisodicPivot", "MomentumBurst", "ElephantBar",
            "VCP", "HighTightFlag", "InsideBar212",
        }
        actual = {st.value for st in SignalType}
        assert actual == expected


# ── TradeSignalEnvelope ───────────────────────────────────────────────────────

class TestTradeSignalEnvelope:
    def test_validates_actual_payload(self):
        env = safe_validate(TradeSignalEnvelope, FIXTURE_TRADE_SIGNAL)
        assert env is not None
        assert env.strategy == "Intelligence_v1"
        assert env.price == 673.575
        assert isinstance(env.pydantic_signal, dict)

    def test_nested_signal_fields(self):
        env = TradeSignalEnvelope(**FIXTURE_TRADE_SIGNAL)
        sig = env.pydantic_signal
        assert sig["action"] == "buy"
        assert sig["ticker_or_event"] == "SPY"

    def test_extra_fields_allowed(self):
        payload = dict(FIXTURE_TRADE_SIGNAL, future_field="ok")
        env = safe_validate(TradeSignalEnvelope, payload)
        assert env is not None

    def test_timestamp_as_string(self):
        env = safe_validate(TradeSignalEnvelope, FIXTURE_TRADE_SIGNAL)
        assert env.timestamp == "2026-03-06 15:10:26"


# ── TradeAction enum ──────────────────────────────────────────────────────────

class TestTradeAction:
    def test_all_members(self):
        assert TradeAction.BUY == "buy"
        assert TradeAction.SELL == "sell"
        assert TradeAction.CANCEL_ALL == "CANCEL_ALL"


# ── StrategyMode enum ─────────────────────────────────────────────────────────

class TestStrategyMode:
    def test_all_members(self):
        assert StrategyMode.CONSERVATIVE == "conservative"
        assert StrategyMode.AGGRESSIVE == "aggressive"
        assert StrategyMode.SNIPER == "sniper"
        assert StrategyMode.STANDARD == "standard"


# ── RiskAssessment ────────────────────────────────────────────────────────────

class TestRiskAssessment:
    def test_from_logger_payload(self):
        payload = {
            "cvar_99": -0.012345,
            "kelly_size": 0.025,
            "nav": 10000.0,
            "drawdown_snapshot": {"peak": 10500.0, "current": 10000.0, "drawdown_pct": -4.76},
        }
        ra = safe_validate(RiskAssessment, payload)
        assert ra is not None
        assert ra.cvar_99 == -0.012345
        assert ra.kelly_size == 0.025
        assert ra.nav == 10000.0

    def test_round_trip(self):
        ra = RiskAssessment(cvar_99=-0.01, kelly_size=0.02, nav=5000.0)
        dumped = safe_dump(ra)
        restored = RiskAssessment.model_validate_json(dumped)
        assert restored.cvar_99 == ra.cvar_99


# ── PlaybookLog ───────────────────────────────────────────────────────────────

class TestPlaybookLog:
    def test_regime_log(self):
        pl = PlaybookLog(
            log_type="regime",
            regime="RED",
            payload={"spy_price": 673.575, "confidence": 0.8},
        )
        assert pl.log_type == "regime"
        assert pl.regime == "RED"
        assert pl.timestamp > 0

    def test_signal_log(self):
        pl = PlaybookLog(
            log_type="signal",
            payload={"pattern_name": "EpisodicPivot", "symbol": "SPY"},
        )
        assert pl.regime is None
        assert pl.payload["pattern_name"] == "EpisodicPivot"

    def test_risk_log(self):
        pl = PlaybookLog(
            log_type="risk",
            regime="RED",
            payload={"cvar_99": -0.01, "kelly_size": 0.02},
        )
        assert pl.log_type == "risk"

    def test_kill_switch_log(self):
        pl = PlaybookLog(
            log_type="kill_switch",
            payload={"event": "kill_switch_triggered", "reason": "PnL velocity"},
        )
        assert pl.regime is None

    def test_round_trip(self):
        pl = PlaybookLog(log_type="regime", regime="GREEN", payload={"spy_price": 590.0})
        dumped = safe_dump(pl)
        restored = PlaybookLog.model_validate_json(dumped)
        assert restored.regime == "GREEN"


# ── KalshiOpportunity ────────────────────────────────────────────────────────

class TestKalshiOpportunity:
    def test_weather_opportunity(self):
        opp = KalshiOpportunity(
            city="MIA",
            bracket="Below 85°F",
            signal="DIAMOND ALPHA",
            expected_value=2.1,
            edge=0.95,
            reason="Model variance 0.8 is low. Consensus is 83°F.",
        )
        assert opp.city == "MIA"
        assert opp.expected_value == 2.1
        assert opp.timestamp > 0

    def test_extra_fields_allowed(self):
        opp = KalshiOpportunity(signal="GOLD ALPHA", expected_value=1.5, edge=0.85, unknown="ok")
        assert opp.signal == "GOLD ALPHA"

    def test_round_trip(self):
        opp = KalshiOpportunity(city="NYC", signal="DIAMOND ALPHA", expected_value=1.8, edge=0.9)
        dumped = safe_dump(opp)
        restored = KalshiOpportunity.model_validate_json(dumped)
        assert restored.city == "NYC"


# ── KillSwitchEvent ───────────────────────────────────────────────────────────

class TestKillSwitchEvent:
    def test_triggered_event(self):
        ev = KillSwitchEvent(
            event="kill_switch_triggered",
            reason="PnL velocity limit hit",
            timestamp=time.time(),
        )
        assert ev.event == "kill_switch_triggered"
        assert "PnL" in ev.reason

    def test_default_values(self):
        ev = KillSwitchEvent()
        assert ev.event == "kill_switch_triggered"
        assert ev.source == "kill_switch"


# ── MarketTick ────────────────────────────────────────────────────────────────

class TestMarketTick:
    def test_minimal_tick(self):
        tick = MarketTick(symbol="SPY", price=673.575)
        assert tick.symbol == "SPY"
        assert tick.price == 673.575
        assert tick.volume is None

    def test_full_tick(self):
        tick = MarketTick(
            symbol="BTC",
            price=65730.0,
            timestamp="2026-03-06T15:10:26Z",
            volume=1234.5,
        )
        assert tick.volume == 1234.5


# ── DiscoveryOpportunity (Step 26 stub) ───────────────────────────────────────

class TestDiscoveryOpportunity:
    def test_instantiates(self):
        opp = DiscoveryOpportunity(
            ticker="AAPL",
            opportunity_type="equity",
            source="gdelt",
            confidence=0.75,
            rationale="Geopolitical catalyst detected",
        )
        assert opp.ticker == "AAPL"
        assert opp.timestamp > 0

    def test_extra_fields_allowed(self):
        opp = DiscoveryOpportunity(ticker="BTC", source="social", future_field=True)
        assert opp.ticker == "BTC"


# ── safe_validate ─────────────────────────────────────────────────────────────

class TestSafeValidate:
    def test_returns_none_on_garbage_string(self):
        assert safe_validate(IntelPayload, "not json at all") is None

    def test_returns_none_on_empty_string(self):
        assert safe_validate(IntelPayload, "") is None

    def test_returns_none_on_wrong_types(self):
        # IntelPayload.value is required — missing field returns None
        assert safe_validate(IntelPayload, {}) is None
        assert safe_validate(RegimeSnapshot, "bad") is None

    def test_never_raises(self):
        for bad_input in [None, 42, [], {}, "", b"", "null", "[]"]:
            try:
                safe_validate(IntelPayload, bad_input)
            except Exception as exc:
                pytest.fail(f"safe_validate raised on {bad_input!r}: {exc}")

    def test_accepts_json_bytes(self):
        raw = json.dumps(FIXTURE_BTC_SENTIMENT).encode()
        result = safe_validate(IntelPayload, raw)
        assert result is not None
        assert result.value == -1.0

    def test_accepts_json_string(self):
        raw = json.dumps(FIXTURE_FED_BIAS)
        result = safe_validate(IntelPayload, raw)
        assert result is not None


# ── safe_dump ─────────────────────────────────────────────────────────────────

class TestSafeDump:
    def test_returns_valid_json_string(self):
        p = IntelPayload(value=42.0, source_system="test")
        dumped = safe_dump(p)
        parsed = json.loads(dumped)
        assert parsed["value"] == 42.0
        assert parsed["source_system"] == "test"

    def test_regime_snapshot_roundtrip(self):
        rs = RegimeSnapshot(regime="GREEN", spy_price=590.0, confidence=0.9)
        dumped = safe_dump(rs)
        restored = RegimeSnapshot.model_validate_json(dumped)
        assert restored.regime == "GREEN"
        assert restored.spy_price == 590.0

    def test_playbook_log_roundtrip(self):
        pl = PlaybookLog(log_type="regime", regime="RED", payload={"key": "val"})
        dumped = safe_dump(pl)
        restored = PlaybookLog.model_validate_json(dumped)
        assert restored.regime == "RED"
        assert restored.payload["key"] == "val"
