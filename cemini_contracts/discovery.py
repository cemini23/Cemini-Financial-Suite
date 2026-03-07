"""Opportunity discovery models — Step 26 implementation.

These contracts define the interface for the Opportunity Discovery Engine.
Architecture paradigm: Intelligence-in, ticker-out.
The discovery layer surfaces tickers; the existing signal machinery
(playbook, regime gate, risk engine) evaluates what is surfaced.
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


# ── Step 26 Phase 1 contracts ────────────────────────────────────────────────


class ExtractedTicker(BaseModel):
    """A ticker symbol extracted from an intel message payload."""

    model_config = ConfigDict(extra="allow")

    symbol: str
    source_channel: str
    confidence: float = Field(ge=0.0, le=1.0)
    extraction_method: str = "regex"  # "dollar_sign" | "company_name" | "alias" | "fuzzy"
    timestamp: float = Field(default_factory=time.time)


class ConvictionScore(BaseModel):
    """Per-ticker Bayesian conviction state stored in Redis."""

    model_config = ConfigDict(extra="allow")

    ticker: str
    conviction: float = Field(ge=0.01, le=0.99)
    last_updated: str = ""          # ISO timestamp
    source_count: int = 0
    sources: list[str] = Field(default_factory=list)
    first_seen: str = ""            # ISO timestamp


class WatchlistMember(BaseModel):
    """Richer watchlist entry used by opportunity_screener."""

    model_config = ConfigDict(extra="allow")

    ticker: str
    conviction: float = Field(ge=0.01, le=0.99)
    promoted_at: float = Field(default_factory=time.time)
    last_intel_at: float = Field(default_factory=time.time)
    source_channels: list[str] = Field(default_factory=list)
    promotion_reason: str = ""
    is_core: bool = False


class WatchlistUpdate(BaseModel):
    """Published to intel:watchlist_update on every promotion/demotion."""

    model_config = ConfigDict(extra="allow")

    action: str                     # "promoted" | "demoted" | "evicted"
    ticker: str
    conviction: float
    reason: str = ""
    timestamp: float = Field(default_factory=time.time)


class DiscoverySnapshot(BaseModel):
    """Published to intel:discovery_snapshot every 5 minutes."""

    model_config = ConfigDict(extra="allow")

    watchlist: list[dict[str, Any]] = Field(default_factory=list)
    rising: list[dict[str, Any]] = Field(default_factory=list)    # top 10
    fading: list[dict[str, Any]] = Field(default_factory=list)    # top 5
    tickers_tracked: int = 0
    messages_processed: int = 0
    timestamp: float = Field(default_factory=time.time)


class DiscoveryAuditRecord(BaseModel):
    """One row in discovery_audit_log Postgres hypertable."""

    model_config = ConfigDict(extra="allow")

    timestamp: float = Field(default_factory=time.time)
    ticker: str
    action: str          # 'conviction_update'|'promoted'|'demoted'|'evicted'|'decayed'
    conviction_before: Optional[float] = None
    conviction_after: Optional[float] = None
    source_channel: Optional[str] = None
    extraction_confidence: Optional[float] = None
    likelihood_ratio: Optional[float] = None
    multi_source_bonus: bool = False
    payload: Optional[dict[str, Any]] = None
    watchlist_size: Optional[int] = None
