"""Cemini Financial Suite — Devil's Advocate Debate Protocol Models (Step 47).

All Pydantic v2 models for the debate state machine.
No LLM dependencies — fully deterministic and auditable.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class DebatePhase(str, Enum):
    GATHERING = "gathering"
    ARGUING = "arguing"
    CROSS_EXAMINING = "cross_examining"
    REBUTTING = "rebutting"
    DECIDING = "deciding"
    COMPLETE = "complete"


class AgentRole(str, Enum):
    MACRO = "macro"
    BULL = "bull"
    BEAR = "bear"
    RISK = "risk"
    TRADER = "trader"


class AgentArgument(BaseModel):
    """One agent's position in the debate."""

    agent: AgentRole
    phase: DebatePhase
    position: str  # "bullish" | "bearish" | "neutral" | "assessment"
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    evidence: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class CrossExamination(BaseModel):
    """Risk agent's challenge targeting a specific argument."""

    target_agent: AgentRole
    vulnerability: str
    severity: float = Field(ge=0.0, le=1.0)
    challenge_question: str


class Rebuttal(BaseModel):
    """Agent's response to a cross-examination challenge."""

    agent: AgentRole
    original_argument_id: str  # agent role string used as ID
    challenge_addressed: str
    rebuttal_text: str
    confidence_after_rebuttal: float = Field(ge=0.0, le=1.0)


class DebateVerdict(BaseModel):
    """Final synthesized decision from the Trader agent."""

    action: Literal["BUY", "SELL", "HOLD", "NO_ACTION"]
    ticker: str
    confidence: float = Field(ge=0.0, le=1.0)
    bull_score: float = Field(ge=0.0)
    bear_score: float = Field(ge=0.0)
    regime: str  # GREEN | YELLOW | RED
    regime_multiplier_applied: bool
    tie_break_used: bool
    reasoning: str
    risk_notes: str = ""


class DebateState(BaseModel):
    """Full mutable state of a single debate session.

    Stored on the Redis Shared Blackboard for the duration of the debate.
    """

    session_id: str
    ticker: str
    phase: DebatePhase = DebatePhase.GATHERING
    regime: str = "YELLOW"
    macro_context: dict = Field(default_factory=dict)
    arguments: list[AgentArgument] = Field(default_factory=list)
    cross_examinations: list[CrossExamination] = Field(default_factory=list)
    rebuttals: list[Rebuttal] = Field(default_factory=list)
    verdict: Optional[DebateVerdict] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def get_arguments_by_role(self, role: AgentRole) -> list[AgentArgument]:
        return [arg for arg in self.arguments if arg.agent == role]

    def get_argument_by_role(self, role: AgentRole) -> Optional[AgentArgument]:
        args = self.get_arguments_by_role(role)
        return args[-1] if args else None


class DebateVerdictIntel(BaseModel):
    """Slim summary published to intel:debate_verdict (Intel Bus envelope value)."""

    session_id: str
    ticker: str
    action: str
    confidence: float
    regime: str
    bull_score: float
    bear_score: float
    tie_break_used: bool
    summary: str
    published_at: float = Field(default_factory=time.time)
