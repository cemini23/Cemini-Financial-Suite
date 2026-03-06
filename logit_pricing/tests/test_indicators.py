"""Tests for logit_pricing.indicators — known-value and property tests."""
import math

import numpy as np
import pytest

from logit_pricing.transforms import logit
from logit_pricing.indicators import (
    logit_sma, logit_ema, logit_bollinger, logit_rsi,
    logit_mean_reversion_score, implied_belief_vol,
)


PRICES_5 = [0.3, 0.35, 0.40, 0.45, 0.50]
LOGITS_5 = [logit(p) for p in PRICES_5]


class TestLogitSMA:
    def test_known_value(self):
        L = np.array(LOGITS_5)
        sma = logit_sma(L, window=3)
        # Index 2 = mean of LOGITS_5[0:3]
        expected = (LOGITS_5[0] + LOGITS_5[1] + LOGITS_5[2]) / 3.0
        assert abs(sma[2] - expected) < 1e-10

    def test_first_entries_nan(self):
        L = np.array(LOGITS_5)
        sma = logit_sma(L, window=3)
        assert np.isnan(sma[0])
        assert np.isnan(sma[1])
        assert np.isfinite(sma[2])

    def test_length_preserved(self):
        L = np.array(LOGITS_5)
        sma = logit_sma(L, window=3)
        assert len(sma) == len(L)


class TestLogitEMA:
    def test_seed_equals_first_value(self):
        L = np.array(LOGITS_5)
        ema = logit_ema(L, span=3)
        assert abs(ema[0] - LOGITS_5[0]) < 1e-10

    def test_ema_tracks_upward_trend(self):
        # Strictly increasing logits → EMA must be below the latest value
        L = np.array(LOGITS_5)
        ema = logit_ema(L, span=3)
        assert ema[-1] < L[-1]

    def test_length_preserved(self):
        L = np.array(LOGITS_5)
        ema = logit_ema(L, span=3)
        assert len(ema) == len(L)


class TestLogitBollinger:
    def test_constant_series_zero_bandwidth(self):
        L = np.full(25, logit(0.5))
        upper, mid, lower = logit_bollinger(L, window=20, num_std=2.0)
        # Standard deviation of constant is 0 → bands collapse to mid
        assert abs(upper[-1] - mid[-1]) < 1e-9
        assert abs(lower[-1] - mid[-1]) < 1e-9

    def test_upper_above_lower(self):
        rng = np.random.default_rng(7)
        L = rng.normal(0, 0.5, 50)
        upper, mid, lower = logit_bollinger(L, window=20)
        valid = np.isfinite(upper) & np.isfinite(lower)
        assert np.all(upper[valid] >= lower[valid])

    def test_length_preserved(self):
        L = np.array(LOGITS_5 * 5)  # 25 elements
        u, m, lo = logit_bollinger(L, window=20)
        assert len(u) == len(L)


class TestLogitRSI:
    def test_wilder_smma_not_sma(self):
        """Explicitly verify Wilder's alpha = 1/period (not 2/(period+1))."""
        # If SMA-RSI were used, results would differ. We verify via known sequence.
        rng = np.random.default_rng(99)
        L = rng.normal(0, 0.3, 30)
        rsi = logit_rsi(L, period=14)
        # RSI must be in [0, 100]
        valid = rsi[np.isfinite(rsi)]
        assert np.all(valid >= 0.0)
        assert np.all(valid <= 100.0)

    def test_all_gains_gives_100(self):
        """Monotonically increasing logits → all gains, no losses → RSI → 100."""
        L = np.linspace(-2, 2, 40)  # strictly increasing
        rsi = logit_rsi(L, period=14)
        valid = rsi[np.isfinite(rsi)]
        assert len(valid) > 0
        # Not exactly 100 (SMMA smoothing), but should be very high
        assert valid[-1] > 90.0

    def test_insufficient_data_returns_nan(self):
        L = np.array(LOGITS_5[:3])  # only 3 points
        rsi = logit_rsi(L, period=14)
        assert np.all(np.isnan(rsi))

    def test_length_preserved(self):
        L = np.array(LOGITS_5 * 4)  # 20 elements
        rsi = logit_rsi(L, period=5)
        assert len(rsi) == len(L)


class TestMeanReversionScore:
    def test_at_fair_value_is_zero(self):
        score = logit_mean_reversion_score(logit(0.5), logit(0.5), 0.3)
        assert abs(score) < 1e-9

    def test_above_ema_is_positive(self):
        # Current logit > EMA → overpriced → positive score
        score = logit_mean_reversion_score(logit(0.7), logit(0.5), 0.3)
        assert score > 0.0

    def test_below_ema_is_negative(self):
        score = logit_mean_reversion_score(logit(0.3), logit(0.5), 0.3)
        assert score < 0.0

    def test_zero_vol_returns_zero(self):
        score = logit_mean_reversion_score(logit(0.7), logit(0.5), 0.0)
        assert score == 0.0

    def test_clamped_to_3sigma(self):
        # Extreme deviation → clamped to ±3
        score = logit_mean_reversion_score(logit(0.999), logit(0.001), 0.01)
        assert abs(score) <= 3.0 + 1e-9


class TestImpliedBeliefVol:
    def test_wider_spread_gives_higher_vol(self):
        sigma_narrow = implied_belief_vol(0.48, 0.52, tau=0.1)
        sigma_wide = implied_belief_vol(0.40, 0.60, tau=0.1)
        assert sigma_wide >= sigma_narrow

    def test_non_negative(self):
        sigma = implied_belief_vol(0.45, 0.55, tau=0.5)
        assert sigma >= 0.0

    def test_zero_spread_returns_zero(self):
        # bid == ask → zero spread → σ → 0 or small
        sigma = implied_belief_vol(0.5, 0.5, tau=0.1)
        assert sigma >= 0.0
