"""Tests for logit_pricing.precision — financial math safety layer."""
import math
from decimal import Decimal

import numpy as np
import pytest

from logit_pricing.precision import (
    assert_finite, safe_divide, multiply_before_divide,
    clamp_probability, sanitize_array, is_finite_float,
)
from logit_pricing.transforms import P_MIN, P_MAX


class TestAssertFinite:
    def test_nan_raises(self):
        with pytest.raises(ValueError):
            assert_finite(float("nan"), "test_nan")

    def test_inf_raises(self):
        with pytest.raises(ValueError):
            assert_finite(float("inf"), "test_inf")

    def test_neg_inf_raises(self):
        with pytest.raises(ValueError):
            assert_finite(float("-inf"), "test_neginf")

    def test_valid_float_ok(self):
        assert_finite(3.14, "pi")  # no exception

    def test_zero_ok(self):
        assert_finite(0.0, "zero")

    def test_decimal_nan_raises(self):
        with pytest.raises(ValueError):
            assert_finite(Decimal("NaN"), "dec_nan")


class TestSafeDivide:
    def test_zero_denominator_returns_default(self):
        result = safe_divide(5, 0)
        assert result == Decimal("0")

    def test_custom_default(self):
        result = safe_divide(5, 0, default=Decimal("-1"))
        assert result == Decimal("-1")

    def test_normal_division(self):
        result = safe_divide(10, 4)
        assert abs(float(result) - 2.5) < 1e-10

    def test_string_inputs(self):
        result = safe_divide("10", "3")
        assert abs(float(result) - 10 / 3) < 1e-6


class TestMultiplyBeforeDivide:
    def test_known_result(self):
        # (3 * 4) / 6 = 2.0
        result = multiply_before_divide(3, 4, 6)
        assert abs(float(result) - 2.0) < 1e-10

    def test_zero_denominator_returns_default(self):
        result = multiply_before_divide(3, 4, 0)
        assert result == Decimal("0")

    def test_precision_near_boundary(self):
        # Test that multiplication before division preserves precision
        a, b, c = 1e-9, 1e-9, 1e-18
        result = multiply_before_divide(a, b, c)
        # (a*b)/c should be ~1.0
        assert abs(float(result) - 1.0) < 1e-6


class TestClampProbability:
    def test_below_min(self):
        assert clamp_probability(-0.1) == P_MIN

    def test_above_max(self):
        assert clamp_probability(1.5) == P_MAX

    def test_nan_returns_midpoint(self):
        result = clamp_probability(float("nan"))
        assert 0.0 < result < 1.0

    def test_inf_returns_midpoint(self):
        result = clamp_probability(float("inf"))
        assert 0.0 < result < 1.0

    def test_valid_passthrough(self):
        assert abs(clamp_probability(0.5) - 0.5) < 1e-10


class TestSanitizeArray:
    def test_no_invalids_unchanged(self):
        arr = np.array([1.0, 2.0, 3.0])
        result, n = sanitize_array(arr)
        assert n == 0
        np.testing.assert_array_equal(result, arr)

    def test_nan_replaced(self):
        arr = np.array([1.0, float("nan"), 3.0])
        result, n = sanitize_array(arr, fill=-99.0)
        assert n == 1
        assert result[1] == -99.0

    def test_inf_replaced(self):
        arr = np.array([float("inf"), 2.0])
        result, n = sanitize_array(arr, fill=0.0)
        assert n == 1
        assert result[0] == 0.0


class TestIsFiniteFloat:
    def test_valid(self):
        assert is_finite_float(3.14)

    def test_nan(self):
        assert not is_finite_float(float("nan"))

    def test_inf(self):
        assert not is_finite_float(float("inf"))

    def test_non_numeric(self):
        assert not is_finite_float("hello")
