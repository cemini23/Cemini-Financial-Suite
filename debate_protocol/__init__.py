"""Cemini Financial Suite — Devil's Advocate Debate Protocol (Step 47).

5-agent debate: Macro, Bull, Bear, Risk (Devil's Advocate), Trader.
Redis Shared Blackboard. Deterministic regime-weighted tie-breaking.
Full audit trail via Step 43 hash chain.

No LLM required — all agents use rule-based deterministic logic.
LLM integration is a future drop-in upgrade to the agent execute() methods.

Public API:
    from debate_protocol.state_machine import run_debate
    verdict = await run_debate("AAPL", redis_client=rdb)

    from debate_protocol.tie_breaker import resolve
    action, multiplier, tie_break = resolve(0.65, 0.60, "GREEN")
"""
from debate_protocol.models import (
    AgentArgument,
    AgentRole,
    CrossExamination,
    DebatePhase,
    DebateState,
    DebateVerdict,
    DebateVerdictIntel,
    Rebuttal,
)
from debate_protocol.state_machine import run_debate
from debate_protocol.tie_breaker import resolve

__all__ = [
    "run_debate",
    "resolve",
    "AgentArgument",
    "AgentRole",
    "CrossExamination",
    "DebatePhase",
    "DebateState",
    "DebateVerdict",
    "DebateVerdictIntel",
    "Rebuttal",
]
