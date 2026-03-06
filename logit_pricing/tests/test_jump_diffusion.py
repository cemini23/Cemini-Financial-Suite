"""Tests for logit_pricing.jump_diffusion — edge cases and regime classification."""
import math
import time

import numpy as np
import pytest

from logit_pricing.transforms import logit
from logit_pricing.jump_diffusion import (
    detect_jumps, classify_regime, time_decay_factor, fair_value_logit,
    JumpEvent,
)


def _smooth_series(n=30, start=0.3, end=0.7):
    """Smooth increasing price series — no jumps."""
    prices = np.linspace(start, end, n)
    return np.array([logit(p) for p in prices])


def _jump_series():
    """Series with a sudden spike: 0.3 → 0.8 (large jump)."""
    prices = [0.3] * 10 + [0.8] + [0.35] * 10
    return np.array([logit(p) for p in prices])


def _constant_series(n=20, p=0.5):
    return np.full(n, logit(p))


class TestDetectJumps:
    def test_smooth_series_no_jumps(self):
        L = _smooth_series(50)
        jumps = detect_jumps(L)
        assert len(jumps) == 0

    def test_constant_series_no_jumps(self):
        L = _constant_series(20)
        jumps = detect_jumps(L)
        assert len(jumps) == 0

    def test_spike_detected(self):
        L = _jump_series()
        jumps = detect_jumps(L)
        assert len(jumps) >= 1
        # Jump should be around index 10
        jump_indices = [j.index for j in jumps]
        assert any(8 <= idx <= 13 for idx in jump_indices)

    def test_jump_event_fields(self):
        L = _jump_series()
        jumps = detect_jumps(L)
        assert len(jumps) >= 1
        j = jumps[0]
        assert j.sigma_multiple >= 2.5   # at or above threshold
        assert math.isfinite(j.delta_logit)

    def test_too_short_returns_empty(self):
        jumps = detect_jumps(np.array([logit(0.5)]))
        assert jumps == []


class TestClassifyRegime:
    def test_smooth_is_diffusion(self):
        L = _smooth_series(50)
        jumps = detect_jumps(L)
        regime = classify_regime(L, jumps)
        assert regime.regime == "diffusion"

    def test_jump_series_is_jump_regime(self):
        # Test classify_regime directly with mocked JumpEvents at known indices.
        # This tests the classification logic independently of detect_jumps.
        # A real series may have consecutive jumps that inflate rolling sigma;
        # here we inject 4 jumps in the last 20 obs = 20% rate (> 15% threshold).
        L = np.zeros(25)  # 25 observations, window=20 → last 20 are indices 5..24
        jumps = [
            JumpEvent(index=10, timestamp=10.0, logit_before=0.0, logit_after=1.5, delta_logit=1.5, sigma_multiple=15.0),
            JumpEvent(index=14, timestamp=14.0, logit_before=0.0, logit_after=1.5, delta_logit=1.5, sigma_multiple=12.0),
            JumpEvent(index=18, timestamp=18.0, logit_before=0.0, logit_after=1.5, delta_logit=1.5, sigma_multiple=10.0),
            JumpEvent(index=22, timestamp=22.0, logit_before=0.0, logit_after=1.5, delta_logit=1.5, sigma_multiple=8.0),
        ]
        regime = classify_regime(L, jumps, window=20)
        assert regime.regime == "jump", f"Expected jump regime, got {regime}"

    def test_constant_is_diffusion(self):
        L = _constant_series(20)
        jumps = detect_jumps(L)
        regime = classify_regime(L, jumps)
        assert regime.regime == "diffusion"

    def test_n_obs_correct(self):
        L = _smooth_series(30)
        jumps = detect_jumps(L)
        regime = classify_regime(L, jumps)
        assert regime.n_obs == 30


class TestTimeDecayFactor:
    def test_far_future_is_one(self):
        future_ts = time.time() + 30 * 86400  # 30 days out
        factor = time_decay_factor(future_ts)
        assert abs(factor - 1.0) < 1e-9

    def test_past_is_zero(self):
        past_ts = time.time() - 3600
        factor = time_decay_factor(past_ts)
        assert factor == 0.0

    def test_none_is_one(self):
        assert time_decay_factor(None) == 1.0

    def test_near_resolution_discounted(self):
        near_ts = time.time() + 3600  # 1 hour out
        factor = time_decay_factor(near_ts)
        assert 0.0 < factor < 0.1   # near-zero since < 0.1/30 day

    def test_monotone(self):
        now = time.time()
        factors = [
            time_decay_factor(now + d * 86400)
            for d in [1, 5, 10, 20, 30]
        ]
        for idx in range(len(factors) - 1):
            assert factors[idx] <= factors[idx + 1]


class TestFairValueLogit:
    def test_returns_finite(self):
        L = _smooth_series(20)
        from logit_pricing.jump_diffusion import RegimeState
        regime = RegimeState("diffusion", 0, 0.0, 0.1, 20)
        fv, conf = fair_value_logit(L, regime)
        assert math.isfinite(fv)
        assert 0.0 <= conf <= 1.0

    def test_jump_regime_reduces_confidence(self):
        L = _smooth_series(30)
        from logit_pricing.jump_diffusion import RegimeState
        diffusion = RegimeState("diffusion", 0, 0.0, 0.1, 30)
        jump = RegimeState("jump", 5, 0.25, 0.5, 30)
        _, conf_diff = fair_value_logit(L, diffusion)
        _, conf_jump = fair_value_logit(L, jump)
        assert conf_jump < conf_diff

    def test_insufficient_data_low_confidence(self):
        L = np.array([logit(0.5)])
        from logit_pricing.jump_diffusion import RegimeState
        regime = RegimeState("diffusion", 0, 0.0, 0.0, 1)
        _, conf = fair_value_logit(L, regime)
        assert conf == 0.0
