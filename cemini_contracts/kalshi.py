"""Kalshi prediction-market models.

Matches shapes from Kalshi by Cemini module outputs, rover scanner
data, and the opportunity dicts used by CeminiAutopilot.
"""

import logging
import time
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KalshiOpportunity(BaseModel):
    """One trading opportunity produced by WeatherAnalyzer.analyze_market().

    Actual dict keys from weather_alpha/analyzer.py:
        {"city", "bracket", "signal", "expected_value", "edge", "reason"}
    """

    model_config = ConfigDict(extra="allow")

    city: Optional[str] = None
    bracket: Optional[str] = None
    signal: str = ""                # "DIAMOND ALPHA" | "GOLD ALPHA"
    expected_value: float = 0.0
    edge: float = 0.0
    reason: str = ""
    source: str = "weather_alpha"
    timestamp: float = Field(default_factory=time.time)


class AutopilotTradeCandidate(BaseModel):
    """One entry in the opportunities list built inside CeminiAutopilot.scan_and_execute().

    Fields added inline in autopilot.py:
        {"module", "signal", "score", "odds", "city" (optional)}
    """

    model_config = ConfigDict(extra="allow")

    module: str                    # "BTC" | "POWELL" | "SOCIAL" | "WEATHER" | "MUSK"
    signal: str
    score: int
    odds: float
    city: Optional[str] = None
    source: str = "kalshi_autopilot"
    timestamp: float = Field(default_factory=time.time)


class KalshiPosition(BaseModel):
    """Active Kalshi position returned by get_active_positions()."""

    model_config = ConfigDict(extra="allow")

    ticker: str
    position: int = 0              # number of contracts
    yes_bid: Optional[float] = None
    cost_basis: Optional[float] = None
    source: str = "kalshi_api"
    timestamp: float = Field(default_factory=time.time)


class RoverMarket(BaseModel):
    """One Kalshi market entry from the WebSocket rover scanner.

    Mirrors the keys used in ws_rover.py and rover.py.
    """

    model_config = ConfigDict(extra="allow")

    ticker: str
    series_ticker: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    yes_bid: float = 0.0
    yes_ask: float = 0.0
    no_bid: float = 0.0
    no_ask: float = 0.0
    volume: int = 0
    open_interest: int = 0
    status: str = "open"
    close_time: Optional[Any] = None
    source: str = "rover_scanner"
    timestamp: float = Field(default_factory=time.time)
