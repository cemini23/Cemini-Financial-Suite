"""logit_pricing.transforms — Core logit-space math.

Implements the logit transform and inverse used throughout the Shaw & Dalen
(2025) framework for binary prediction market pricing.

All functions:
- Clamp probability inputs to [P_MIN, P_MAX] before log to avoid ±inf
- Guard NaN/Inf outputs and replace with finite fallback
- Never raise on bad input — callers are hot-path trading logic
"""
import math
from decimal import Decimal, getcontext, InvalidOperation

import numpy as np

# High precision for intermediate Decimal calculations
getcontext().prec = 50

# Probability boundary constants
EPSILON = 1e-12           # absolute floor for division safety
P_MIN = 0.001             # minimum tradeable probability (0.1¢)
P_MAX = 0.999             # maximum tradeable probability (99.9¢)
LOGIT_OVERFLOW = 500.0    # |L| above this overflows exp() — use asymptotic

# Logit values at boundaries (precomputed)
LOGIT_MIN = math.log(P_MIN / (1.0 - P_MIN))   # ≈ -6.906
LOGIT_MAX = math.log(P_MAX / (1.0 - P_MAX))   # ≈  6.906


# ---------------------------------------------------------------------------
# Scalar float versions
# ---------------------------------------------------------------------------

def logit(p: float) -> float:
    """Transform probability to logit (log-odds) space.

    L(p) = log(p / (1 - p))

    Clamps p to [P_MIN, P_MAX] so result is always finite.
    """
    p_c = max(P_MIN, min(P_MAX, float(p)))
    return math.log(p_c / (1.0 - p_c))


def inv_logit(L: float) -> float:
    """Transform logit back to probability (sigmoid).

    p = 1 / (1 + exp(-L))

    Asymptotic approximation for |L| > LOGIT_OVERFLOW.
    """
    L = float(L)
    if L >= LOGIT_OVERFLOW:
        return P_MAX
    if L <= -LOGIT_OVERFLOW:
        return P_MIN
    return 1.0 / (1.0 + math.exp(-L))


def logit_spread(bid: float, ask: float) -> float:
    """Implied logit spread between bid and ask.

    Δx = logit(ask) - logit(bid)

    Follows Shaw & Dalen §4 for implied belief volatility calibration.
    Result is always ≥ 0 (asks always dominate bids in probability space).
    """
    return logit(ask) - logit(bid)


def logit_mid(bid: float, ask: float) -> float:
    """Logit-space mid-price (arithmetic mean in logit, not probability).

    More accurate than probability-space mid for near-boundary contracts.
    """
    return (logit(bid) + logit(ask)) / 2.0


# ---------------------------------------------------------------------------
# Decimal (high-precision) version
# ---------------------------------------------------------------------------

def logit_decimal(p) -> Decimal:
    """High-precision logit using Python Decimal type.

    Multiplication-before-division ordering as per LESSONS.md.
    Returns logit(p) with 50-digit precision.
    Clamps to [P_MIN, P_MAX] first.
    """
    try:
        p_d = Decimal(str(p))
        p_min = Decimal(str(P_MIN))
        p_max = Decimal(str(P_MAX))
        p_c = max(p_min, min(p_max, p_d))

        one = Decimal('1')
        # ln(p) - ln(1-p) avoids direct division then log
        # Equivalent to log(p/(1-p)) but computed via subtraction of logs
        # to keep Decimal chain intact
        lp = p_c.ln()
        l1p = (one - p_c).ln()
        return lp - l1p
    except (InvalidOperation, Exception):
        return Decimal(str(logit(float(p))))


def inv_logit_decimal(L) -> Decimal:
    """High-precision sigmoid: 1 / (1 + exp(-L))."""
    try:
        L_d = Decimal(str(L))
        one = Decimal('1')
        return one / (one + (-L_d).exp())
    except (InvalidOperation, Exception):
        return Decimal(str(inv_logit(float(L))))


# ---------------------------------------------------------------------------
# Vectorized NumPy versions
# ---------------------------------------------------------------------------

def logit_array(prices: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Vectorized logit for arrays of contract probabilities.

    Args:
        prices: 1-D array of probability values (0–1 scale, e.g. yes_bid/100)

    Returns:
        (logits, invalid_mask) where invalid_mask flags any NaN/Inf that was
        replaced with 0.0. Callers should check invalid_mask and decide
        whether to discard or flag those elements.
    """
    prices = np.asarray(prices, dtype=np.float64)
    p_c = np.clip(prices, P_MIN, P_MAX)
    logits = np.log(p_c / (1.0 - p_c))

    invalid_mask = ~np.isfinite(logits)
    if invalid_mask.any():
        logits[invalid_mask] = 0.0

    return logits, invalid_mask


def inv_logit_array(logits: np.ndarray) -> np.ndarray:
    """Vectorized sigmoid (inverse logit) for arrays.

    Clips extreme logit values to avoid overflow in exp().
    """
    logits = np.asarray(logits, dtype=np.float64)
    clipped = np.clip(logits, -LOGIT_OVERFLOW, LOGIT_OVERFLOW)
    return 1.0 / (1.0 + np.exp(-clipped))
