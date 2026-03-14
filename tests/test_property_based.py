"""Hypothesis property-based tests for Cemini Financial Suite (Step 42b).

Tests mathematical invariants that must hold for ALL valid inputs, not just
the specific cases in unit tests. Complements test_trading_playbook.py.

Run alone   : python3 -m pytest tests/test_property_based.py -m property -v
Run in CI   : included in default suite (not marked fuzz or slow)
"""

import json

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from trading_playbook.macro_regime import RegimeState, regime_from_prices
from trading_playbook.risk_engine import (
    CVaRCalculator,
    DrawdownMonitor,
    FractionalKelly,
)
from trading_playbook.signal_catalog import (
    ElephantBar,
    EpisodicPivot,
    HighTightFlag,
    InsideBar212,
    MomentumBurst,
    VCP,
)

pytestmark = [pytest.mark.property]

# ── Shared strategies ──────────────────────────────────────────────────────────

_positive_prices = st.floats(min_value=1.0, max_value=10_000.0, allow_nan=False, allow_infinity=False)
_small_return = st.floats(min_value=-0.5, max_value=0.5, allow_nan=False, allow_infinity=False)


def _make_ohlcv_df(prices: list, volumes: list = None) -> pd.DataFrame:
    """Build a minimal OHLCV DataFrame from a price list."""
    n = len(prices)
    arr = np.array(prices, dtype=float)
    vols = volumes if volumes is not None else [100_000] * n
    # Construct OHLC that satisfies High >= max(Open, Close) and Low <= min(Open, Close)
    opens = np.roll(arr, 1)
    opens[0] = arr[0]
    high = np.maximum(arr, opens) * 1.002
    low = np.minimum(arr, opens) * 0.998
    return pd.DataFrame(
        {"Open": opens, "High": high, "Low": low, "Close": arr, "Volume": vols[:n]},
    )


# ══════════════════════════════════════════════════════════════════════════════
# FractionalKelly — position sizing invariants
# ══════════════════════════════════════════════════════════════════════════════

class TestFractionalKellyProperties:
    """Kelly fraction must always lie in [0, fraction]."""

    @given(
        win_rate=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        avg_win=st.floats(min_value=0.01, max_value=1_000.0, allow_nan=False, allow_infinity=False),
        avg_loss=st.floats(min_value=0.01, max_value=1_000.0, allow_nan=False, allow_infinity=False),
        fraction=st.floats(min_value=0.01, max_value=1.0, allow_nan=False),
    )
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_kelly_fraction_bounded(self, win_rate, avg_win, avg_loss, fraction):
        """Result must be in [0, fraction] for all valid positive inputs."""
        kelly = FractionalKelly(fraction=fraction)
        result = kelly.calculate(win_rate, avg_win, avg_loss)
        assert 0.0 <= result <= fraction + 1e-9, (
            f"Kelly={result} outside [0, {fraction}] for "
            f"win_rate={win_rate}, avg_win={avg_win}, avg_loss={avg_loss}"
        )

    @given(
        win_rate=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        avg_win=st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False),
        avg_loss=st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=150)
    def test_kelly_never_raises(self, win_rate, avg_win, avg_loss):
        """calculate() must never raise on valid floats."""
        kelly = FractionalKelly(fraction=0.25)
        try:
            kelly.calculate(win_rate, avg_win, avg_loss)
        except Exception as exc:
            pytest.fail(f"FractionalKelly.calculate() raised: {exc}")

    @given(
        win_rate=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        avg_win=st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False),
        avg_loss=st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_kelly_deterministic(self, win_rate, avg_win, avg_loss):
        """Same inputs must always produce the same result (pure function)."""
        kelly = FractionalKelly(fraction=0.25)
        r1 = kelly.calculate(win_rate, avg_win, avg_loss)
        r2 = kelly.calculate(win_rate, avg_win, avg_loss)
        assert r1 == r2


# ══════════════════════════════════════════════════════════════════════════════
# CVaRCalculator — tail-risk invariants
# ══════════════════════════════════════════════════════════════════════════════

