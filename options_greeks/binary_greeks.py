"""
Cemini Financial Suite — Binary (Digital) Option Greeks (Step 23)

Cash-or-nothing binary call/put pricing and Greeks.
Complements logit_pricing/ which gives Kalshi fair value via jump-diffusion —
binary_greeks provides closed-form sensitivity analysis.

Reference: Hull (2018) Ch. 26 "Exotic Options".

For a cash-or-nothing binary call paying $1 if S_T > K:
    price  = e^(-rT) * N(d2)

Public API
----------
    binary_price(S, K, T, r, sigma) -> float
    binary_delta(S, K, T, r, sigma) -> float
    binary_gamma(S, K, T, r, sigma) -> float
    binary_theta(S, K, T, r, sigma) -> float    # per calendar day
    binary_vega(S, K, T, r, sigma) -> float     # per 1% vol move
    binary_greeks(S, K, T, r, sigma) -> dict
"""
from __future__ import annotations

import math

from options_greeks.black_scholes import norm_cdf, norm_pdf, _d1d2


def binary_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
) -> float:
    """Cash-or-nothing binary call price = e^(-rT) * N(d2).

    Represents the risk-neutral probability the contract expires ITM,
    discounted to present value.

    At expiry (T=0): returns 1.0 if S > K, else 0.0.
    """
    if T <= 0.0:
        return 1.0 if S > K else 0.0
    disc = math.exp(-r * T)
    _, d2 = _d1d2(S, K, T, r, sigma)
    return disc * norm_cdf(d2)


def binary_delta(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
) -> float:
    """Binary call delta: ∂price/∂S.

    Always positive for a binary call (higher spot → more likely ITM).
    """
    if T <= 0.0:
        return 0.0
    disc = math.exp(-r * T)
    sqrt_T = math.sqrt(T)
    _, d2 = _d1d2(S, K, T, r, sigma)
    return disc * norm_pdf(d2) / (S * sigma * sqrt_T)


def binary_gamma(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
) -> float:
    """Binary call gamma: ∂²price/∂S².

    Can be negative (binary gamma changes sign at-the-money).
    Formula: -e^(-rT) * n(d2) * d1 / (S² * σ² * T)
    """
    if T <= 0.0:
        return 0.0
    disc = math.exp(-r * T)
    d1, d2 = _d1d2(S, K, T, r, sigma)
    return -disc * norm_pdf(d2) * d1 / (S * S * sigma * sigma * T)


def binary_theta(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
) -> float:
    """Binary call theta: ∂price/∂t per calendar day (negative = time decay).

    Derivation:
        price = e^(-rT) * N(d2)
        ∂price/∂T = -r*e^(-rT)*N(d2) + e^(-rT)*n(d2)*∂d2/∂T
        ∂d2/∂T = [(r - σ²/2)/(σ√T) - d2/(2T)]
    Then per calendar day: divide by 365, negate (θ = -∂V/∂T * 1/365).
    """
    if T <= 0.0:
        return 0.0
    disc = math.exp(-r * T)
    sqrt_T = math.sqrt(T)
    _, d2 = _d1d2(S, K, T, r, sigma)

    dd2_dT = (r - 0.5 * sigma * sigma) / (sigma * sqrt_T) - d2 / (2.0 * T)
    annual = -r * disc * norm_cdf(d2) + disc * norm_pdf(d2) * dd2_dT
    # Convention: negative theta means losing value with passage of time
    return -annual / 365.0


def binary_vega(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
) -> float:
    """Binary call vega: ∂price/∂σ per 1% vol move.

    Formula: -e^(-rT) * n(d2) * d1 / σ / 100
    (negative: higher vol → binary price approaches 0.5*disc, can go up or down)
    """
    if T <= 0.0:
        return 0.0
    disc = math.exp(-r * T)
    d1, d2 = _d1d2(S, K, T, r, sigma)
    # ∂d2/∂σ = -d1/σ (see derivation in black_scholes.py comments)
    return -disc * norm_pdf(d2) * d1 / sigma / 100.0


def binary_greeks(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
) -> dict:
    """Compute all binary call Greeks in a single call.

    Returns a plain dict compatible with BinaryGreeks Pydantic model.
    Keys: price, delta, gamma, theta, vega.
    """
    return {
        "price": binary_price(S, K, T, r, sigma),
        "delta": binary_delta(S, K, T, r, sigma),
        "gamma": binary_gamma(S, K, T, r, sigma),
        "theta": binary_theta(S, K, T, r, sigma),
        "vega": binary_vega(S, K, T, r, sigma),
    }
