"""Cemini Financial Suite — State Hydration (Step 49c).

Solves the L1 "fresh_start_pending" issue: on service restart, the engine
previously came up with an empty executed_trades dict, potentially re-executing
already-filled orders.

StateHydrator provides a single hydrate() call that:
  1. Loads executed_trades from Redis (quantos:executed_trades)
  2. Loads active positions from Redis (quantos:active_positions)
  3. Returns a HydratedState dataclass consumed by TradingEngine.initialize()

Key contracts:
  - Fail-silent: any Redis/JSON error returns empty HydratedState
  - All callers MUST check .loaded before trusting the data
  - TTL on executed_trades key: 86400 s (24 h)  [set by engine on each trade]
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("shared.safety.state_hydrator")

_EXECUTED_TRADES_KEY = "quantos:executed_trades"
_ACTIVE_POSITIONS_KEY = "quantos:active_positions"


@dataclass
class HydratedState:
    """Container returned by StateHydrator.hydrate()."""

    executed_trades: dict[str, Any] = field(default_factory=dict)
    active_positions: list[dict] = field(default_factory=list)
    loaded: bool = False  # True only when Redis data was successfully read

    @property
    def trade_count(self) -> int:
        return len(self.executed_trades)

    @property
    def position_count(self) -> int:
        return len(self.active_positions)


class StateHydrator:
    """Hydrates QuantOS engine state from Redis on service restart.

    Args:
        redis_client: A sync ``redis.Redis`` client.
    """

    def __init__(self, redis_client) -> None:
        self.redis = redis_client

    def hydrate(self) -> HydratedState:
        """Load executed_trades and active_positions from Redis.

        Returns a HydratedState with loaded=True if any data was found,
        loaded=False if Redis was unavailable or keys were absent.
        """
        state = HydratedState()

        try:
            trades_raw = self.redis.get(_EXECUTED_TRADES_KEY)
            if trades_raw:
                state.executed_trades = json.loads(trades_raw)
                logger.info(
                    "📦 StateHydrator: loaded %d executed trades from Redis.",
                    len(state.executed_trades),
                )

            positions_raw = self.redis.get(_ACTIVE_POSITIONS_KEY)
            if positions_raw:
                loaded = json.loads(positions_raw)
                # Accept both dict (keyed by ticker) and list formats
                if isinstance(loaded, dict):
                    state.active_positions = list(loaded.values())
                elif isinstance(loaded, list):
                    state.active_positions = loaded
                logger.info(
                    "📦 StateHydrator: loaded %d active positions from Redis.",
                    len(state.active_positions),
                )

            state.loaded = bool(trades_raw or positions_raw)

        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "StateHydrator: Redis read failed (%s) — starting with empty state.", exc
            )

        return state

    def persist_trades(self, executed_trades: dict, ttl: int = 86_400) -> None:
        """Write executed_trades back to Redis (call after each new trade)."""
        try:
            self.redis.set(_EXECUTED_TRADES_KEY, json.dumps(executed_trades), ex=ttl)
        except Exception as exc:  # noqa: BLE001
            logger.warning("StateHydrator: persist_trades failed: %s", exc)

    def persist_positions(self, positions: list[dict] | dict, ttl: int = 3_600) -> None:
        """Write active positions to Redis (call after position changes)."""
        try:
            payload = positions if isinstance(positions, list) else list(positions.values())
            self.redis.set(_ACTIVE_POSITIONS_KEY, json.dumps(payload), ex=ttl)
        except Exception as exc:  # noqa: BLE001
            logger.warning("StateHydrator: persist_positions failed: %s", exc)
