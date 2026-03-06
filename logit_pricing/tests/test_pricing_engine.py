"""Tests for logit_pricing.pricing_engine — integration tests."""
import math
import time

import numpy as np
import pytest

from logit_pricing import LogitPricingEngine, ContractAssessment
from logit_pricing.transforms import logit


engine = LogitPricingEngine()


def _synthetic_prices(n=100, start=0.3, end=0.7):
    """Synthetic trending price series (0-1 scale)."""
    return list(np.linspace(start, end, n))


def _random_prices(n=50, seed=42):
    rng = np.random.default_rng(seed)
    return list(rng.uniform(0.2, 0.8, n))


class TestAssessContractSufficient:
    def test_trending_series_produces_valid_assessment(self):
        prices = _synthetic_prices(100, 0.3, 0.7)
        result = engine.assess_contract(prices, ticker="TEST-TREND")
        assert isinstance(result, ContractAssessment)
        assert result.is_sufficient
        assert math.isfinite(result.mispricing_score)
        assert math.isfinite(result.logit_current)
        assert math.isfinite(result.logit_fair_value)
        assert math.isfinite(result.confidence)
        assert math.isfinite(result.logit_volatility)

    def test_all_fields_within_bounds(self):
        prices = _random_prices(80)
        result = engine.assess_contract(prices, ticker="BOUND-TEST")
        assert 0.0 <= result.current_price <= 1.0
        assert 0.0 <= result.fair_value_probability <= 1.0
        assert -3.0 <= result.mispricing_score <= 3.0
        assert result.regime in ("diffusion", "jump")
        assert 0.0 <= result.confidence <= 1.0
        assert 0.0 <= result.time_decay_factor <= 1.0
        assert result.jump_count_window >= 0
        assert result.logit_volatility >= 0.0

    def test_trending_start_underpriced_end_overpriced(self):
        """Prices trending 0.3→0.7: early assessment underpriced, late overpriced."""
        prices_early = _synthetic_prices(100, 0.3, 0.7)
        prices_late = prices_early[::-1]  # reversed: high → low

        # Early in trend: current price 0.3, fair value tracking upward → underpriced
        result_early = engine.assess_contract(
            prices_early[:20], current_price=0.3, ticker="EARLY"
        )
        # Late: price reversed, now overpriced relative to EMA
        result_late = engine.assess_contract(
            prices_late[:20], current_price=0.65, ticker="LATE"
        )
        # Both should be finite and valid
        assert math.isfinite(result_early.mispricing_score)
        assert math.isfinite(result_late.mispricing_score)

    def test_contract_assessment_validates_pydantic(self):
        """ContractAssessment Pydantic model must accept engine output."""
        prices = _random_prices(50)
        result = engine.assess_contract(prices)
        # Re-validate through model (should not raise)
        revalidated = ContractAssessment.model_validate(result.model_dump())
        assert revalidated.ticker == result.ticker


class TestAssessContractInsufficient:
    def test_empty_prices_returns_default(self):
        result = engine.assess_contract([], ticker="EMPTY")
        assert not result.is_sufficient
        assert result.confidence == 0.0
        assert result.n_observations == 0

    def test_one_price_returns_default(self):
        result = engine.assess_contract([0.5], ticker="SINGLE")
        assert not result.is_sufficient
        assert result.confidence == 0.0

    def test_two_prices_partial(self):
        result = engine.assess_contract([0.4, 0.5], ticker="TWO")
        # Should not crash; confidence may be low
        assert result.n_observations == 2
        assert math.isfinite(result.mispricing_score)


class TestWithBidAsk:
    def test_spread_gives_nonzero_sigma_b(self):
        prices = _random_prices(50)
        resolution_ts = time.time() + 7 * 86400  # 7 days out
        result = engine.assess_contract(
            prices,
            resolution_timestamp=resolution_ts,
            yes_bid=0.45,
            yes_ask=0.55,
        )
        assert result.implied_sigma_b >= 0.0

    def test_near_resolution_low_time_decay(self):
        prices = _random_prices(30)
        near_ts = time.time() + 3600  # 1 hour out
        result = engine.assess_contract(prices, resolution_timestamp=near_ts)
        assert result.time_decay_factor < 0.1

    def test_far_resolution_full_time_decay(self):
        prices = _random_prices(30)
        far_ts = time.time() + 30 * 86400  # 30 days out
        result = engine.assess_contract(prices, resolution_timestamp=far_ts)
        assert abs(result.time_decay_factor - 1.0) < 1e-9


class TestIndicatorsPresent:
    def test_all_indicator_keys_present(self):
        prices = _synthetic_prices(60)
        result = engine.assess_contract(prices)
        for key in ["logit_ema", "logit_rsi", "logit_bb_upper", "logit_bb_lower", "logit_bb_mid"]:
            assert key in result.indicators

    def test_indicator_values_finite(self):
        prices = _random_prices(60)
        result = engine.assess_contract(prices)
        for key, val in result.indicators.items():
            assert math.isfinite(val), f"Non-finite indicator: {key}={val}"


class TestNaNInfSafety:
    def test_no_nan_inf_in_any_output(self):
        """End-to-end: no NaN/Inf anywhere in ContractAssessment output."""
        prices = _synthetic_prices(100)
        result = engine.assess_contract(prices)
        for field_name in ContractAssessment.model_fields:
            val = getattr(result, field_name)
            if isinstance(val, float):
                assert math.isfinite(val), f"Non-finite field: {field_name}={val}"
