"""Cemini Financial Suite — Redis Shared Blackboard (Step 47).

All debate agents read/write through this blackboard — no direct agent-to-agent
communication. State is stored as a JSON string in a Redis key with a 1-hour TTL.

Key pattern: debate:{session_id}
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from debate_protocol.config import BLACKBOARD_TTL
from debate_protocol.models import (
    AgentArgument,
    CrossExamination,
    DebatePhase,
    DebateState,
    DebateVerdict,
    Rebuttal,
)

logger = logging.getLogger("debate_protocol.blackboard")


class Blackboard:
    """Redis Shared Blackboard for a single debate session.

    Uses a single Redis STRING key (not HSET) for simplicity and atomic
    read-modify-write via optimistic locking.  Full DebateState is serialized
    as JSON on every write.

    Args:
        redis_client: A redis.asyncio.Redis client (or compatible mock).
        session_id:   UUIDv7 string identifying this debate.
        ttl:          Key TTL in seconds (default 3600 = 1 hour).
    """

    def __init__(self, redis_client, session_id: str, ttl: int = BLACKBOARD_TTL) -> None:
        self.redis = redis_client
        self.session_id = session_id
        self.key = f"debate:{session_id}"
        self.ttl = ttl

    async def write_state(self, state: DebateState) -> None:
        """Serialize full DebateState to Redis and refresh TTL."""
        try:
            await self.redis.set(self.key, state.model_dump_json(), ex=self.ttl)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Blackboard write failed (%s): %s", self.key, exc)

    async def read_state(self) -> Optional[DebateState]:
        """Deserialize DebateState from Redis. Returns None on miss/error."""
        try:
            raw = await self.redis.get(self.key)
            if raw is None:
                return None
            return DebateState.model_validate_json(raw)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Blackboard read failed (%s): %s", self.key, exc)
            return None

    async def add_argument(self, state: DebateState, arg: AgentArgument) -> DebateState:
        """Append an argument to state and persist. Returns updated state."""
        state.arguments.append(arg)
        await self.write_state(state)
        return state

    async def add_cross_examination(self, state: DebateState, cx: CrossExamination) -> DebateState:
        """Append a cross-examination and persist."""
        state.cross_examinations.append(cx)
        await self.write_state(state)
        return state

    async def add_rebuttal(self, state: DebateState, rebuttal: Rebuttal) -> DebateState:
        """Append a rebuttal and persist."""
        state.rebuttals.append(rebuttal)
        await self.write_state(state)
        return state

    async def set_phase(self, state: DebateState, phase: DebatePhase) -> DebateState:
        """Advance debate phase and persist."""
        state.phase = phase
        await self.write_state(state)
        return state

    async def set_verdict(self, state: DebateState, verdict: DebateVerdict) -> DebateState:
        """Set final verdict, mark phase COMPLETE, and persist."""
        state.verdict = verdict
        state.phase = DebatePhase.COMPLETE
        await self.write_state(state)
        return state

    async def delete(self) -> None:
        """Explicitly remove debate key (optional cleanup)."""
        try:
            await self.redis.delete(self.key)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Blackboard delete failed: %s", exc)
