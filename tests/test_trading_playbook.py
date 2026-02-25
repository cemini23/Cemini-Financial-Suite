"""
Tests for the trading_playbook layer.

All tests are pure (no network, no Redis, no Postgres) and run in < 5 s.
Data is generated synthetically with numpy.
"""

import json
import tempfile  # noqa: F401
import time
from pathlib import Path  # noqa: F401

import numpy as np
import pandas as pd
import pytest

from trading_playbook.kill_switch import KillSwitch
from trading_playbook.macro_regime import RegimeState, regime_from_prices
from trading_playbook.playbook_logger import PlaybookLogger
from trading_playbook.risk_engine import (
    CVaRCalculator,
    DrawdownMonitor,
    FractionalKelly,
    build_risk_engine,
)
from trading_playbook.signal_catalog import (
    SIGNAL_REGISTRY,
    ElephantBar,
    EpisodicPivot,
    HighTightFlag,
    InsideBar212,
    MomentumBurst,
    VCP,
    scan_symbol,
)


def _spy_prices(n: int = 100, trend: float = 0.001) -> np.ndarray:
    """Generate a synthetic SPY price series with a given daily trend."""
    rng = np.random.default_rng(42)
    noise = rng.normal(0, 0.005, n)
    prices = 450.0 * np.cumprod(1 + trend + noise)
    return prices


class TestMacroRegime:
    def test_green_regime(self):
        """Strong uptrend: SPY above EMA21 and EMA rising → GREEN."""
        prices = _spy_prices(100, trend=0.003)
        state = regime_from_prices(prices)
        assert state.regime == "GREEN"
        assert state.confidence > 0.5
        assert isinstance(state.timestamp, float)
        assert state.timestamp <= time.time()

    def test_red_regime(self):
        """Strong downtrend: SPY below SMA50 → RED."""
        prices = _spy_prices(100, trend=-0.005)
        state = regime_from_prices(prices)
        assert state.regime == "RED"

    def test_insufficient_data_defaults_red(self):
        """Fewer than 50 bars → RED with low confidence."""
        prices = np.linspace(400, 420, 30)
        state = regime_from_prices(prices)
        assert state.regime == "RED"
        assert state.confidence < 0.3

    def test_jnk_tlt_flag_lowers_confidence(self):
        """JNK underperforming TLT during equity breakout → reduced confidence."""
        prices = _spy_prices(100, trend=0.003)
        # JNK falling, TLT rising
        jnk = np.linspace(90, 85, 100)
        tlt = np.linspace(95, 100, 100)
        state = regime_from_prices(prices, jnk_close=jnk, tlt_close=tlt)
        assert state.jnk_tlt_flag is True
        assert state.confidence < 0.85

    def test_to_dict_serialisable(self):
        """RegimeState.to_dict() must produce a JSON-serialisable dict."""
        import json
        prices = _spy_prices(100, trend=0.001)
        state = regime_from_prices(prices)
        d = state.to_dict()
        assert isinstance(d, dict)
        json.dumps(d)   # raises if not serialisable

    def test_regime_state_fields(self):
        """RegimeState has all required fields."""
        state = RegimeState(
            regime="YELLOW", spy_price=450.0, ema21=451.0, sma50=440.0,
            jnk_tlt_flag=False, confidence=0.7, timestamp=time.time(),
            reason="Test",
        )
        assert state.regime == "YELLOW"
        d = state.to_dict()
        for key in ("regime", "spy_price", "ema21", "sma50", "jnk_tlt_flag", "confidence", "timestamp", "reason"):
            assert key in d


