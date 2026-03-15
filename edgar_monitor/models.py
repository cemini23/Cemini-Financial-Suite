"""Cemini Financial Suite — EDGAR Monitor Pydantic models (Step 17)."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class FilingSignificance(BaseModel):
    """Significance assessment for a single EDGAR filing."""

    ticker: str
    cik: str
    form_type: str
    accession_number: str
    significance_score: int  # clamped to 0-100 by validator
    base_score: int          # clamped to 0-100 by validator
    boosters: dict[str, int]
    alert_triggered: bool  # True when significance_score >= 60

    @field_validator("significance_score", "base_score", mode="before")
    @classmethod
    def clamp_score(cls, val: int) -> int:
        return max(0, min(100, int(val)))


class InsiderCluster(BaseModel):
    """A cluster of insider purchases detected within a time window."""

    ticker: str
    window_start: datetime
    window_end: datetime
    insiders: list[str]
    insider_count: int = Field(ge=1)
    total_value: float = Field(ge=0.0)
    includes_ceo_cfo: bool
    cluster_score: int = Field(ge=0, le=100)
    transaction_type: str = "P"  # "P" purchase, "S" sale


class EdgarAlert(BaseModel):
    """A published EDGAR alert for high-significance events."""

    alert_id: str
    ticker: str
    alert_type: str  # "filing_significance" | "insider_cluster" | "earnings_surprise"
    significance_score: int = Field(ge=0, le=100)
    summary: str
    filing_url: Optional[str] = None
    payload: dict
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    source_system: str = "edgar_monitor"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    def to_intel_envelope(self) -> dict:
        """Wrap as Intel Bus envelope (matching edgar_harvester._publish format)."""
        return {
            "value": self.model_dump(mode="json"),
            "source_system": self.source_system,
            "timestamp": time.time(),
            "confidence": self.confidence,
        }
