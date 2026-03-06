"""Tests for logit_pricing.transforms — property-based and boundary checks."""
import math

import numpy as np
import pytest

from logit_pricing.transforms import (
    logit, inv_logit, logit_array, inv_logit_array,
    logit_decimal, logit_mid, logit_spread,
    P_MIN, P_MAX, LOGIT_MIN, LOGIT_MAX,
)


class TestLogitScalar:
    def test_midpoint_is_zero(self):
        assert abs(logit(0.5)) < 1e-10

    def test_symmetry(self):
        for p in [0.1, 0.2, 0.35, 0.7, 0.9]:
            assert abs(logit(p) + logit(1.0 - p)) < 1e-10

    def test_roundtrip(self):
        for p in [0.001, 0.01, 0.1, 0.3, 0.5, 0.7, 0.9, 0.99, 0.999]:
            assert abs(inv_logit(logit(p)) - p) < 1e-10

    def test_clamps_zero(self):
        # logit(0) must not return -inf — returns logit(P_MIN)
        result = logit(0.0)
        assert math.isfinite(result)
        assert abs(result - LOGIT_MIN) < 1e-9

    def test_clamps_one(self):
        result = logit(1.0)
        assert math.isfinite(result)
        assert abs(result - LOGIT_MAX) < 1e-9

    def test_monotone(self):
        ps = [0.1, 0.3, 0.5, 0.7, 0.9]
        logits = [logit(p) for p in ps]
        for idx in range(len(logits) - 1):
            assert logits[idx] < logits[idx + 1]

    def test_inv_logit_large_positive(self):
        # Very large positive L → P_MAX (not >1 or inf)
        result = inv_logit(1000.0)
        assert result == P_MAX

    def test_inv_logit_large_negative(self):
        result = inv_logit(-1000.0)
        assert result == P_MIN


class TestLogitDecimal:
    def test_midpoint(self):
        from decimal import Decimal
        result = logit_decimal(0.5)
        assert abs(float(result)) < 1e-9

    def test_roundtrip_boundary(self):
        """Decimal should give tighter round-trip error near boundaries."""
        from logit_pricing.transforms import inv_logit_decimal
        from decimal import Decimal

        for p in [0.001, 0.002, 0.998, 0.999]:
            L = logit_decimal(p)
            p_back = float(inv_logit_decimal(L))
            assert abs(p_back - p) < 1e-9


class TestLogitArray:
    def test_matches_scalar(self):
        """logit_array should match element-wise logit() for 1000 random values."""
        rng = np.random.default_rng(42)
        ps = rng.uniform(P_MIN, P_MAX, 1000)
        arr_result, mask = logit_array(ps)
        scalar_result = np.array([logit(p) for p in ps])
        assert not mask.any(), "No invalid values expected in [P_MIN, P_MAX]"
        np.testing.assert_allclose(arr_result, scalar_result, rtol=1e-10)

    def test_no_nan_inf_in_valid_range(self):
        ps = np.linspace(P_MIN, P_MAX, 500)
        logits, mask = logit_array(ps)
        assert not mask.any()
        assert np.all(np.isfinite(logits))

    def test_out_of_range_clamped(self):
        ps = np.array([0.0, 0.0005, 0.9995, 1.0])
        logits, mask = logit_array(ps)
        # Should be finite after clamping — no inf
        assert np.all(np.isfinite(logits))

    def test_roundtrip_array(self):
        ps = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        logits, _ = logit_array(ps)
        ps_back = inv_logit_array(logits)
        np.testing.assert_allclose(ps_back, ps, atol=1e-10)


class TestLogitMidSpread:
    def test_spread_non_negative(self):
        # ask always >= bid in a valid orderbook
        result = logit_spread(0.45, 0.50)
        assert result >= 0.0

    def test_mid_between_bid_ask(self):
        mid = logit_mid(0.45, 0.55)
        assert logit(0.45) <= mid <= logit(0.55)
