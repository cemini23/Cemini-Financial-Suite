"""
liquidity_detector.py — Sudden order book depth anomaly detection.

After each orderbook update, total depth (sum of all contracts at all price levels)
is computed for each side. A rolling 60-minute window of measurements tracks
the mean and standard deviation of depth. Alerts when depth deviates >2σ.

Signal published to intel:kalshi_liquidity_spike:
  {
    "market":       "BTCX-24-01-01",
    "side":         "yes",
    "depth_change": +5000.0,
    "sigma":        3.2,
    "timestamp":    "2026-03-02T12:00:00Z"
  }

Redis state:
  kalshi:liq:{ticker}:yes_hist  list  JSON [{depth, ts}, ...]
  kalshi:liq:{ticker}:no_hist   list  JSON [{depth, ts}, ...]
"""

import json
import logging
import math
import os
import sys
import time

logger = logging.getLogger("kalshi.liquidity_detector")

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

try:
    from core.intel_bus import IntelPublisher as _IntelPublisher
    _DEFAULT_PUBLISHER = _IntelPublisher
except ImportError:
    _DEFAULT_PUBLISHER = None

ROLLING_WINDOW_SEC = 3600   # 60-minute history window
MIN_SAMPLES = 10            # minimum samples before alerting
SIGMA_THRESHOLD = 2.0       # alert when deviation exceeds 2σ
REDIS_TTL = 7200            # 2-hour TTL on history lists


class LiquidityDetector:
    """
    Monitors total order book depth per market and alerts on sudden spikes or drains.

    Args:
        redis_client:     async Redis client
        orderbook_manager: OrderBookManager used to read current depth
        publisher:        optional IntelPublisher replacement (for unit tests)
    """

    def __init__(self, redis_client, orderbook_manager, publisher=None):
        self._r = redis_client
        self._ob = orderbook_manager
        self._pub = publisher if publisher is not None else _DEFAULT_PUBLISHER

    async def on_orderbook_update(self, ticker: str) -> None:
        """
        Entry point — called after every orderbook snapshot or delta for `ticker`.
        Checks both yes and no sides for depth anomalies.
        """
        for side in ("yes", "no"):
            await self._check_side(ticker, side)

    async def _check_side(self, ticker: str, side: str) -> None:
        """Compute depth, compare to rolling stats, publish if spike detected."""
        depth = await self._ob.get_total_depth(ticker, side)
        now = time.time()
        cutoff = now - ROLLING_WINDOW_SEC
        hist_key = f"kalshi:liq:{ticker}:{side}_hist"

        # Load recent history (within the rolling window)
        all_raw = await self._r.lrange(hist_key, 0, -1)
        history = []
        for raw in all_raw:
            try:
                entry = json.loads(raw)
                if entry["ts"] >= cutoff:
                    history.append(float(entry["depth"]))
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

        # Record current measurement
        await self._r.lpush(hist_key, json.dumps({"depth": depth, "ts": now}))
        await self._r.expire(hist_key, REDIS_TTL)

        if len(history) < MIN_SAMPLES:
            return  # not enough history to establish baseline

        mean = sum(history) / len(history)
        variance = sum((val - mean) ** 2 for val in history) / len(history)
        stddev = math.sqrt(variance) if variance > 0 else 0.0

        if stddev == 0.0:
            return

        sigma = (depth - mean) / stddev

        if abs(sigma) <= SIGMA_THRESHOLD:
            return

        depth_change = depth - mean
        payload = {
            "market":       ticker,
            "side":         side,
            "depth_change": round(depth_change, 2),
            "sigma":        round(sigma, 2),
            "timestamp":    time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        }

        logger.warning(
            "💧 Liquidity spike [%s] %s-side: depth=%.0f mean=%.0f sigma=%.2f",
            ticker, side, depth, mean, sigma,
        )

        if self._pub:
            await self._pub.publish_async(
                "intel:kalshi_liquidity_spike", payload,
                "LiquidityDetector", confidence=0.8,
            )

    @staticmethod
    def compute_sigma(history: list, current_depth: float) -> float:
        """
        Pure helper: compute how many standard deviations `current_depth` is
        from the mean of `history`. Returns 0.0 if stddev is zero.
        Used by tests to verify the detection logic directly.
        """
        if not history:
            return 0.0
        mean = sum(history) / len(history)
        variance = sum((val - mean) ** 2 for val in history) / len(history)
        stddev = math.sqrt(variance) if variance > 0 else 0.0
        if stddev == 0.0:
            return 0.0
        return (current_depth - mean) / stddev
