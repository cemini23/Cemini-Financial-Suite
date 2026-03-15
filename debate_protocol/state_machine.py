"""Cemini Financial Suite — Debate State Machine (Step 47).

Orchestrates the 5-phase Devil's Advocate debate for a single ticker.

Phases:
  1. GATHERING      — Macro Agent reads Intel Bus, sets macro context + regime
  2. ARGUING        — Bull + Bear write their arguments to the blackboard
  3. CROSS_EXAMINING — Risk Agent challenges both sides, generates CrossExamination objects
  4. REBUTTING      — Bull + Bear respond to challenges
  5. DECIDING       — Trader Agent synthesizes a final DebateVerdict

The debate state lives on the Redis Shared Blackboard throughout.
All phases fail silently — if Redis is unavailable, state is managed in-memory.

Public API:
    result = await run_debate("AAPL", redis_client=rdb, db_conn=pg, sync_redis=rdb_sync)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from debate_protocol.agents.bear_agent import BearAgent
from debate_protocol.agents.bull_agent import BullAgent
from debate_protocol.agents.macro_agent import MacroAgent
from debate_protocol.agents.risk_agent import RiskAgent
from debate_protocol.agents.trader_agent import TraderAgent
from debate_protocol.blackboard import Blackboard
from debate_protocol.debate_logger import log_debate
from debate_protocol.models import AgentRole, DebatePhase, DebateState, DebateVerdict

logger = logging.getLogger("debate_protocol.state_machine")


def _new_uuid() -> str:
    try:
        from uuid_utils import uuid7
        return str(uuid7())
    except ImportError:
        import uuid
        return str(uuid.uuid4())


async def run_debate(
    ticker: str,
    redis_client=None,
    db_conn=None,
    sync_redis=None,
) -> DebateVerdict:
    """Execute a full Devil's Advocate debate for a ticker.

    Args:
        ticker:       Stock ticker symbol.
        redis_client: Async redis.asyncio.Redis client for the blackboard.
        db_conn:      Optional psycopg2 connection for Postgres logging.
        sync_redis:   Optional synchronous redis.Redis for Intel Bus reads in agents
                      and for publishing intel:debate_verdict.

    Returns:
        DebateVerdict with final action, scores, and reasoning.
    """
    session_id = _new_uuid()
    logger.info("Debate started: session=%s ticker=%s", session_id, ticker)

    # ── Initialise blackboard ──────────────────────────────────────────────────
    blackboard = Blackboard(redis_client, session_id)

    state = DebateState(
        session_id=session_id,
        ticker=ticker,
        started_at=datetime.now(tz=timezone.utc),
    )

    try:
        # ── Phase 1: GATHERING ──────────────────────────────────────────────────
        state.phase = DebatePhase.GATHERING
        await blackboard.write_state(state)

        macro = MacroAgent(AgentRole.MACRO, blackboard, redis_client=sync_redis)
        macro_arg = await macro.execute(state)
        state = await blackboard.add_argument(state, macro_arg)

        # Propagate regime from macro context to top-level state
        regime_from_ctx = macro_arg.evidence.get("regime", "YELLOW")
        state.regime = regime_from_ctx
        state.macro_context = macro_arg.evidence
        await blackboard.write_state(state)

        # ── Phase 2: ARGUING ───────────────────────────────────────────────────
        state = await blackboard.set_phase(state, DebatePhase.ARGUING)

        bull = BullAgent(AgentRole.BULL, blackboard)
        bear = BearAgent(AgentRole.BEAR, blackboard)

        bull_arg = await bull.execute(state)
        bear_arg = await bear.execute(state)

        state = await blackboard.add_argument(state, bull_arg)
        state = await blackboard.add_argument(state, bear_arg)

        # ── Phase 3: CROSS_EXAMINING ───────────────────────────────────────────
        state = await blackboard.set_phase(state, DebatePhase.CROSS_EXAMINING)

        risk = RiskAgent(AgentRole.RISK, blackboard)
        risk_arg = await risk.execute(state)
        state = await blackboard.add_argument(state, risk_arg)

        challenges = risk.generate_challenges(state)
        for challenge in challenges:
            state = await blackboard.add_cross_examination(state, challenge)

        # ── Phase 4: REBUTTING ─────────────────────────────────────────────────
        state = await blackboard.set_phase(state, DebatePhase.REBUTTING)

        for challenge in state.cross_examinations:
            if challenge.target_agent == AgentRole.BULL:
                rebuttal = await bull.rebut(state, challenge)
                state = await blackboard.add_rebuttal(state, rebuttal)
            elif challenge.target_agent == AgentRole.BEAR:
                rebuttal = await bear.rebut(state, challenge)
                state = await blackboard.add_rebuttal(state, rebuttal)

        # ── Phase 5: DECIDING ──────────────────────────────────────────────────
        state = await blackboard.set_phase(state, DebatePhase.DECIDING)

        trader = TraderAgent(AgentRole.TRADER, blackboard)
        verdict = await trader.synthesize(state)

        state = await blackboard.set_verdict(state, verdict)
        state.completed_at = datetime.now(tz=timezone.utc)
        await blackboard.write_state(state)

        # ── Log complete debate ────────────────────────────────────────────────
        log_debate(state, conn=db_conn, redis_client=sync_redis)

        logger.info(
            "Debate complete: session=%s ticker=%s action=%s confidence=%.2f",
            session_id, ticker, verdict.action, verdict.confidence,
        )
        return verdict

    except Exception as exc:  # noqa: BLE001
        logger.error("Debate failed: session=%s ticker=%s error=%s", session_id, ticker, exc)
        state.error = str(exc)
        state.completed_at = datetime.now(tz=timezone.utc)
        await blackboard.write_state(state)
        # Return safe default: NO_ACTION
        return DebateVerdict(
            action="NO_ACTION",
            ticker=ticker,
            confidence=0.0,
            bull_score=0.0,
            bear_score=0.0,
            regime=state.regime or "YELLOW",
            regime_multiplier_applied=False,
            tie_break_used=False,
            reasoning=f"Debate failed with error: {exc}",
            risk_notes="Error state — do not trade.",
        )
