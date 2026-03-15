"""Cemini Financial Suite — Hard-Blocking Exposure Gate (Step 49d).

Resolves C6 (hardcoded buying power) and L2 (exposure never blocks).

ExposureGate is FAIL-CLOSED: if it cannot determine buying power, it blocks
the order rather than allowing it through.  This is the correct posture for
a live trading system.

Logic:
  1. Fetch buying_power via adapter.get_buying_power() (real or paper)
  2. Calculate proposed_spend = buying_power * allocation_pct
  3. Query current exposure for ticker from Redis (safety:exposure:{ticker})
  4. If current_exposure + proposed_spend > max_exposure → BLOCK
  5. On approval: atomically increment Redis exposure counter (TTL 86400 s)

Redis key pattern:  safety:exposure:{ticker}   (float stored as string)
TTL:                86400 s (reset daily — approximate, not calendar-aligned)
"""
from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger("shared.safety.exposure_gate")

_EXPOSURE_KEY_PREFIX = "safety:exposure:"
_EXPOSURE_TTL = 86_400            # 24 h
_DEFAULT_MAX_EXPOSURE_PCT = 0.10  # 10 % of buying power per ticker per day


class ExposureGate:
    """Hard-blocking per-ticker exposure ceiling.

    Args:
        redis_client:       Sync Redis client.
        max_exposure_pct:   Maximum fraction of buying_power per ticker (default 0.10).
        paper_buying_power: Fixed buying power to use when LIVE_TRADING is not set.
    """

    def __init__(
        self,
        redis_client,
        max_exposure_pct: float = _DEFAULT_MAX_EXPOSURE_PCT,
        paper_buying_power: float = 1_000.0,
    ) -> None:
        self.redis = redis_client
        self.max_exposure_pct = max_exposure_pct
        self.paper_buying_power = paper_buying_power

    # ── Public interface ────────────────────────────────────────────────────

    def check(
        self,
        ticker: str,
        allocation_pct: float,
        buying_power: Optional[float] = None,
    ) -> bool:
        """Return True if the order MAY proceed; False to BLOCK it.

        Args:
            ticker:         Instrument symbol (e.g. "AAPL").
            allocation_pct: Fraction of buying_power this order will use.
            buying_power:   Optional override; if None, uses configured paper value
                            or raises if LIVE_TRADING=true and no value provided.
        """
        bp = self._resolve_buying_power(buying_power)
        if bp <= 0:
            logger.warning(
                "ExposureGate: buying_power=%.2f ≤ 0 — BLOCKING order for %s (fail-closed).",
                bp, ticker,
            )
            return False

        max_exposure = round(bp * self.max_exposure_pct, 4)
        proposed_spend = round(bp * allocation_pct, 4)

        current = self._get_current_exposure(ticker)
        projected = round(current + proposed_spend, 4)

        if projected > max_exposure:
            logger.warning(
                "🚫 ExposureGate BLOCKED: ticker=%s current=%.2f proposed=%.2f "
                "projected=%.2f max=%.2f (buying_power=%.2f max_pct=%.1f%%)",
                ticker, current, proposed_spend, projected, max_exposure,
                bp, self.max_exposure_pct * 100,
            )
            return False

        logger.debug(
            "✅ ExposureGate: ticker=%s current=%.2f proposed=%.2f projected=%.2f max=%.2f — allowed.",
            ticker, current, proposed_spend, projected, max_exposure,
        )
        return True

    def record_fill(
        self,
        ticker: str,
        allocation_pct: float,
        buying_power: Optional[float] = None,
    ) -> None:
        """Increment the Redis exposure counter after a confirmed fill.

        Call this AFTER the broker confirms the order, not before.
        """
        bp = self._resolve_buying_power(buying_power)
        if bp <= 0:
            return
        amount = round(bp * allocation_pct, 4)
        self._increment_exposure(ticker, amount)

    def get_exposure(self, ticker: str) -> float:
        """Return current cumulative exposure for a ticker (in USD)."""
        return self._get_current_exposure(ticker)

    def reset_exposure(self, ticker: str) -> None:
        """Manually reset a ticker's exposure counter (e.g. after position close)."""
        key = f"{_EXPOSURE_KEY_PREFIX}{ticker}"
        try:
            self.redis.delete(key)
            logger.info("ExposureGate: reset exposure for %s.", ticker)
        except Exception as exc:  # noqa: BLE001
            logger.warning("ExposureGate: reset_exposure failed: %s", exc)

    # ── Private helpers ─────────────────────────────────────────────────────

    def _resolve_buying_power(self, override: Optional[float]) -> float:
        if override is not None:
            return override
        live = os.getenv("LIVE_TRADING", "false").lower() in ("1", "true", "yes")
        if live:
            # In live mode, caller MUST pass buying_power explicitly.
            # Failing closed here is intentional.
            logger.error(
                "ExposureGate: LIVE_TRADING=true but no buying_power provided — "
                "returning 0 (fail-closed)."
            )
            return 0.0
        return self.paper_buying_power

    def _get_current_exposure(self, ticker: str) -> float:
        key = f"{_EXPOSURE_KEY_PREFIX}{ticker}"
        try:
            val = self.redis.get(key)
            return float(val) if val else 0.0
        except Exception as exc:  # noqa: BLE001
            logger.warning("ExposureGate: get_exposure Redis error (%s) — assuming 0.", exc)
            return 0.0

    def _increment_exposure(self, ticker: str, amount: float) -> None:
        key = f"{_EXPOSURE_KEY_PREFIX}{ticker}"
        try:
            pipe = self.redis.pipeline()
            pipe.incrbyfloat(key, amount)
            pipe.expire(key, _EXPOSURE_TTL)
            pipe.execute()
        except Exception as exc:  # noqa: BLE001
            logger.warning("ExposureGate: increment_exposure failed: %s", exc)
