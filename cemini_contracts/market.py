"""Market data models.

Matches tick shapes stored in Postgres raw_market_ticks and the
dict payloads read by playbook/runner.py and QuantOS/core/engine.py.
"""

import logging
import time
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class MarketTick(BaseModel):
    """One price tick as stored in raw_market_ticks Postgres table.

    Polygon free-tier note: ORDER BY created_at, not timestamp — bar
    close times can be hours behind real time. (See LESSONS.md)
    """

    model_config = ConfigDict(extra="allow")

    symbol: str
    price: float
    timestamp: Optional[Any] = None   # str ISO or float epoch — both seen in practice
    created_at: Optional[Any] = None
    volume: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    source: str = "polygon"


class MarketEvent(BaseModel):
    """Generic market event — wraps a tick with context."""

    model_config = ConfigDict(extra="allow")

    event_type: str = "tick"           # "tick" | "bar" | "trade" | "quote"
    symbol: str
    price: Optional[float] = None
    timestamp: float = Field(default_factory=time.time)
    source: str = "unknown"
    data: dict[str, Any] = Field(default_factory=dict)


class FearGreedIndex(BaseModel):
    """macro:fear_greed Redis key — stored as raw float, not Intel envelope."""

    model_config = ConfigDict(extra="allow")

    value: float = 50.0               # 0 (extreme fear) → 100 (extreme greed)
    source: str = "macro_harvester"
    timestamp: float = Field(default_factory=time.time)
