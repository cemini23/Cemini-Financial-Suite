"""
Tests for options_greeks/ package (Step 23 — Options Greeks Engine).

All tests are pure math — no network, no Redis, no Postgres.
All inputs and expected values are deterministic.

Reference values validated against known Black-Scholes closed-form solutions.
"""
from __future__ import annotations

import math
from typing import Literal

import pytest

from options_greeks.black_scholes import (
    bs_price,
    delta,
    gamma,
    greeks,
    norm_cdf,
    norm_pdf,
    rho,
    theta,
    vega,
)
from options_greeks.binary_greeks import (
    binary_delta,
    binary_gamma,
    binary_greeks,
    binary_price,
    binary_theta,
    binary_vega,
)
from options_greeks.implied_vol import implied_volatility
from options_greeks.realized_vol import (
    approx_iv,
    parkinson_vol,
    realized_vol,
    realized_vol_ewm,
    rolling_beta,
    vol_regime,
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

_ATM = dict(S=100.0, K=100.0, T=1.0, r=0.05, sigma=0.20)


# ---------------------------------------------------------------------------
# norm_cdf / norm_pdf sanity
# ---------------------------------------------------------------------------


class TestMathHelpers:
    def test_norm_cdf_at_zero(self):
        assert norm_cdf(0.0) == pytest.approx(0.5, abs=1e-10)

    def test_norm_cdf_extreme_positive(self):
        assert norm_cdf(8.0) == pytest.approx(1.0, abs=1e-6)

    def test_norm_cdf_extreme_negative(self):
        assert norm_cdf(-8.0) == pytest.approx(0.0, abs=1e-6)

    def test_norm_pdf_at_zero(self):
        assert norm_pdf(0.0) == pytest.approx(1.0 / math.sqrt(2 * math.pi), rel=1e-10)

    def test_norm_pdf_symmetric(self):
        assert norm_pdf(1.5) == pytest.approx(norm_pdf(-1.5), rel=1e-10)

    def test_norm_pdf_positive_everywhere(self):
        for x in [-3, -1, 0, 1, 3]:
            assert norm_pdf(x) > 0


# ---------------------------------------------------------------------------
# Black-Scholes pricing — known values
# ---------------------------------------------------------------------------


class TestBSPrice:
    def test_atm_call_known_value(self):
        """S=100, K=100, T=1, r=0.05, sigma=0.20 → call ≈ 10.4506."""
        price = bs_price(**_ATM, option_type="call")
        assert price == pytest.approx(10.4506, abs=0.01)

    def test_atm_put_known_value(self):
        """Put ≈ call - S + K*e^(-rT) by put-call parity ≈ 5.5735."""
        price = bs_price(**_ATM, option_type="put")
        assert price == pytest.approx(5.5735, abs=0.02)

    def test_put_call_parity(self):
        """C - P = S - K * e^(-rT) must hold exactly."""
        S, K, T, r, sigma = 100.0, 100.0, 1.0, 0.05, 0.20
        call = bs_price(S, K, T, r, sigma, "call")
        put = bs_price(S, K, T, r, sigma, "put")
        assert call - put == pytest.approx(S - K * math.exp(-r * T), abs=1e-8)

    def test_put_call_parity_itm(self):
        S, K, T, r, sigma = 110.0, 100.0, 0.5, 0.03, 0.25
        call = bs_price(S, K, T, r, sigma, "call")
        put = bs_price(S, K, T, r, sigma, "put")
        assert call - put == pytest.approx(S - K * math.exp(-r * T), abs=1e-8)

    def test_price_non_negative(self):
        for otype in ("call", "put"):
            for s in [80, 100, 120]:
                p = bs_price(s, 100.0, 1.0, 0.05, 0.20, otype)
                assert p >= 0.0

    def test_deep_itm_call_approaches_intrinsic(self):
        """Deep ITM call (S>>K) should ≈ S - K * e^(-rT)."""
        p = bs_price(200.0, 100.0, 1.0, 0.05, 0.20, "call")
        intrinsic = 200.0 - 100.0 * math.exp(-0.05)
        assert p == pytest.approx(intrinsic, abs=0.5)

    def test_zero_vol_call_returns_intrinsic(self):
        """sigma → 0: call price → max(S - K*e^(-rT), 0)."""
        p = bs_price(100.0, 100.0, 1.0, 0.05, 1e-8, "call")
        expected = max(0.0, 100.0 - 100.0 * math.exp(-0.05))
        assert p == pytest.approx(expected, abs=0.01)

    def test_expiry_call_intrinsic(self):
        """T=0: call = max(S-K, 0)."""
        assert bs_price(110.0, 100.0, 0.0, 0.05, 0.20, "call") == pytest.approx(10.0, abs=1e-10)
        assert bs_price(90.0, 100.0, 0.0, 0.05, 0.20, "call") == pytest.approx(0.0, abs=1e-10)

    def test_expiry_put_intrinsic(self):
        """T=0: put = max(K-S, 0)."""
        assert bs_price(90.0, 100.0, 0.0, 0.05, 0.20, "put") == pytest.approx(10.0, abs=1e-10)
        assert bs_price(110.0, 100.0, 0.0, 0.05, 0.20, "put") == pytest.approx(0.0, abs=1e-10)

    def test_invalid_inputs_raise(self):
        with pytest.raises(ValueError):
            bs_price(-1.0, 100.0, 1.0, 0.05, 0.20)


# ---------------------------------------------------------------------------
# Greeks
# ---------------------------------------------------------------------------


class TestDelta:
    def test_call_delta_positive(self):
        d = delta(**_ATM, option_type="call")
        assert 0.0 < d < 1.0

    def test_put_delta_negative(self):
        d = delta(**_ATM, option_type="put")
        assert -1.0 < d < 0.0

    def test_call_put_delta_sum_equals_one(self):
        """call_delta - put_delta = 1 (from put-call parity)."""
        dc = delta(**_ATM, option_type="call")
        dp = delta(**_ATM, option_type="put")
        assert dc - dp == pytest.approx(1.0, abs=1e-10)

    def test_deep_itm_call_delta_approaches_one(self):
        d = delta(S=200.0, K=100.0, T=1.0, r=0.05, sigma=0.20, option_type="call")
        assert d == pytest.approx(1.0, abs=0.01)

    def test_deep_otm_call_delta_approaches_zero(self):
        d = delta(S=50.0, K=100.0, T=1.0, r=0.05, sigma=0.20, option_type="call")
        assert d == pytest.approx(0.0, abs=0.01)

    def test_atm_call_delta_near_half(self):
        """ATM call delta ≈ 0.5 to 0.6 depending on drift."""
        d = delta(**_ATM, option_type="call")
        assert 0.50 < d < 0.65


class TestGamma:
    def test_gamma_positive(self):
        """Gamma is always non-negative for long options."""
        g = gamma(**_ATM)
        assert g > 0.0

    def test_gamma_peaks_atm(self):
        """Gamma is higher ATM than deep ITM or deep OTM."""
        g_atm = gamma(**_ATM)
        g_itm = gamma(S=200.0, K=100.0, T=1.0, r=0.05, sigma=0.20)
        g_otm = gamma(S=50.0, K=100.0, T=1.0, r=0.05, sigma=0.20)
        assert g_atm > g_itm
        assert g_atm > g_otm


class TestTheta:
    def test_theta_negative_for_long_call(self):
        """Theta is always negative for long vanilla options (time decay)."""
        t = theta(**_ATM, option_type="call")
        assert t < 0.0

    def test_theta_negative_for_long_put(self):
        t = theta(**_ATM, option_type="put")
        assert t < 0.0

    def test_theta_per_day_small(self):
        """Theta should be a fraction of price per day (not per year)."""
        t = theta(**_ATM, option_type="call")
        price = bs_price(**_ATM, option_type="call")
        # Daily decay should be small relative to option price
        assert abs(t) < price * 0.05


class TestVega:
    def test_vega_positive(self):
        """Vega is always positive for long options."""
        v = vega(**_ATM)
        assert v > 0.0

    def test_vega_zero_at_expiry(self):
        v = vega(100.0, 100.0, 0.0, 0.05, 0.20)
        assert v == pytest.approx(0.0, abs=1e-10)


class TestRho:
    def test_call_rho_positive(self):
        """Higher r → higher call value → positive rho."""
        r_val = rho(**_ATM, option_type="call")
        assert r_val > 0.0

    def test_put_rho_negative(self):
        """Higher r → lower put value → negative rho."""
        r_val = rho(**_ATM, option_type="put")
        assert r_val < 0.0


class TestGreeksConvenience:
    def test_greeks_dict_has_all_keys(self):
        g = greeks(**_ATM)
        for key in ("price", "delta", "gamma", "theta", "vega", "rho", "option_type"):
            assert key in g

    def test_greeks_consistent_with_individual_functions(self):
        g = greeks(**_ATM)
        assert g["price"] == pytest.approx(bs_price(**_ATM), rel=1e-10)
        assert g["delta"] == pytest.approx(delta(**_ATM), rel=1e-10)
        assert g["gamma"] == pytest.approx(gamma(**_ATM), rel=1e-10)


# ---------------------------------------------------------------------------
# Implied Volatility
# ---------------------------------------------------------------------------


class TestImpliedVolatility:
    def test_round_trip_atm(self):
        """IV from a BS price should recover the original sigma."""
        sigma_true = 0.20
        price = bs_price(100.0, 100.0, 1.0, 0.05, sigma_true, "call")
        iv = implied_volatility(price, 100.0, 100.0, 1.0, 0.05, "call")
        assert iv == pytest.approx(sigma_true, abs=1e-4)

    def test_round_trip_high_vol(self):
        sigma_true = 0.60
        price = bs_price(100.0, 100.0, 0.5, 0.03, sigma_true, "call")
        iv = implied_volatility(price, 100.0, 100.0, 0.5, 0.03, "call")
        assert iv == pytest.approx(sigma_true, abs=1e-4)

    def test_round_trip_put(self):
        sigma_true = 0.30
        price = bs_price(95.0, 100.0, 0.25, 0.05, sigma_true, "put")
        iv = implied_volatility(price, 95.0, 100.0, 0.25, 0.05, "put")
        assert iv == pytest.approx(sigma_true, abs=1e-4)

    def test_sub_intrinsic_returns_nan(self):
        """Price below intrinsic has no valid IV → NaN."""
        iv = implied_volatility(0.01, 110.0, 100.0, 1.0, 0.05, "call")
        assert math.isnan(iv)

    def test_zero_time_returns_nan(self):
        iv = implied_volatility(5.0, 100.0, 100.0, 0.0, 0.05, "call")
        assert math.isnan(iv)


# ---------------------------------------------------------------------------
# Binary Greeks
# ---------------------------------------------------------------------------


class TestBinaryPrice:
    def test_price_in_valid_range(self):
        """Binary price ∈ [0, e^(-rT)]."""
        disc = math.exp(-0.05)
        p = binary_price(100.0, 100.0, 1.0, 0.05, 0.20)
        assert 0.0 <= p <= disc + 1e-10

    def test_atm_binary_price(self):
        """ATM binary call (S=K, T=1, r=0, sigma>0) ≈ N(d2) = N(-sigma/2)."""
        p = binary_price(100.0, 100.0, 1.0, 0.0, 0.20)
        # d2 = -sigma/2 = -0.10; N(-0.10) ≈ 0.4602
        expected = norm_cdf(-0.10)
        assert p == pytest.approx(expected, abs=1e-4)

    def test_deep_itm_binary_approaches_disc(self):
        """Deep ITM (S >> K): binary price → e^(-rT)."""
        p = binary_price(500.0, 100.0, 1.0, 0.05, 0.20)
        assert p == pytest.approx(math.exp(-0.05), abs=0.01)

    def test_deep_otm_binary_approaches_zero(self):
        p = binary_price(10.0, 100.0, 1.0, 0.05, 0.20)
        assert p == pytest.approx(0.0, abs=0.01)

    def test_expiry_itm(self):
        assert binary_price(110.0, 100.0, 0.0, 0.05, 0.20) == pytest.approx(1.0)

    def test_expiry_otm(self):
        assert binary_price(90.0, 100.0, 0.0, 0.05, 0.20) == pytest.approx(0.0)


class TestBinaryDelta:
    def test_delta_positive(self):
        """Binary call delta is always positive."""
        d = binary_delta(100.0, 100.0, 1.0, 0.05, 0.20)
        assert d > 0.0

    def test_delta_consistency_with_price(self):
        """Finite-difference check: delta ≈ ΔV/ΔS."""
        S, K, T, r, sig = 100.0, 100.0, 1.0, 0.05, 0.20
        eps = 0.001
        fd_delta = (binary_price(S + eps, K, T, r, sig) - binary_price(S - eps, K, T, r, sig)) / (2 * eps)
        analytical = binary_delta(S, K, T, r, sig)
        assert analytical == pytest.approx(fd_delta, rel=1e-3)


class TestBinaryGreeksDict:
    def test_all_keys_present(self):
        g = binary_greeks(100.0, 100.0, 1.0, 0.05, 0.20)
        for key in ("price", "delta", "gamma", "theta", "vega"):
            assert key in g


# ---------------------------------------------------------------------------
# Realized Volatility
# ---------------------------------------------------------------------------


class TestRealizedVol:
    def test_constant_returns_zero_vol(self):
        """Constant price → zero log returns → zero vol."""
        closes = [100.0] * 30
        rv = realized_vol(closes)
        assert rv == pytest.approx(0.0, abs=1e-10)

    def test_known_vol_from_daily_returns(self):
        """Daily returns of exactly 1% → realized vol ≈ 0.01 × sqrt(252)."""
        closes = [100.0 * (1.01 ** i) for i in range(30)]
        rv = realized_vol(closes)
        expected = 0.0  # constant 1% returns → zero stdev (all same)
        # Actually constant returns → stdev = 0
        assert rv == pytest.approx(0.0, abs=1e-8)

    def test_known_vol_with_variation(self):
        """Manually computed: alternating +1% / -1% gives known vol."""
        import math as _math
        # Alternating returns: log(1.01) and log(0.99) alternating
        base_closes = [100.0]
        for i in range(30):
            if i % 2 == 0:
                base_closes.append(base_closes[-1] * 1.01)
            else:
                base_closes.append(base_closes[-1] * 0.99)
        rv = realized_vol(base_closes)
        assert rv > 0.0  # must be positive
        assert 0.05 < rv < 0.25  # ~10-15% annualised for 1% daily swings

    def test_two_prices_gives_single_return(self):
        rv = realized_vol([100.0, 101.0])
        assert math.isnan(rv)  # stdev requires at least 2 returns (3 prices)

    def test_single_price_returns_nan(self):
        rv = realized_vol([100.0])
        assert math.isnan(rv)

    def test_ewm_vol_non_negative(self):
        closes = [100.0 + i * 0.5 + (i % 3 - 1) * 2 for i in range(50)]
        rv = realized_vol_ewm(closes)
        assert rv >= 0.0 or math.isnan(rv)


class TestParkinsonVol:
    def test_non_negative(self):
        highs = [101.0 + i * 0.1 for i in range(25)]
        lows = [99.0 + i * 0.1 for i in range(25)]
        pv = parkinson_vol(highs, lows)
        assert pv >= 0.0

    def test_wider_range_higher_vol(self):
        """Wider daily H-L range → higher Parkinson vol."""
        highs_narrow = [102.0] * 25
        lows_narrow = [99.0] * 25
        highs_wide = [110.0] * 25
        lows_wide = [90.0] * 25
        pv_narrow = parkinson_vol(highs_narrow, lows_narrow)
        pv_wide = parkinson_vol(highs_wide, lows_wide)
        assert pv_wide > pv_narrow

    def test_zero_range_returns_zero(self):
        """H = L → zero range → zero vol."""
        highs = lows = [100.0] * 25
        pv = parkinson_vol(highs, lows)
        assert pv == pytest.approx(0.0, abs=1e-10)

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            parkinson_vol([100.0, 101.0], [99.0])

    def test_insufficient_data(self):
        pv = parkinson_vol([102.0], [99.0])
        assert math.isnan(pv)


class TestVolRegime:
    def test_high_vol_classified_high(self):
        lookback = [0.10, 0.12, 0.11, 0.13, 0.10, 0.12, 0.11, 0.10]
        assert vol_regime(0.30, lookback) == "HIGH"

    def test_low_vol_classified_low(self):
        lookback = [0.20, 0.25, 0.22, 0.23, 0.24, 0.21, 0.20, 0.22]
        assert vol_regime(0.05, lookback) == "LOW"

    def test_median_vol_classified_normal(self):
        lookback = [0.10, 0.20, 0.30, 0.15, 0.25, 0.12, 0.22, 0.18]
        result = vol_regime(0.18, lookback)
        assert result == "NORMAL"

    def test_empty_lookback_returns_normal(self):
        assert vol_regime(0.20, []) == "NORMAL"


class TestRollingBeta:
    def _varying_spy(self) -> list[float]:
        """Generate 65 SPY closes with non-zero variance (alternating pattern)."""
        closes = [100.0]
        for i in range(64):
            mult = 1.01 if i % 3 != 0 else 0.98
            closes.append(closes[-1] * mult)
        return closes

    def test_spy_vs_spy_beta_is_one(self):
        """A series regressed against itself has beta = 1."""
        spy = self._varying_spy()
        beta = rolling_beta(spy, spy)
        assert beta == pytest.approx(1.0, abs=1e-8)

    def test_double_return_beta_is_two(self):
        """Stock with exactly 2× each SPY log return → beta ≈ 2."""
        import math as _math
        spy = self._varying_spy()
        # Build stock whose log returns are exactly 2× spy log returns
        spy_log_rets = [_math.log(spy[i] / spy[i - 1]) for i in range(1, len(spy))]
        stock = [100.0]
        for lr in spy_log_rets:
            stock.append(stock[-1] * _math.exp(2.0 * lr))
        beta = rolling_beta(stock, spy)
        assert beta == pytest.approx(2.0, rel=1e-6)

    def test_insufficient_data_returns_nan(self):
        beta = rolling_beta([100.0, 101.0], [100.0, 101.0])
        assert math.isnan(beta)

    def test_mismatched_lengths_returns_nan(self):
        beta = rolling_beta([100.0] * 30, [100.0] * 20)
        assert math.isnan(beta)


class TestApproxIV:
    def test_spy_beta_one_approx_iv(self):
        """Beta=1 stock → approx_iv ≈ VIX / 100."""
        iv = approx_iv(vix=20.0, beta=1.0)
        assert iv == pytest.approx(0.20, rel=1e-10)

    def test_high_beta_scales_iv(self):
        iv = approx_iv(vix=20.0, beta=1.5)
        assert iv == pytest.approx(0.30, rel=1e-10)

    def test_negative_beta_uses_abs(self):
        iv_neg = approx_iv(vix=20.0, beta=-0.5)
        iv_pos = approx_iv(vix=20.0, beta=0.5)
        assert iv_neg == pytest.approx(iv_pos, rel=1e-10)

    def test_zero_vix_returns_nan(self):
        assert math.isnan(approx_iv(vix=0.0, beta=1.0))


# ---------------------------------------------------------------------------
# Pydantic contracts
# ---------------------------------------------------------------------------


class TestOptionsPydanticModels:
    def test_option_greeks_model(self):
        from cemini_contracts.options import OptionGreeks
        g = OptionGreeks(price=10.45, delta=0.60, gamma=0.018, theta=-0.028, vega=0.38, rho=0.45, option_type="call")
        assert g.delta == pytest.approx(0.60)
        assert g.option_type == "call"

    def test_binary_greeks_model(self):
        from cemini_contracts.options import BinaryGreeks
        bg = BinaryGreeks(price=0.48, delta=0.025, gamma=-0.0003, theta=-0.0012, vega=-0.008)
        assert bg.price == pytest.approx(0.48)

    def test_vol_surface_entry_model(self):
        from cemini_contracts.options import VolSurfaceEntry
        entry = VolSurfaceEntry(symbol="AAPL", realized_vol_21d=0.25, parkinson_vol_21d=0.23, vol_regime="NORMAL", approx_iv=0.27, beta_to_spy=1.15)
        assert entry.vol_regime == "NORMAL"

    def test_vol_surface_intel_model(self):
        from cemini_contracts.options import VolSurfaceIntel, VolSurfaceEntry
        from datetime import datetime, timezone
        intel = VolSurfaceIntel(
            timestamp=datetime.now(timezone.utc),
            vix=20.0,
            symbols={"SPY": VolSurfaceEntry(symbol="SPY", vol_regime="NORMAL")},
            market_vol_regime="NORMAL",
            high_vol_symbols=[],
            low_vol_symbols=[],
            total_tracked=1,
        )
        assert intel.total_tracked == 1
        assert "SPY" in intel.symbols
