"""Cemini Financial Suite — Kalshi Self-Match Prevention (Step 49g).

CFTC regulations prohibit self-matching (trading against yourself) on
regulated prediction markets.  This guard ensures the system never
simultaneously holds opposing positions on the same Kalshi market.

Mechanism:
  - When an order is sent, record the direction (YES/NO) in Redis
  - Before any new order, check for an opposing open position
  - If detected → block the order and log a CFTC warning

Redis key pattern:  safety:self_match:{market_id}   → "YES" | "NO"
TTL:                3600 s (1 hour — Kalshi positions are short-lived)

market_id examples:
  "INXD-23DEC31-B4500"  (Kalshi event ticker)
  "KXBTCD-23"           (crypto market)
"""
from __future__ import annotations

import logging
from typing import Literal, Optional

logger = logging.getLogger("shared.safety.self_match_lock")

_KEY_PREFIX = "safety:self_match:"
_LOCK_TTL = 3_600   # 1 hour

Direction = Literal["YES", "NO"]


class SelfMatchLock:
    """Prevents self-matching on Kalshi prediction markets.

    Args:
        redis_client: Sync Redis client.
        ttl:          Position lock TTL in seconds (default 3600).
    """

    def __init__(self, redis_client, ttl: int = _LOCK_TTL) -> None:
        self.redis = redis_client
        self.ttl = ttl

    # ── Public interface ────────────────────────────────────────────────────

    def check(self, market_id: str, direction: Direction) -> bool:
        """Return True if order MAY proceed; False if it would self-match.

        Args:
            market_id:  Kalshi market ticker (e.g. "INXD-23DEC31-B4500").
            direction:  "YES" or "NO" side of the market.
        """
        existing = self._get_direction(market_id)
        if existing is None:
            # No open position — safe to proceed
            return True

        if existing != direction:
            logger.warning(
                "🚫 SelfMatchLock BLOCKED: market=%s tried_direction=%s existing=%s "
                "(CFTC self-match prevention)",
                market_id, direction, existing,
            )
            return False

        # Same direction as existing position — allowed (adding to position)
        return True

    def record_open(self, market_id: str, direction: Direction) -> None:
        """Record that we have an open position in this direction.

        Call after the broker confirms the order.
        """
        key = f"{_KEY_PREFIX}{market_id}"
        try:
            self.redis.set(key, direction, ex=self.ttl)
            logger.debug(
                "SelfMatchLock: recorded open position — market=%s direction=%s",
                market_id, direction,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("SelfMatchLock: record_open failed: %s", exc)

    def record_close(self, market_id: str) -> None:
        """Remove the self-match lock after a position is closed."""
        key = f"{_KEY_PREFIX}{market_id}"
        try:
            self.redis.delete(key)
            logger.debug("SelfMatchLock: position closed — market=%s", market_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("SelfMatchLock: record_close failed: %s", exc)

    def get_open_direction(self, market_id: str) -> Optional[Direction]:
        """Return current open direction for market_id, or None."""
        return self._get_direction(market_id)

    # ── Private helpers ─────────────────────────────────────────────────────

    def _get_direction(self, market_id: str) -> Optional[Direction]:
        key = f"{_KEY_PREFIX}{market_id}"
        try:
            val = self.redis.get(key)
            if val is None:
                return None
            s = val if isinstance(val, str) else val.decode()
            return s.upper() if s.upper() in ("YES", "NO") else None  # type: ignore[return-value]
        except Exception as exc:  # noqa: BLE001
            logger.warning("SelfMatchLock: get_direction Redis error (%s) — assuming no position.", exc)
            return None
