"""
Cemini Financial Suite — Implied Volatility Solver (Step 23)

Newton-Raphson solver with bisection fallback.
No scipy dependency — pure stdlib math.

Public API
----------
    implied_volatility(market_price, S, K, T, r, option_type, ...) -> float | NaN
"""
from __future__ import annotations

import math
from typing import Literal

from options_greeks.black_scholes import bs_price, norm_pdf, _d1d2


def implied_volatility(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: Literal["call", "put"] = "call",
    max_iter: int = 50,
    tol: float = 1e-6,
) -> float:
    """Compute implied volatility from a market option price.

    Uses Newton-Raphson (fast) with bisection fallback (robust).

    Args:
        market_price: Observed market price of the option.
        S: Spot price.
        K: Strike price.
        T: Time to expiry in years.
        r: Risk-free interest rate (continuously compounded).
        option_type: "call" or "put".
        max_iter: Maximum Newton-Raphson iterations.
        tol: Convergence tolerance on price difference.

    Returns:
        Implied volatility as a decimal (e.g., 0.25 for 25%).
        Returns float('nan') if:
          - T <= 0
          - market_price < intrinsic value (no valid IV exists)
          - Solver fails to converge
    """
    if T <= 0.0:
        return float("nan")

    # Intrinsic value guard
    disc = math.exp(-r * T)
    if option_type == "call":
        intrinsic = max(0.0, S - K * disc)
    else:
        intrinsic = max(0.0, K * disc - S)

    if market_price < intrinsic - tol:
        return float("nan")

    # Clip to intrinsic if below it by rounding noise
    if market_price < intrinsic:
        market_price = intrinsic

    # Upper bound check: call price cannot exceed S, put cannot exceed K*disc
    upper_bound = S if option_type == "call" else K * disc
    if market_price > upper_bound + tol:
        return float("nan")

    # Newton-Raphson
    sigma = 0.20  # initial guess
    for _ in range(max_iter):
        try:
            price = bs_price(S, K, T, r, sigma, option_type)
        except (ValueError, ZeroDivisionError):
            break

        diff = price - market_price
        if abs(diff) < tol:
            return sigma

        # Vega: ∂price/∂sigma = S * n(d1) * sqrt(T)
        try:
            d1, _ = _d1d2(S, K, T, r, sigma)
            v = S * norm_pdf(d1) * math.sqrt(T)
        except (ValueError, ZeroDivisionError):
            break

        if v < 1e-10:
            break  # fall through to bisection

        sigma = sigma - diff / v
        sigma = max(1e-6, min(sigma, 20.0))  # clamp to [~0, 2000%]

    # Bisection fallback
    return _bisection_iv(market_price, S, K, T, r, option_type, tol, max_iter * 4)


def _bisection_iv(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: str,
    tol: float,
    max_iter: int,
) -> float:
    """Bisection search on sigma ∈ [0.001, 5.0]."""
    lo, hi = 0.001, 5.0

    try:
        f_lo = bs_price(S, K, T, r, lo, option_type) - market_price
        f_hi = bs_price(S, K, T, r, hi, option_type) - market_price
    except (ValueError, ZeroDivisionError):
        return float("nan")

    # Market price must be bracketed
    if f_lo * f_hi > 0.0:
        return float("nan")

    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        try:
            f_mid = bs_price(S, K, T, r, mid, option_type) - market_price
        except (ValueError, ZeroDivisionError):
            return float("nan")

        if abs(f_mid) < tol or (hi - lo) < 1e-8:
            return mid

        if f_lo * f_mid < 0.0:
            hi = mid
            f_hi = f_mid
        else:
            lo = mid
            f_lo = f_mid

    return 0.5 * (lo + hi)
