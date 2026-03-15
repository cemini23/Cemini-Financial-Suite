"""
Cemini Financial Suite — Black-Scholes Pricing Engine (Step 23)

Pure-math implementation using only Python stdlib (math module).
No scipy dependency required.

All formulas follow Hull (2018) "Options, Futures, and Other Derivatives".

Public API
----------
    bs_price(S, K, T, r, sigma, option_type) -> float
    delta(S, K, T, r, sigma, option_type) -> float
    gamma(S, K, T, r, sigma) -> float
    theta(S, K, T, r, sigma, option_type) -> float   # per calendar day
    vega(S, K, T, r, sigma) -> float                 # per 1% vol move
    rho(S, K, T, r, sigma, option_type) -> float
    greeks(S, K, T, r, sigma, option_type) -> OptionGreeks
"""
from __future__ import annotations

import math
from typing import Literal

# ---------------------------------------------------------------------------
# Internal: standard normal CDF / PDF (stdlib only)
# ---------------------------------------------------------------------------


def norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function using math.erf."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_pdf(x: float) -> float:
    """Standard normal probability density function."""
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


# ---------------------------------------------------------------------------
# Internal: d1 / d2 helper
# ---------------------------------------------------------------------------


def _d1d2(
    S: float, K: float, T: float, r: float, sigma: float
) -> tuple[float, float]:
    """Compute Black-Scholes d1 and d2."""
    if T <= 0.0 or sigma <= 0.0 or S <= 0.0 or K <= 0.0:
        raise ValueError(
            f"Invalid BS inputs: S={S}, K={K}, T={T}, r={r}, sigma={sigma}"
        )
    sqrt_T = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T
    return d1, d2


# ---------------------------------------------------------------------------
# Pricing
# ---------------------------------------------------------------------------


def bs_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: Literal["call", "put"] = "call",
) -> float:
    """European option price under Black-Scholes.

    Args:
        S: Spot price.
        K: Strike price.
        T: Time to expiry in years.
        r: Risk-free interest rate (annualised, continuously compounded).
        sigma: Annualised volatility.
        option_type: "call" or "put".

    Returns:
        Theoretical option price ≥ 0.

    Raises:
        ValueError: For non-positive S, K, T, sigma.
    """
    if T <= 0.0:
        # At expiry: intrinsic value only
        intrinsic = S - K if option_type == "call" else K - S
        return max(0.0, intrinsic)

    d1, d2 = _d1d2(S, K, T, r, sigma)
    disc = math.exp(-r * T)

    if option_type == "call":
        return S * norm_cdf(d1) - K * disc * norm_cdf(d2)
    else:
        return K * disc * norm_cdf(-d2) - S * norm_cdf(-d1)


# ---------------------------------------------------------------------------
# Greeks — closed-form (not finite-difference)
# ---------------------------------------------------------------------------


def delta(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: Literal["call", "put"] = "call",
) -> float:
    """Option delta: ∂V/∂S.

    Call delta ∈ [0, 1]; put delta ∈ [-1, 0].
    """
    if T <= 0.0:
        # At expiry: delta is 1 if ITM, 0 if OTM (call), sign-flipped for put
        if option_type == "call":
            return 1.0 if S > K else 0.0
        else:
            return -1.0 if S < K else 0.0

    d1, _ = _d1d2(S, K, T, r, sigma)
    if option_type == "call":
        return norm_cdf(d1)
    else:
        return norm_cdf(d1) - 1.0


def gamma(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
) -> float:
    """Option gamma: ∂²V/∂S² (identical for call and put).

    Always non-negative for long options.
    """
    if T <= 0.0:
        return 0.0
    d1, _ = _d1d2(S, K, T, r, sigma)
    return norm_pdf(d1) / (S * sigma * math.sqrt(T))


def theta(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: Literal["call", "put"] = "call",
) -> float:
    """Option theta: ∂V/∂t per *calendar day* (negative = time decay).

    Convention: negative means the option loses value as one calendar day
    passes (standard "theta decay" sign convention).
    """
    if T <= 0.0:
        return 0.0
    d1, d2 = _d1d2(S, K, T, r, sigma)
    sqrt_T = math.sqrt(T)
    disc = math.exp(-r * T)

    common = -(S * norm_pdf(d1) * sigma) / (2.0 * sqrt_T)

    if option_type == "call":
        annual = common - r * K * disc * norm_cdf(d2)
    else:
        annual = common + r * K * disc * norm_cdf(-d2)

    return annual / 365.0  # per calendar day


def vega(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
) -> float:
    """Option vega: ∂V/∂σ per *1% vol move* (identical for call and put).

    e.g., vega=0.10 means a 1% rise in vol increases option value by $0.10.
    """
    if T <= 0.0:
        return 0.0
    d1, _ = _d1d2(S, K, T, r, sigma)
    # Full vega (per unit vol): S * n(d1) * sqrt(T)
    # Per 1% vol move: divide by 100
    return S * norm_pdf(d1) * math.sqrt(T) / 100.0


def rho(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: Literal["call", "put"] = "call",
) -> float:
    """Option rho: ∂V/∂r per 1% rate move.

    e.g., rho=0.05 means a 1% rise in r increases option value by $0.05.
    """
    if T <= 0.0:
        return 0.0
    _, d2 = _d1d2(S, K, T, r, sigma)
    disc = math.exp(-r * T)

    if option_type == "call":
        return K * T * disc * norm_cdf(d2) / 100.0
    else:
        return -K * T * disc * norm_cdf(-d2) / 100.0


# ---------------------------------------------------------------------------
# Convenience: all Greeks in one call
# ---------------------------------------------------------------------------


def greeks(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: Literal["call", "put"] = "call",
) -> dict:
    """Compute all 5 Greeks plus BS price in a single call.

    Returns a plain dict (use with OptionGreeks model from cemini_contracts).
    Keys: price, delta, gamma, theta, vega, rho, option_type.
    """
    return {
        "price": bs_price(S, K, T, r, sigma, option_type),
        "delta": delta(S, K, T, r, sigma, option_type),
        "gamma": gamma(S, K, T, r, sigma),
        "theta": theta(S, K, T, r, sigma, option_type),
        "vega": vega(S, K, T, r, sigma),
        "rho": rho(S, K, T, r, sigma, option_type),
        "option_type": option_type,
    }