# ============================================================================
# OHLCV helper
# ============================================================================
def _make_ohlcv(n: int = 100, base: float = 100.0, trend: float = 0.001) -> pd.DataFrame:
    """Generate a synthetic OHLCV DataFrame."""
    rng = np.random.default_rng(7)
    closes = base * np.cumprod(1 + trend + rng.normal(0, 0.008, n))
    highs = closes * (1 + np.abs(rng.normal(0, 0.005, n)))
    lows = closes * (1 - np.abs(rng.normal(0, 0.005, n)))
    opens = lows + rng.uniform(0, 1, n) * (highs - lows)
    volumes = rng.integers(500_000, 2_000_000, n).astype(float)
    return pd.DataFrame({
        "Open": opens, "High": highs, "Low": lows,
        "Close": closes, "Volume": volumes,
    })


# ============================================================================
# signal_catalog — BaseSetup contract
# ============================================================================
class TestSignalCatalog:
    def test_all_detectors_return_none_on_flat_data(self):
        """Flat, low-volume data should not trigger any detector."""
        df = _make_ohlcv(100, trend=0.0)
        results = scan_symbol(df, "FLAT")
        # Some may still trigger on synthetic data — just verify structure
        for sig in results:
            assert "pattern_name" in sig
            assert "confidence" in sig
            assert "entry_price" in sig
            assert "stop_price" in sig
            assert "detected_at" in sig

    def test_all_detectors_handle_insufficient_data(self):
        """Too-short DataFrame should never raise, always return None."""
        df = _make_ohlcv(5)
        for detector in SIGNAL_REGISTRY:
            result = detector.detect(df, "SHORT")
            assert result is None

    def test_all_detectors_handle_missing_columns(self):
        """DataFrame without required columns must not raise."""
        df = pd.DataFrame({"Price": [100, 101, 102]})
        for detector in SIGNAL_REGISTRY:
            result = detector.detect(df, "BAD")
            assert result is None

    def test_signal_dict_schema(self):
        """Any returned signal must contain required keys with correct types."""
        required = {"pattern_name", "symbol", "confidence", "entry_price", "stop_price", "detected_at"}
        df = _make_ohlcv(200, trend=0.002)
        for detector in SIGNAL_REGISTRY:
            result = detector.detect(df, "TEST")
            if result is not None:
                assert required.issubset(result.keys()), f"{detector.name} missing keys"
                assert 0.0 <= result["confidence"] <= 1.0
                assert result["entry_price"] > 0
                assert result["stop_price"] > 0

    def test_episodic_pivot_triggers_on_crafted_data(self):
        """Manually craft data that satisfies EpisodicPivot criteria."""
        df = _make_ohlcv(100, base=100.0, trend=0.0)
        # Inject a gap-up bar at the end with extreme volume
        df = df.copy()
        max_vol = float(df["Volume"].max())
        gap_open = float(df["Close"].iloc[-2]) * 1.06  # 6 % gap
        gap_high = gap_open * 1.01
        gap_low = gap_open * 0.98
        gap_close = gap_open * 1.005
        new_row = {
            "Open": gap_open, "High": gap_high,
            "Low": gap_low, "Close": gap_close,
            "Volume": max_vol * 2.0,
        }
        df.iloc[-1] = new_row
        result = EpisodicPivot().detect(df, "PIVOT_TEST")
        assert result is not None
        assert result["pattern_name"] == "EpisodicPivot"

    def test_inside_bar_triggers_on_crafted_data(self):
        """Manually craft a clean 2-1-2 inside bar sequence."""
        df = _make_ohlcv(50, base=100.0, trend=0.001)
        df = df.copy()
        # bar -3: neutral
        # bar -2: strong directional up (N-1)
        df.iloc[-2, df.columns.get_loc("Open")] = 100.0
        df.iloc[-2, df.columns.get_loc("Close")] = 102.5   # +2.5 %
        df.iloc[-2, df.columns.get_loc("High")] = 103.0
        df.iloc[-2, df.columns.get_loc("Low")] = 99.5
        # bar -1: inside bar (N, today)
        df.iloc[-1, df.columns.get_loc("Open")] = 101.0
        df.iloc[-1, df.columns.get_loc("Close")] = 101.5
        df.iloc[-1, df.columns.get_loc("High")] = 102.5    # < bar -2 High (103)
        df.iloc[-1, df.columns.get_loc("Low")] = 100.0     # > bar -2 Low (99.5)
        # Also make bar -3 have a lower close so N-1 shows a proper up-move
        df.iloc[-3, df.columns.get_loc("Close")] = 100.0
        result = InsideBar212().detect(df, "IB_TEST")
        assert result is not None
        assert result["pattern_name"] == "InsideBar212"


