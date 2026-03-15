"""Earnings Calendar models — Step 19 implementation.

Published to intel:earnings_calendar (TTL=7200, refreshed every hour).
Data source: SEC EDGAR submissions API (free).
"""

import time
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class EarningsEvent(BaseModel):
    """Single ticker's earnings proximity status."""

    model_config = ConfigDict(extra="allow")

    symbol: str
    cik: str
    company_name: str
    last_filing_date: Optional[date] = None    # most recent 10-Q or 10-K
    last_filing_type: Optional[str] = None     # "10-Q" or "10-K"
    estimated_next_date: Optional[date] = None  # projected from historical cadence
    days_until_earnings: Optional[int] = None  # None if can't estimate
    status: Literal["REPORTING_THIS_WEEK", "REPORTING_SOON", "JUST_REPORTED", "CLEAR"] = "CLEAR"
    confidence: float = 0.0  # 0-1 based on cadence regularity


class EarningsCalendarIntel(BaseModel):
    """Published to intel:earnings_calendar.

    Payload structure:
        {
            "timestamp": "2026-03-15T14:30:00",
            "reporting_this_week": ["AAPL", "MSFT"],
            "reporting_soon": ["NVDA", "GOOGL"],
            "just_reported": ["JPM"],
            "earnings_cluster": false,
            "events": {"AAPL": EarningsEvent, ...},
            "total_tracked": 28
        }
    """

    model_config = ConfigDict(extra="allow")

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    reporting_this_week: list[str] = Field(default_factory=list)
    reporting_soon: list[str] = Field(default_factory=list)
    just_reported: list[str] = Field(default_factory=list)
    earnings_cluster: bool = False
    events: dict[str, EarningsEvent] = Field(default_factory=dict)
    total_tracked: int = 0
    published_at: float = Field(default_factory=time.time)
