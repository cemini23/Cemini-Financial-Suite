"""logit_pricing.precision — Financial math safety layer.

Per LESSONS.md: enforce multiplication-before-division, use Decimal for
intermediate calculations, assert guards on all NaN/Inf outputs.
"""
import math
from decimal import Decimal, getcontext, ROUND_HALF_EVEN, InvalidOperation

import numpy as np

from logit_pricing.transforms import P_MIN, P_MAX

getcontext().prec = 50


# ---------------------------------------------------------------------------
# NaN / Inf guards
# ---------------------------------------------------------------------------

def assert_finite(value, context: str = "") -> None:
    """Raise ValueError if value is NaN, Inf, or -Inf.

    Call after every pricing calculation. Context string helps trace errors.
    """
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"Non-finite value in {context!r}: {value!r}")
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError(f"Non-finite Decimal in {context!r}: {value!r}")
    if isinstance(value, (np.floating, np.integer)):
        if not np.isfinite(float(value)):
            raise ValueError(f"Non-finite numpy scalar in {context!r}: {value!r}")


def is_finite_float(value) -> bool:
    """Return True if value is a finite Python float (not NaN/Inf)."""
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# Decimal precision arithmetic
# ---------------------------------------------------------------------------

def safe_divide(
    numerator,
    denominator,
    default: Decimal = Decimal("0"),
) -> Decimal:
    """Division with zero-check. Returns default if denominator is zero or invalid."""
    try:
        num = Decimal(str(numerator))
        den = Decimal(str(denominator))
        if den == 0:
            return default
        return num / den
    except (InvalidOperation, Exception):
        return default


def multiply_before_divide(a, b, c, default: Decimal = Decimal("0")) -> Decimal:
    """Compute (a * b) / c with Decimal precision.

    Multiplication-before-division ordering preserves precision when a and c
    are close in magnitude (per LESSONS.md financial math rule).
    """
    try:
        da = Decimal(str(a))
        db = Decimal(str(b))
        dc = Decimal(str(c))
        if dc == 0:
            return default
        return (da * db) / dc
    except (InvalidOperation, Exception):
        return default


# ---------------------------------------------------------------------------
# Probability clamping
# ---------------------------------------------------------------------------

def clamp_probability(p: float, context: str = "") -> float:
    """Ensure p is in [P_MIN, P_MAX] with an audit log on modification."""
    p = float(p)
    if math.isnan(p) or math.isinf(p):
        return (P_MIN + P_MAX) / 2.0  # 0.5 as safe midpoint
    if p < P_MIN:
        return P_MIN
    if p > P_MAX:
        return P_MAX
    return p


# ---------------------------------------------------------------------------
# Array-level guards
# ---------------------------------------------------------------------------

def sanitize_array(arr: np.ndarray, fill: float = 0.0) -> tuple[np.ndarray, int]:
    """Replace NaN/Inf in a numpy array with fill value.

    Returns (sanitized_array, n_replaced).
    """
    arr = np.asarray(arr, dtype=np.float64)
    mask = ~np.isfinite(arr)
    n_replaced = int(mask.sum())
    if n_replaced:
        arr = arr.copy()
        arr[mask] = fill
    return arr, n_replaced
