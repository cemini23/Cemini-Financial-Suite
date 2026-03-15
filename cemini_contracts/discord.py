"""Discord alert models — Step 36 Discord Alert Enrichment.

Published as enriched embed metadata; also used to type-check alert payloads
before they are sent to the Discord webhook.
"""
from __future__ import annotations

import time
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

AlertType = Literal["SIGNAL", "TRADE", "WARNING", "CRITICAL", "INFO", "REGIME_CHANGE"]


class DiscordAlert(BaseModel):
    """Structured Discord alert with optional intel enrichment context."""

    model_config = ConfigDict(extra="allow")

    title: str
    message: str
    alert_type: AlertType = "INFO"
    ticker: Optional[str] = None

    # Intel Bus context (populated by DiscordNotifier._gather_context)
    regime: Optional[str] = None
    rotation_bias: Optional[str] = None
    vix_level: Optional[float] = None
    earnings_cluster: bool = False
    ticker_near_earnings: bool = False

    sent_at: float = Field(default_factory=time.time)
    http_status: Optional[int] = None
