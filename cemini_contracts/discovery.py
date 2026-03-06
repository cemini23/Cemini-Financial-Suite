"""Opportunity discovery models — stub for Step 26.

These contracts define the interface that Step 26 (Opportunity Discovery Engine)
will populate. They are referenced here so Step 28 contracts are complete and
Step 26 can implement against this spec without changing the contract layer.
"""

import logging
import time
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class OpportunitySource(str, Enum):
    """Which discovery engine surfaced this opportunity."""

    GDELT = "gdelt"
    WEATHER = "weather"
    SOCIAL = "social"
    QUANT = "quant"
    MANUAL = "manual"
    UNKNOWN = "unknown"


class DiscoveryOpportunity(BaseModel):
    """A market opportunity surfaced by the discovery engine (Step 26).

    Architecture paradigm: Intelligence-in, ticker-out.
    The discovery layer surfaces tickers; the existing signal machinery
    (playbook, regime gate, risk engine) evaluates what is surfaced.
    """

    model_config = ConfigDict(extra="allow")

    ticker: str
    opportunity_type: str = "equity"       # "equity" | "crypto" | "prediction_market"
    source: str = OpportunitySource.UNKNOWN
    confidence: float = 0.0
    rationale: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)
    expiry: Optional[float] = None         # epoch when opportunity is stale


class WatchlistEntry(BaseModel):
    """One entry in the dynamic watchlist populated by DiscoveryEngine."""

    model_config = ConfigDict(extra="allow")

    ticker: str
    added_at: float = Field(default_factory=time.time)
    source: str = OpportunitySource.UNKNOWN
    priority: int = 5                      # 1 (highest) → 10 (lowest)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