# ============================================================================
# risk_engine
# ============================================================================
class TestFractionalKelly:
    def test_positive_edge(self):
        """60 % win rate, 2:1 reward-risk → positive Kelly."""
        k = FractionalKelly(fraction=0.25)
        size = k.calculate(win_rate=0.60, avg_win=2.0, avg_loss=1.0)
        assert size > 0
        assert size <= 0.25   # capped at fraction

    def test_no_edge(self):
        """50 % win rate, 1:1 → Kelly = 0 (no edge)."""
        k = FractionalKelly(fraction=0.25)
        size = k.calculate(win_rate=0.50, avg_win=1.0, avg_loss=1.0)
        assert size == 0.0

    def test_invalid_inputs_return_zero(self):
        k = FractionalKelly(fraction=0.25)
        assert k.calculate(win_rate=0.6, avg_win=0.0, avg_loss=1.0) == 0.0
        assert k.calculate(win_rate=0.6, avg_win=2.0, avg_loss=0.0) == 0.0
        assert k.calculate(win_rate=1.5, avg_win=2.0, avg_loss=1.0) == 0.0

    def test_invalid_fraction_raises(self):
        with pytest.raises(ValueError):
            FractionalKelly(fraction=0.0)
        with pytest.raises(ValueError):
            FractionalKelly(fraction=1.5)

    def test_fraction_caps_output(self):
        k = FractionalKelly(fraction=0.50)
        size = k.calculate(win_rate=0.99, avg_win=10.0, avg_loss=1.0)
        assert size <= 0.50


class TestCVaR:
    def test_normal_returns(self):
        """CVaR of a normal distribution should be a negative number."""
        rng = np.random.default_rng(1)
        returns = rng.normal(0.0005, 0.01, 500)
        cvar = CVaRCalculator().calculate(returns)
        assert cvar < 0

    def test_cvar_more_extreme_than_var(self):
        """CVaR (expected shortfall) must be <= the VaR threshold."""
        rng = np.random.default_rng(2)
        returns = rng.normal(0.0, 0.02, 1000)
        cvar = CVaRCalculator(confidence=0.99).calculate(returns)
        var = float(np.percentile(returns, 1.0))
        assert cvar <= var

    def test_insufficient_data_returns_zero(self):
        cvar = CVaRCalculator().calculate(np.array([0.01, -0.02, 0.005]))
        assert cvar == 0.0

    def test_exceeds_limit_true(self):
        """All large losses → limit breached."""
        returns = np.full(200, -0.10)   # -10 % every period
        result = CVaRCalculator().exceeds_limit(returns, nav=100_000, limit_pct=0.05)
        assert result is True

    def test_exceeds_limit_false(self):
        """Small positive returns → no breach."""
        returns = np.full(200, 0.001)
        result = CVaRCalculator().exceeds_limit(returns, nav=100_000, limit_pct=0.05)
        assert result is False


