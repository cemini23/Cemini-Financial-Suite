"""Cemini Financial Suite — Debate Agent Base Class (Step 47).

All agents are deterministic by default. The LLM integration hook is prepared
but requires no LLM installation — agents override execute() with rule-based logic.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from debate_protocol.blackboard import Blackboard
from debate_protocol.models import AgentArgument, AgentRole, CrossExamination, DebateState, Rebuttal


class BaseAgent(ABC):
    """Abstract base for all debate agents.

    Subclasses must implement ``execute()`` and ``rebut()``.
    All methods are async to support future parallel execution.
    All methods should fail gracefully and never raise to the caller.
    """

    def __init__(self, role: AgentRole, blackboard: Blackboard) -> None:
        self.role = role
        self.blackboard = blackboard
        self.logger = logging.getLogger(f"debate_protocol.agents.{role.value}")

    @abstractmethod
    async def execute(self, state: DebateState) -> AgentArgument:
        """Produce an argument based on current blackboard state."""

    @abstractmethod
    async def rebut(self, state: DebateState, challenge: CrossExamination) -> Rebuttal:
        """Respond to a cross-examination challenge targeting this agent."""

    def _safe_float(self, value, default: float = 0.0) -> float:
        """Convert a value to float safely, returning default on failure."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _read_intel_value(self, intel_data: dict | None, field: str | None = None):
        """Extract value from an Intel Bus envelope dict.

        Intel envelope schema: {"value": ..., "source_system": ..., "timestamp": ..., "confidence": ...}
        """
        if intel_data is None:
            return None
        val = intel_data.get("value")
        if field and isinstance(val, dict):
            return val.get(field)
        return val
