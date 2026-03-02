"""
oi_tracker.py — Open Interest change tracker via Kalshi trade events.

The public 'trade' WebSocket channel emits a message for every fill.
Cumulative trade volume is used as a proxy for gross OI growth.
A 1-hour rolling window tracks recent activity.

Signal published to intel:kalshi_oi when 1h change > 2% of lifetime total:
  {
    "market":       "BTCX-24-01-01",
    "oi":           12345,
    "oi_1h_change": +500,
    "oi_pct_change": 4.2,
    "signal":       "RISING_CONVICTION"
  }

Redis state:
  kalshi:oi:{ticker}         hash   {total_contracts, updated_at}
  kalshi:oi:{ticker}:window  list   JSON [{count, ts}, ...]  — rolling 1h entries
"""

import json
import logging
import os
import sys
import time
from typing import Optional

logger = logging.getLogger("kalshi.oi_tracker")

# Intel bus — optional; injected in tests via publisher= kwarg
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

try:
    from core.intel_bus import IntelPublisher as _IntelPublisher
    _DEFAULT_PUBLISHER = _IntelPublisher
except ImportError:
    _DEFAULT_PUBLISHER = None

OI_SIGNAL_THRESHOLD = 0.02   # 2% of lifetime volume triggers a signal
ROLLING_WINDOW_SEC = 3600    # 1-hour rolling window
REDIS_TTL = 7200             # 2-hour TTL on window lists


class OITracker:
    """
    Tracks per-market trade volume as a proxy for open interest changes.

    Args:
        redis_client: async Redis client (redis.asyncio or FakeRedis for tests)
        publisher:    optional IntelPublisher replacement (for unit tests)
    """

    def __init__(self, redis_client, publisher=None):
        self._r = redis_client
        self._pub = publisher if publisher is not None else _DEFAULT_PUBLISHER

    async def process_trade(self, msg: dict) -> None:
        """
        Ingest a trade WebSocket message and update OI tracking state.
        Publishes a conviction signal if the 1h change crosses the threshold.
        """
        inner = msg.get("msg", {})
        ticker = inner.get("market_ticker", "")
        count = int(inner.get("count", 0))
        now = time.time()

        if not ticker or count <= 0:
            return

        oi_key = f"kalshi:oi:{ticker}"
        window_key = f"kalshi:oi:{ticker}:window"

        # Update cumulative total
        existing = await self._r.hgetall(oi_key)
        prev_total = int(existing.get("total_contracts") or 0)
        total = prev_total + count

        await self._r.hset(oi_key, mapping={
            "total_contracts": str(total),
            "updated_at":      str(now),
        })

        # Append this trade to the rolling window
        entry = json.dumps({"count": count, "ts": now})
        await self._r.lpush(window_key, entry)
        await self._r.expire(window_key, REDIS_TTL)

        await self._maybe_publish(ticker, total, window_key, now)

    async def _maybe_publish(
        self, ticker: str, total: int, window_key: str, now: float
    ) -> None:
        """Compute 1h rolling change and publish if it crosses the signal threshold."""
        if total == 0:
            return

        cutoff = now - ROLLING_WINDOW_SEC
        all_entries = await self._r.lrange(window_key, 0, -1)

        oi_1h_change = 0
        for raw in all_entries:
            try:
                entry = json.loads(raw)
                if entry["ts"] >= cutoff:
                    oi_1h_change += entry["count"]
            except (json.JSONDecodeError, KeyError):
                continue

        pct_change = (oi_1h_change / total) * 100.0

        if abs(pct_change) < OI_SIGNAL_THRESHOLD * 100:
            return

        signal = "RISING_CONVICTION" if oi_1h_change > 0 else "FALLING_CONVICTION"
        payload = {
            "market":        ticker,
            "oi":            total,
            "oi_1h_change":  oi_1h_change,
            "oi_pct_change": round(pct_change, 2),
            "signal":        signal,
        }

        logger.info(
            "📊 OI signal [%s] %s: +%d contracts (%.1f%%)",
            signal, ticker, oi_1h_change, pct_change,
        )

        if self._pub:
            await self._pub.publish_async(
                "intel:kalshi_oi", payload, "OITracker", confidence=0.7
            )

    def get_signal(self, total: int, oi_1h_change: int) -> Optional[str]:
        """
        Pure helper: return signal string for given totals, or None if below threshold.
        Used by tests to verify threshold logic without async calls.
        """
        if total == 0:
            return None
        pct = (oi_1h_change / total) * 100.0
        if abs(pct) < OI_SIGNAL_THRESHOLD * 100:
            return None
        return "RISING_CONVICTION" if oi_1h_change > 0 else "FALLING_CONVICTION"
