"""logit_pricing.indicators — TA indicators adapted to logit space.

Key insight (Shaw & Dalen 2025): computing moving averages in logit space
and inverting back to probability produces geometrically correct signals
that don't suffer from the [0,1] boundary compression of raw probability TA.

All functions accept numpy arrays of logit values (not raw probabilities).
Call logit_array() from transforms.py first to convert price series.

RSI uses Wilder's SMMA (NOT SMA) — see LESSONS.md re: QuantOS RSI bug.
"""
import numpy as np

from logit_pricing.transforms import inv_logit_array
from logit_pricing.precision import sanitize_array


# ---------------------------------------------------------------------------
# Moving averages in logit space
# ---------------------------------------------------------------------------

def logit_sma(logits: np.ndarray, window: int) -> np.ndarray:
    """Simple moving average of logit values.

    Returns array of same length; first (window-1) entries are NaN.
    """
    logits, _ = sanitize_array(logits, fill=np.nan)
    result = np.full_like(logits, np.nan)
    for idx in range(window - 1, len(logits)):
        result[idx] = np.nanmean(logits[idx - window + 1 : idx + 1])
    return result


def logit_ema(logits: np.ndarray, span: int) -> np.ndarray:
    """Exponential moving average of logit values (pandas-style span EMA).

    Uses alpha = 2 / (span + 1).
    Returns array of same length; first entry seeded with logits[0].
    """
    logits, _ = sanitize_array(logits, fill=0.0)
    if len(logits) == 0:
        return logits
    alpha = 2.0 / (span + 1)
    result = np.empty_like(logits)
    result[0] = logits[0]
    for idx in range(1, len(logits)):
        result[idx] = alpha * logits[idx] + (1.0 - alpha) * result[idx - 1]
    return result


# ---------------------------------------------------------------------------
# Bollinger Bands in logit space
# ---------------------------------------------------------------------------

def logit_bollinger(
    logits: np.ndarray,
    window: int = 20,
    num_std: float = 2.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Bollinger Bands computed on logit values.

    Returns:
        (upper, mid, lower) arrays — all in logit space.
        Bands are always symmetric around mid (unlike probability-space bands
        which can clip below 0 or above 1).

    Contracts whose logit is outside the 2σ bands are mispricing candidates.
    """
    logits, _ = sanitize_array(logits, fill=np.nan)
    mid = np.full_like(logits, np.nan)
    upper = np.full_like(logits, np.nan)
    lower = np.full_like(logits, np.nan)

    for idx in range(window - 1, len(logits)):
        window_vals = logits[idx - window + 1 : idx + 1]
        valid = window_vals[np.isfinite(window_vals)]
        if len(valid) < 2:
            continue
        mn = np.mean(valid)
        sd = np.std(valid, ddof=1)
        mid[idx] = mn
        upper[idx] = mn + num_std * sd
        lower[idx] = mn - num_std * sd

    return upper, mid, lower


# ---------------------------------------------------------------------------
# Logit RSI — Wilder's SMMA (NOT SMA)
# ---------------------------------------------------------------------------

def logit_rsi(logits: np.ndarray, period: int = 14) -> np.ndarray:
    """RSI computed on logit returns (delta logit between consecutive periods).

    Uses Wilder's Smoothed Moving Average (SMMA), NOT SMA.
    Per LESSONS.md: QuantOS RSI uses SMA-RSI — we do NOT repeat that mistake.

    Wilder's SMMA: EMA with alpha = 1/period
    """
    logits, _ = sanitize_array(logits, fill=0.0)
    if len(logits) < period + 1:
        return np.full(len(logits), np.nan)

    deltas = np.diff(logits)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    result = np.full(len(logits), np.nan)

    # Seed with simple average over first 'period' deltas
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    alpha = 1.0 / period  # Wilder's smoothing factor

    for idx in range(period, len(deltas)):
        # Wilder's SMMA: new_avg = (prev_avg * (period-1) + current) / period
        avg_gain = (avg_gain * (period - 1) + gains[idx]) / period
        avg_loss = (avg_loss * (period - 1) + losses[idx]) / period

        if avg_loss < 1e-12:
            result[idx + 1] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[idx + 1] = 100.0 - (100.0 / (1.0 + rs))

    return result


# ---------------------------------------------------------------------------
# Implied belief volatility (Shaw & Dalen §4)
# ---------------------------------------------------------------------------

def implied_belief_vol(
    bid: float,
    ask: float,
    tau: float,
    gamma: float = 0.08,
    k: float = 1.4,
    n_iter: int = 10,
) -> float:
    """Calibrate implied belief volatility σ_b from market bid/ask spread.

    Shaw & Dalen (2025) model:
        Δx_model(σ_b) = γ·τ·σ_b² + (2/k)·log(1 + γ/k)
        Δx_mkt = logit(ask) - logit(bid)

    Solved by Newton-Raphson:
        σ_{n+1} = max(0, σ_n - f(σ_n)/f'(σ_n))
        f(σ) = Δx_model(σ) - Δx_mkt
        f'(σ) = 2·γ·τ·σ

    Args:
        bid, ask: probability-scale prices (0-1)
        tau:      time to resolution in years (e.g. 1 day = 1/365)
        gamma:    risk aversion coefficient (default 0.08)
        k:        order-arrival parameter (default 1.4)

    Returns:
        implied σ_b ≥ 0
    """
    from logit_pricing.transforms import logit as _logit
    dx_mkt = _logit(ask) - _logit(bid)
    if dx_mkt <= 0:
        return 0.0

    spread_const = (2.0 / k) * np.log(1.0 + gamma / max(k, 1e-9))
    sigma = 0.3  # initial guess

    for _ in range(n_iter):
        f = gamma * tau * sigma ** 2 + spread_const - dx_mkt
        fp = 2.0 * gamma * tau * sigma
        if abs(fp) < 1e-12:
            break
        sigma = max(0.0, sigma - f / fp)

    return sigma


# ---------------------------------------------------------------------------
# Mean-reversion score
# ---------------------------------------------------------------------------

def logit_mean_reversion_score(
    current_logit: float,
    ema_logit: float,
    logit_vol: float,
) -> float:
    """How far the current logit is from EMA, normalized by logit volatility.

    Score > 0 → contract is overpriced (logit above EMA) → consider NO
    Score < 0 → contract is underpriced (logit below EMA) → consider YES
    Score ≈ 0 → fairly priced

    Clamped to [-3, 3] (beyond 3σ is extreme and likely a jump).
    """
    if logit_vol < 1e-9:
        return 0.0
    raw = (current_logit - ema_logit) / logit_vol
    return float(np.clip(raw, -3.0, 3.0))