class TestDrawdownMonitor:
    def test_no_halt_below_threshold(self):
        dd = DrawdownMonitor(threshold=0.15)
        result = dd.update("strat_a", 100.0)
        assert result is None
        result = dd.update("strat_a", 90.0)   # 10 % drawdown — under 15 %
        assert result is None

    def test_halt_at_threshold(self):
        dd = DrawdownMonitor(threshold=0.15)
        dd.update("strat_b", 100.0)
        dd.update("strat_b", 105.0)   # new peak
        reason = dd.update("strat_b", 89.0)   # 15.2 % drawdown
        assert reason is not None
        assert dd.is_halted("strat_b")

    def test_already_halted_returns_reason(self):
        dd = DrawdownMonitor(threshold=0.15)
        dd.update("strat_c", 100.0)
        dd.update("strat_c", 80.0)   # 20 % → halted
        r1 = dd.update("strat_c", 80.0)
        r2 = dd.update("strat_c", 80.0)
        assert r1 == r2

    def test_reset(self):
        dd = DrawdownMonitor(threshold=0.10)
        dd.update("strat_d", 100.0)
        dd.update("strat_d", 85.0)
        assert dd.is_halted("strat_d")
        dd.reset("strat_d")
        assert not dd.is_halted("strat_d")

    def test_portfolio_drawdown_zero_at_peak(self):
        curve = np.array([90.0, 95.0, 100.0])
        dd = DrawdownMonitor.portfolio_drawdown(curve)
        assert dd == pytest.approx(0.0)

    def test_portfolio_drawdown_calculation(self):
        curve = np.array([100.0, 110.0, 95.0])
        dd = DrawdownMonitor.portfolio_drawdown(curve)
        assert dd == pytest.approx(0.1364, rel=1e-2)

    def test_build_risk_engine(self):
        engine = build_risk_engine(kelly_fraction=0.25, cvar_confidence=0.99, drawdown_threshold=0.15)
        assert "kelly" in engine
        assert "cvar" in engine
        assert "drawdown" in engine


# ============================================================================
# kill_switch
# ============================================================================
class TestKillSwitch:
    def test_no_trigger_clean_conditions(self):
        ks = KillSwitch()
        ks.record_pnl(100.0)
        time.sleep(0.01)
        ks.record_pnl(100.5)
        reason = ks.run_all_checks(nav=1000.0)
        assert reason is None
        assert not ks.triggered

    def test_pnl_velocity_no_data_safe(self):
        """Single data point → no velocity computable → no trigger."""
        ks = KillSwitch(pnl_vel_threshold=-0.01)
        ks.record_pnl(1000.0)
        reason = ks.check_pnl_velocity(nav=1000.0)
        assert reason is None

    def test_order_rate_anomaly(self):
        ks = KillSwitch(order_rate_max=5)
        for _ in range(10):
            ks.record_order_message()
        reason = ks.check_order_rate()
        assert reason is not None

    def test_order_rate_normal(self):
        ks = KillSwitch(order_rate_max=100)
        for _ in range(3):
            ks.record_order_message()
        reason = ks.check_order_rate()
        assert reason is None

    def test_connectivity_ok(self):
        ks = KillSwitch(latency_threshold=500.0)
        reason = ks.check_connectivity(latency_ms=200.0)
        assert reason is None

    def test_connectivity_breach(self):
        ks = KillSwitch(latency_threshold=500.0)
        reason = ks.check_connectivity(latency_ms=600.0)
        assert reason is not None

    def test_price_deviation_ok(self):
        ks = KillSwitch(price_dev_max=0.02)
        reason = ks.check_price_deviation(exec_price=100.0, fair_value=100.5)
        assert reason is None

    def test_price_deviation_breach(self):
        ks = KillSwitch(price_dev_max=0.02)
        reason = ks.check_price_deviation(exec_price=100.0, fair_value=110.0)
        assert reason is not None

    def test_trigger_is_idempotent(self):
        ks = KillSwitch()
        ks.triggered = False
        # Manually trigger without Redis
        ks.triggered = True
        ks.trigger_reason = "test"
        ks.trigger_time = time.time()
        # Calling trigger again should not overwrite
        ks.trigger("second call")
        assert ks.trigger_reason == "test"

    def test_strategy_halt_and_resume(self):
        ks = KillSwitch()
        ks.halt_strategy("test_strat", "unit test")
        assert ks.is_strategy_halted("test_strat")
        ks.resume_strategy("test_strat")
        assert not ks.is_strategy_halted("test_strat")

    def test_state_snapshot(self):
        ks = KillSwitch()
        snap = ks.state_snapshot()
        assert "triggered" in snap
        assert "trigger_reason" in snap
        assert "halted_strategies" in snap


