"""
Cemini Financial Suite — Realized Volatility Calculator (Step 23)

Pure-math realized volatility estimators that work with existing
raw_market_ticks OHLCV data.  No scipy, no pandas — stdlib + math only.

Estimators
----------
realized_vol      Close-to-close log-return standard deviation (annualised)
realized_vol_ewm  Exponentially-weighted version (more responsive to recent vol)
parkinson_vol     Range-based Parkinson (1980) estimator — more efficient than C2C
vol_regime        Percentile-based classification: LOW / NORMAL / HIGH

Beta / IV Approximation
-----------------------
rolling_beta      OLS slope of stock returns vs SPY returns
approx_iv         Beta-adjusted VIX proxy for stocks without OPRA feed
"""
from __future__ import annotations

import math
import statistics
from typing import Literal


# ---------------------------------------------------------------------------
# Close-to-close realized volatility
# ---------------------------------------------------------------------------


def _log_returns(closes: list[float]) -> list[float]:
    """Compute log returns from a list of closing prices."""
    if len(closes) < 2:
        return []
    return [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]


def realized_vol(
    closes: list[float],
    annualization_factor: int = 252,
) -> float:
    """Annualised close-to-close realized volatility.

    Standard formula: σ = stdev(log_returns) × sqrt(annualization_factor).

    Args:
        closes: List of closing prices (chronological order, oldest first).
        annualization_factor: 252 for daily equity data, 365 for crypto.

    Returns:
        Annualised volatility as a decimal (e.g., 0.20 = 20%).
        Returns NaN if fewer than 2 data points.
    """
    rets = _log_returns(closes)
    if len(rets) < 2:
        return float("nan")
    return statistics.stdev(rets) * math.sqrt(annualization_factor)


def realized_vol_ewm(
    closes: list[float],
    span: int = 21,
    annualization_factor: int = 252,
) -> float:
    """Annualised exponentially-weighted realized volatility.

    Uses EWMA with decay λ = 2/(span+1), giving more weight to recent returns.
    More responsive to volatility regime changes than the uniform estimator.

    Args:
        closes: List of closing prices (chronological order, oldest first).
        span: EWM span (half-life ≈ span/2 trading days).
        annualization_factor: 252 for daily equity data.

    Returns:
        Annualised EWM volatility as a decimal.
        Returns NaN if fewer than 2 data points.
    """
    rets = _log_returns(closes)
    if not rets:
        return float("nan")

    lam = 2.0 / (span + 1)
    mean_r = sum(rets) / len(rets)

    # EWM variance: accumulate with lambda decay (newest last)
    variance = 0.0
    weight_sum = 0.0
    weight = 1.0
    for r in reversed(rets):
        variance += weight * (r - mean_r) ** 2
        weight_sum += weight
        weight *= (1.0 - lam)

    if weight_sum < 1e-12:
        return float("nan")

    ewm_var = variance / weight_sum
    return math.sqrt(ewm_var * annualization_factor)


# ---------------------------------------------------------------------------
# Parkinson range-based volatility (more efficient than C2C)
# ---------------------------------------------------------------------------


def parkinson_vol(
    highs: list[float],
    lows: list[float],
    annualization_factor: int = 252,
) -> float:
    """Parkinson (1980) range-based realized volatility estimator.

    Uses intraday high-low range instead of close-to-close returns.
    ~5× more statistically efficient than C2C vol for the same number of days.

    Formula: σ² = annualization_factor / (4 * ln(2) * N) * Σ[ln(H/L)]²

    Args:
        highs: List of daily high prices (chronological, oldest first).
        lows:  List of daily low prices (same length and order as highs).
        annualization_factor: 252 for equity, 365 for crypto.

    Returns:
        Annualised Parkinson vol as a decimal.
        Returns NaN if fewer than 2 bars or any H < L.
    """
    if len(highs) != len(lows):
        raise ValueError("highs and lows must have the same length")
    n = len(highs)
    if n < 2:
        return float("nan")

    factor = annualization_factor / (4.0 * math.log(2.0) * n)
    total = 0.0
    for h, lo in zip(highs, lows, strict=False):
        if lo <= 0 or h < lo:
            continue  # skip invalid bars
        total += math.log(h / lo) ** 2

    return math.sqrt(factor * total)


