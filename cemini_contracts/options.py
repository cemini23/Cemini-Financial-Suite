"""Options Greeks and volatility surface models — Step 23.

Published to intel:vol_surface (TTL=3600, refreshed every 30 min).
Architecture: pure-math computation in options_greeks/ package.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class OptionGreeks(BaseModel):
    """Black-Scholes Greeks for a single European option."""

    model_config = ConfigDict(extra="allow")

    price: float
    delta: float
    gamma: float
    theta: float      # per calendar day (negative = time decay)
    vega: float       # per 1% vol move
    rho: float
    option_type: Literal["call", "put"]


class BinaryGreeks(BaseModel):
    """Cash-or-nothing binary option Greeks (for Kalshi contract analysis)."""

    model_config = ConfigDict(extra="allow")

    price: float      # e^(-rT) * N(d2)
    delta: float      # always positive for binary call
    gamma: float      # can be negative
    theta: float      # per calendar day
    vega: float       # per 1% vol move


class VolSurfaceEntry(BaseModel):
    """Volatility data for a single tracked equity symbol."""

    model_config = ConfigDict(extra="allow")

    symbol: str
    realized_vol_21d: Optional[float] = None    # close-to-close annualised
    parkinson_vol_21d: Optional[float] = None   # range-based, more efficient
    vol_regime: Optional[Literal["LOW", "NORMAL", "HIGH"]] = None
    approx_iv: Optional[float] = None           # beta-adjusted VIX proxy
    beta_to_spy: Optional[float] = None


class VolSurfaceIntel(BaseModel):
    """Full volatility surface snapshot — published to intel:vol_surface."""

    model_config = ConfigDict(extra="allow")

    timestamp: datetime
    vix: Optional[float] = None                 # from intel:vix_level
    symbols: dict[str, VolSurfaceEntry]
    market_vol_regime: Literal["LOW", "NORMAL", "HIGH"]
    high_vol_symbols: list[str]
    low_vol_symbols: list[str]
    total_tracked: int
