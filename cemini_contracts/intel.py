"""Intel Bus envelope model.

Every key written by IntelPublisher uses this exact envelope:
    {"value": <mixed>, "source_system": str, "timestamp": float, "confidence": float}

Usage:
    from cemini_contracts.intel import IntelPayload
    payload = safe_validate(IntelPayload, raw_redis_value)
"""

import logging
import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class IntelPayload(BaseModel):
    """Generic intel:* envelope as written by IntelPublisher."""

    model_config = ConfigDict(extra="allow")

    value: Any
    source_system: str = "unknown"
    timestamp: float = Field(default_factory=time.time)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class FedBiasValue(BaseModel):
    """Structured value for intel:fed_bias."""

    model_config = ConfigDict(extra="allow")

    bias: str = "neutral"       # "dovish" | "hawkish" | "neutral"
    confidence: float = 0.0


class BtcVolumeSpikeValue(BaseModel):
    """Structured value for intel:btc_volume_spike."""

    model_config = ConfigDict(extra="allow")

    detected: bool = False
    multiplier: float = 0.0
    symbol: str = "BTC"


class PlaybookSnapshotValue(BaseModel):
    """Structured value nested inside intel:playbook_snapshot.value."""

    model_config = ConfigDict(extra="allow")

    regime: str = "UNKNOWN"
    detail: dict = Field(default_factory=dict)


class SocialScoreValue(BaseModel):
    """Structured value for intel:social_score."""

    model_config = ConfigDict(extra="allow")

    score: float = 0.0
    top_ticker: str = "BTC"