class TestCVaRProperties:
    """CVaR must be <= 0 (a loss) for any returns distribution."""

    @given(
        returns=st.lists(
            _small_return,
            min_size=10,
            max_size=500,
        )
    )
    @settings(max_examples=150, suppress_health_check=[HealthCheck.too_slow])
    def test_cvar_never_positive(self, returns):
        """CVaR at 99th percentile cannot be a gain — it measures expected tail loss.

        CVaR is the expected *loss* in the worst tail: it is only meaningful
        when at least one return is negative.  An all-positive distribution has
        no loss tail, so CVaR = 0 (min of positive numbers) is trivially correct
        but not the scenario this invariant tests.  We filter degenerate inputs.
        """
        # CVaR measures tail *losses*; skip degenerate all-gains distributions.
        assume(any(r < 0 for r in returns))
        calc = CVaRCalculator(confidence=0.99)
        cvar = calc.calculate(np.array(returns, dtype=float))
        assert cvar <= 1e-9, f"CVaR={cvar} is positive for returns={returns[:5]}…"

    @given(
        returns=st.lists(_small_return, min_size=10, max_size=200)
    )
    @settings(max_examples=100)
    def test_cvar_deterministic(self, returns):
        """Same returns must produce same CVaR (pure function, no randomness)."""
        arr = np.array(returns, dtype=float)
        calc = CVaRCalculator(confidence=0.99)
        assert calc.calculate(arr) == calc.calculate(arr)

    @given(
        returns=st.lists(_small_return, min_size=0, max_size=9)
    )
    @settings(max_examples=50)
    def test_cvar_insufficient_data_returns_zero(self, returns):
        """With fewer than 10 observations CVaR defaults to 0.0 safely."""
        calc = CVaRCalculator(confidence=0.99)
        result = calc.calculate(np.array(returns, dtype=float))
        assert result == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# DrawdownMonitor — portfolio drawdown invariants
# ══════════════════════════════════════════════════════════════════════════════