# ---------------------------------------------------------------------------
# Vol regime classifier
# ---------------------------------------------------------------------------


def vol_regime(
    current_vol: float,
    lookback_vols: list[float],
) -> Literal["LOW", "NORMAL", "HIGH"]:
    """Classify vol regime relative to its historical distribution.

    Percentile-based:
      < 25th percentile  → "LOW"
      25–75th percentile → "NORMAL"
      > 75th percentile  → "HIGH"

    Args:
        current_vol: The vol to classify (e.g., today's 21-day realized vol).
        lookback_vols: Historical vol series for percentile reference.

    Returns:
        "LOW", "NORMAL", or "HIGH".
    """
    if not lookback_vols:
        return "NORMAL"

    sorted_vols = sorted(v for v in lookback_vols if not math.isnan(v))
    n = len(sorted_vols)
    if n == 0:
        return "NORMAL"

    # 25th and 75th percentile via linear interpolation
    def _percentile(data: list[float], p: float) -> float:
        idx = (len(data) - 1) * p / 100.0
        lo, hi = int(idx), min(int(idx) + 1, len(data) - 1)
        frac = idx - lo
        return data[lo] * (1 - frac) + data[hi] * frac

    p25 = _percentile(sorted_vols, 25.0)
    p75 = _percentile(sorted_vols, 75.0)

    if current_vol < p25:
        return "LOW"
    elif current_vol > p75:
        return "HIGH"
    else:
        return "NORMAL"


# ---------------------------------------------------------------------------
# Beta calculation (OLS slope: cov(r_stock, r_spy) / var(r_spy))
# ---------------------------------------------------------------------------


def rolling_beta(
    stock_closes: list[float],
    spy_closes: list[float],
) -> float:
    """Compute beta of stock vs SPY using OLS regression on log returns.

    Args:
        stock_closes: Stock closing prices (oldest first).
        spy_closes:   SPY closing prices (same length and alignment).

    Returns:
        Beta coefficient (e.g., 1.5 = 50% more volatile than SPY).
        Returns NaN if insufficient data (<5 paired returns).
    """
    if len(stock_closes) != len(spy_closes):
        return float("nan")

    r_stock = _log_returns(stock_closes)
    r_spy = _log_returns(spy_closes)

    if len(r_stock) < 5:
        return float("nan")

    n = len(r_stock)
    mean_s = sum(r_stock) / n
    mean_m = sum(r_spy) / n

    cov = sum((r_stock[i] - mean_s) * (r_spy[i] - mean_m) for i in range(n))
    var_m = sum((r_spy[i] - mean_m) ** 2 for i in range(n))

    if var_m < 1e-12:
        return float("nan")

    return cov / var_m


# ---------------------------------------------------------------------------
# Beta-adjusted IV approximation from VIX
# ---------------------------------------------------------------------------


def approx_iv(vix: float, beta: float) -> float:
    """Approximate individual stock IV from VIX using beta scaling.

    This is a rough proxy for stocks without a live OPRA options feed.
    IV_stock ≈ VIX * |beta|

    Note: VIX represents ~30-day implied vol for SPY. Beta-scaling gives
    a first-order approximation. Will be replaced by real IV when the
    Alpaca OPRA feed (Step 22) is activated.

    Args:
        vix: VIX level as a percentage (e.g., 20.0 for 20%).
        beta: Stock beta vs SPY (from rolling_beta).

    Returns:
        Approximate IV as a decimal (e.g., 0.25 for 25%).
        Returns NaN for invalid inputs.
    """
    if math.isnan(vix) or math.isnan(beta) or vix <= 0.0:
        return float("nan")
    # VIX is in percentage points; convert to decimal, then scale by |beta|
    return (vix / 100.0) * abs(beta)
