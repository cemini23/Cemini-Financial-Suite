"""Sector rotation models — Step 25 implementation.

Published to intel:sector_rotation (TTL=3600, refreshed every 30 min).
Architecture: RRG-style quadrant classification (Leading/Weakening/Lagging/Improving)
with offensive vs defensive rotation bias.
"""

import time
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SectorSnapshot(BaseModel):
    """RS analysis snapshot for a single sector ETF vs SPY."""

    model_config = ConfigDict(extra="allow")

    symbol: str
    name: str
    rs_ratio: float        # RS Ratio normalized to 100 at start of lookback window
    rs_momentum: float     # Rate of change of RS Ratio (positive = accelerating)
    rank: int              # Ordinal rank 1-11 by RS Ratio (1 = strongest)
    quadrant: Literal["LEADING", "WEAKENING", "LAGGING", "IMPROVING"]


class SectorRotationIntel(BaseModel):
    """Sector rotation analysis published to intel:sector_rotation.

    Payload structure:
        {
            "timestamp": "2026-03-15T14:30:00",
            "lookback_days": 21,
            "sectors": {"XLK": SectorSnapshot, ...},
            "top_3": ["XLK", "XLY", "XLF"],
            "bottom_3": ["XLU", "XLRE", "XLP"],
            "rotation_bias": "RISK_ON",
            "offensive_score": 4,
            "defensive_score": 1
        }
    """

    model_config = ConfigDict(extra="allow")

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    lookback_days: int = 21
    sectors: dict[str, SectorSnapshot] = Field(default_factory=dict)
    top_3: list[str] = Field(default_factory=list)
    bottom_3: list[str] = Field(default_factory=list)
    rotation_bias: Literal["RISK_ON", "RISK_OFF", "NEUTRAL"] = "NEUTRAL"
    offensive_score: int = 0
    defensive_score: int = 0
    published_at: float = Field(default_factory=time.time)