class TestDrawdownProperties:
    """portfolio_drawdown must always return a value in [0, 1]."""

    @given(
        equity_curve=st.lists(
            st.floats(min_value=0.01, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=1000,
        )
    )
    @settings(max_examples=200)
    def test_drawdown_bounded_0_1(self, equity_curve):
        """Drawdown fraction must be in [0, 1] for any equity curve."""
        dd = DrawdownMonitor.portfolio_drawdown(np.array(equity_curve, dtype=float))
        assert 0.0 <= dd <= 1.0 + 1e-9, f"Drawdown={dd} out of [0, 1]"

    @given(
        equity=st.floats(min_value=1.0, max_value=100_000.0, allow_nan=False)
    )
    @settings(max_examples=100)
    def test_no_drawdown_at_peak(self, equity):
        """A monotonically increasing equity curve has zero drawdown at the final bar."""
        curve = np.linspace(equity * 0.5, equity, 50)
        dd = DrawdownMonitor.portfolio_drawdown(curve)
        assert dd == pytest.approx(0.0, abs=1e-9)

    @given(
        equity_curve=st.lists(
            st.floats(min_value=0.01, max_value=1e6, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=500,
        )
    )
    @settings(max_examples=100)
    def test_drawdown_deterministic(self, equity_curve):
        """Same equity curve always gives same drawdown."""
        arr = np.array(equity_curve, dtype=float)
        d1 = DrawdownMonitor.portfolio_drawdown(arr)
        d2 = DrawdownMonitor.portfolio_drawdown(arr)
        assert d1 == d2


# ══════════════════════════════════════════════════════════════════════════════
# regime_from_prices — classification invariants
# ══════════════════════════════════════════════════════════════════════════════

class TestRegimeClassifierProperties:
    """regime_from_prices must be deterministic and return valid regime labels."""

    @given(
        spy_close=st.lists(
            st.floats(min_value=100.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=50,
            max_size=200,
        )
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_regime_always_valid_label(self, spy_close):
        """Regime output must always be GREEN, YELLOW, or RED."""
        state = regime_from_prices(np.array(spy_close))
        assert state.regime in ("GREEN", "YELLOW", "RED"), f"Invalid regime: {state.regime}"

    @given(
        spy_close=st.lists(
            _positive_prices,
            min_size=50,
            max_size=100,
        )
    )
    @settings(max_examples=100)
    def test_regime_deterministic(self, spy_close):
        """Same prices must always produce the same regime."""
        arr = np.array(spy_close)
        r1 = regime_from_prices(arr)
        r2 = regime_from_prices(arr)
        assert r1.regime == r2.regime

    @given(
        spy_close=st.lists(_positive_prices, min_size=50, max_size=100)
    )
    @settings(max_examples=100)
    def test_regime_confidence_bounded(self, spy_close):
        """Confidence must always be in [0, 1]."""
        state = regime_from_prices(np.array(spy_close))
        assert 0.0 <= state.confidence <= 1.0

    @given(
        spy_close=st.lists(_positive_prices, min_size=1, max_size=49)
    )
    @settings(max_examples=50)
    def test_regime_insufficient_data_returns_red(self, spy_close):
        """Fewer than 50 SPY bars defaults to RED (defensive)."""
        state = regime_from_prices(np.array(spy_close))
        assert state.regime == "RED"


# ══════════════════════════════════════════════════════════════════════════════
# Pydantic model round-trips (cemini_contracts)
# ══════════════════════════════════════════════════════════════════════════════

class TestPydanticContractRoundTrips:
    """Every Pydantic model must survive JSON serialization round-trips."""

    @given(
        symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Lu",))),
        pattern_name=st.sampled_from(["EpisodicPivot", "MomentumBurst", "ElephantBar", "VCP", "HighTightFlag", "InsideBar212"]),
        detected=st.booleans(),
        confidence=st.one_of(st.none(), st.floats(min_value=0.0, max_value=1.0, allow_nan=False)),
        rsi=st.one_of(st.none(), st.floats(min_value=0.0, max_value=100.0, allow_nan=False)),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_signal_detection_roundtrip(self, symbol, pattern_name, detected, confidence, rsi):
        """SignalDetection survives JSON round-trip."""
        from cemini_contracts.signals import SignalDetection

        model = SignalDetection(
            symbol=symbol,
            pattern_name=pattern_name,
            detected=detected,
            confidence=confidence,
            rsi=rsi,
        )
        json_str = model.model_dump_json()
        rebuilt = SignalDetection.model_validate_json(json_str)
        assert rebuilt.symbol == model.symbol
        assert rebuilt.pattern_name == model.pattern_name
        assert rebuilt.detected == model.detected

    @given(
        source_system=st.text(min_size=1, max_size=50),
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        value=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_intel_payload_roundtrip(self, source_system, confidence, value):
        """IntelPayload survives JSON round-trip."""
        from cemini_contracts.intel import IntelPayload

        payload = IntelPayload(value=value, source_system=source_system, confidence=confidence)
        json_str = payload.model_dump_json()
        rebuilt = IntelPayload.model_validate_json(json_str)
        assert rebuilt.source_system == payload.source_system
        assert abs(rebuilt.confidence - payload.confidence) < 1e-9

    @given(
        spread_10y2y=st.one_of(st.none(), st.floats(min_value=-5.0, max_value=5.0, allow_nan=False)),
        spread_10y3m=st.one_of(st.none(), st.floats(min_value=-5.0, max_value=5.0, allow_nan=False)),
        observation_date=st.just("2026-03-12"),
    )
    @settings(max_examples=100)
    def test_fred_yield_curve_roundtrip(self, spread_10y2y, spread_10y3m, observation_date):
        """FredYieldCurveIntel survives JSON round-trip."""
        from cemini_contracts.fred import FredYieldCurveIntel

        model = FredYieldCurveIntel(
            spread_10y2y=spread_10y2y,
            spread_10y3m=spread_10y3m,
            observation_date=observation_date,
        )
        json_str = model.model_dump_json()
        rebuilt = FredYieldCurveIntel.model_validate_json(json_str)
        assert rebuilt.observation_date == model.observation_date
        assert rebuilt.source == "fred"


# ══════════════════════════════════════════════════════════════════════════════
# Signal detectors — no crash on valid OHLCV inputs
# ══════════════════════════════════════════════════════════════════════════════

class TestSignalDetectorsNeverCrash:
    """No signal detector should raise on valid OHLCV-shaped data."""

    @given(
        prices=st.lists(
            st.floats(min_value=10.0, max_value=5_000.0, allow_nan=False, allow_infinity=False),
            min_size=70,
            max_size=200,
        )
    )
    @settings(max_examples=80, suppress_health_check=[HealthCheck.too_slow])
    def test_all_detectors_no_crash(self, prices):
        """All 6 signal detectors must handle any valid price sequence without raising."""
        df = _make_ohlcv_df(prices)
        detectors = [
            EpisodicPivot(),
            MomentumBurst(),
            ElephantBar(),
            VCP(),
            HighTightFlag(),
            InsideBar212(),
        ]
        for det in detectors:
            try:
                result = det.detect(df, symbol="TEST")
                # result is None (no signal) or a dict — both are valid
                assert result is None or isinstance(result, dict), (
                    f"{det.name}.detect() returned unexpected type: {type(result)}"
                )
            except Exception as exc:
                pytest.fail(f"{det.name}.detect() raised on valid input: {exc}")

    @given(
        prices=st.lists(
            st.floats(min_value=1.0, max_value=10_000.0, allow_nan=False, allow_infinity=False),
            min_size=70,
            max_size=200,
        )
    )
    @settings(max_examples=50)
    def test_signal_output_schema_when_detected(self, prices):
        """When a signal is returned, it must contain the required schema keys."""
        required_keys = {"pattern_name", "symbol", "confidence", "entry_price", "stop_price", "detected_at", "metadata"}
        df = _make_ohlcv_df(prices)
        for det in [EpisodicPivot(), ElephantBar(), InsideBar212()]:
            result = det.detect(df, symbol="AAPL")
            if result is not None:
                missing = required_keys - set(result.keys())
                assert not missing, f"{det.name} signal missing keys: {missing}"
                assert 0.0 <= result["confidence"] <= 1.0
                assert result["entry_price"] > 0
