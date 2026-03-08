"""Vector intelligence contracts — Step 29h.

Models for the pgvector intelligence layer:
  EmbeddingRecord          — content to be embedded and stored
  SimilarityResult         — one result from a vector similarity search
  SimilarityWithMarketResult — SimilarityResult + market state JOIN
  GradedContext            — CRAG-graded retrieved document
  RetrievalResult          — full CRAG retrieval output
  VectorStoreStats         — get_stats() return type
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class EmbeddingRecord(BaseModel):
    """One record to be embedded and stored in intel_embeddings."""

    model_config = ConfigDict(extra="allow")

    content: str
    source_type: str
    source_id: Optional[str] = None
    source_channel: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    tickers: list[str] = Field(default_factory=list)
    timestamp: Optional[datetime] = None


class SimilarityResult(BaseModel):
    """One result from a pgvector cosine similarity search."""

    model_config = ConfigDict(extra="allow")

    id: int
    content: str
    source_type: str
    source_id: Optional[str] = None
    source_channel: Optional[str] = None
    similarity_score: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    tickers: list[str] = Field(default_factory=list)
    timestamp: Optional[datetime] = None


class MarketState(BaseModel):
    """Snapshot of market state at the time a piece of intel was published."""

    model_config = ConfigDict(extra="allow")

    close: Optional[float] = None
    volume: Optional[float] = None
    rsi: Optional[float] = None
    ticker: Optional[str] = None


class SimilarityWithMarketResult(SimilarityResult):
    """SimilarityResult enriched with the market state at intel publish time.

    This is the killer query: pgvector + TimescaleDB JOIN in a single statement.
    No standalone vector DB can do this.
    """

    market_state: Optional[MarketState] = None


class GradedContext(BaseModel):
    """A retrieved document graded for relevance by the CRAG retriever."""

    model_config = ConfigDict(extra="allow")

    content: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    grade: Literal["RELEVANT", "AMBIGUOUS", "IRRELEVANT"]
    source_type: str
    source_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    tickers: list[str] = Field(default_factory=list)
    timestamp: Optional[datetime] = None


class RetrievalResult(BaseModel):
    """Full output of the CRAG retriever — contexts ready for LLM injection."""

    model_config = ConfigDict(extra="allow")

    contexts: list[GradedContext] = Field(default_factory=list)
    total_retrieved: int = 0
    total_relevant: int = 0
    retrieval_quality: Literal["high", "mixed", "insufficient"] = "insufficient"


class VectorStoreStats(BaseModel):
    """Stats snapshot from intelligence.vector_store.get_stats()."""

    model_config = ConfigDict(extra="allow")

    total_embeddings: int = 0
    by_source_type: dict[str, int] = Field(default_factory=dict)
    oldest: Optional[str] = None
    newest: Optional[str] = None
    avg_per_day: float = 0.0