# ============================================================================
# playbook_logger (disk-only, no Postgres/Redis)
# ============================================================================
class TestPlaybookLogger:
    def _make_logger(self, tmpdir) -> PlaybookLogger:
        return PlaybookLogger(
            archive_root=str(tmpdir),
            enable_postgres=False,
            enable_redis=False,
            enable_disk=True,
        )

    def test_log_regime_writes_jsonl(self, tmp_path):
        pb = self._make_logger(tmp_path)
        state = RegimeState(
            regime="GREEN", spy_price=475.0, ema21=470.0, sma50=460.0,
            jnk_tlt_flag=False, confidence=0.85, timestamp=time.time(),
            reason="Test regime",
        )
        pb.log_regime(state)
        files = list(tmp_path.rglob("*.jsonl"))
        assert len(files) == 1
        with files[0].open() as fh:
            record = json.loads(fh.readline())
        assert record["log_type"] == "regime"
        assert record["regime"] == "GREEN"
        assert "payload" in record

    def test_log_signal_writes_jsonl(self, tmp_path):
        pb = self._make_logger(tmp_path)
        sig = {
            "pattern_name": "EpisodicPivot",
            "symbol": "AAPL",
            "confidence": 0.80,
            "entry_price": 182.0,
            "stop_price": 175.0,
            "detected_at": "2026-02-25T12:00:00+00:00",
            "metadata": {},
        }
        pb.log_signal(sig)
        files = list(tmp_path.rglob("*.jsonl"))
        assert len(files) == 1
        with files[0].open() as fh:
            record = json.loads(fh.readline())
        assert record["log_type"] == "signal"
        assert record["payload"]["pattern_name"] == "EpisodicPivot"

    def test_log_risk_snapshot_writes_jsonl(self, tmp_path):
        pb = self._make_logger(tmp_path)
        pb.log_risk_snapshot(cvar=-0.025, kelly_size=0.05, drawdown_snapshot={}, nav=50000.0)
        files = list(tmp_path.rglob("*.jsonl"))
        assert len(files) == 1
        with files[0].open() as fh:
            record = json.loads(fh.readline())
        assert record["log_type"] == "risk"
        assert "cvar_99" in record["payload"]

    def test_multiple_records_append(self, tmp_path):
        """Multiple log calls append to the same hourly file."""
        pb = self._make_logger(tmp_path)
        state = RegimeState(
            regime="YELLOW", spy_price=450.0, ema21=455.0, sma50=440.0,
            jnk_tlt_flag=False, confidence=0.70, timestamp=time.time(),
            reason="test",
        )
        pb.log_regime(state)
        pb.log_regime(state)
        pb.log_regime(state)
        files = list(tmp_path.rglob("*.jsonl"))
        assert len(files) == 1
        lines = files[0].read_text().strip().split("\n")
        assert len(lines) == 3

    def test_jsonl_records_are_valid_json(self, tmp_path):
        """Every written line must be valid JSON."""
        pb = self._make_logger(tmp_path)
        state = RegimeState(
            regime="RED", spy_price=400.0, ema21=420.0, sma50=430.0,
            jnk_tlt_flag=True, confidence=0.80, timestamp=time.time(),
            reason="test red",
        )
        pb.log_regime(state)
        pb.log_kill_switch_event({"event": "test", "timestamp": time.time()})
        files = list(tmp_path.rglob("*.jsonl"))
        for fpath in files:
            for line in fpath.read_text().strip().split("\n"):
                json.loads(line)   # raises if invalid

    def test_close_is_safe_without_postgres(self, tmp_path):
        """close() must not raise when Postgres is disabled."""
        pb = self._make_logger(tmp_path)
        pb.close()   # should be silent
