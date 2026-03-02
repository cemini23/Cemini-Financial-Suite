"""
ws_rover.py — WebSocket-based Kalshi market rover.

Replaces the 15-minute REST polling loop (rover.py / rover_runner.py) with a
single long-lived WebSocket connection that receives real-time market data.

Flow:
  1. REST bootstrap — one-time GET /markets to seed the active market list
  2. Connect to Kalshi WebSocket API with RSA-PSS auth
  3. Subscribe to:
       market_lifecycle_v2  (public) — market open/close discovery
       trade                (public) — fill events for OI tracking
       orderbook_delta      (private, with initial snapshot) — top markets
  4. Dispatch messages to OrderBookManager, OITracker, LiquidityDetector
  5. Publish intel:kalshi_orderbook_summary every 5 minutes

The REST API is only used for startup bootstrap; WebSocket owns everything after.
"""

import asyncio
import logging
import os
import sys
import time

import httpx

logger = logging.getLogger("kalshi.ws_rover")

# ── Repo root on sys.path (for core.intel_bus) ────────────────────────────────
_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

try:
    import redis.asyncio as _aioredis
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False

try:
    from core.intel_bus import IntelPublisher
    _INTEL_AVAILABLE = True
except ImportError:
    _INTEL_AVAILABLE = False

from modules.market_rover.rover import MarketRover, MIN_VOLUME
from modules.market_rover.ws_client import KalshiWebSocketClient
from modules.market_rover.orderbook import OrderBookManager
from modules.market_rover.oi_tracker import OITracker
from modules.market_rover.liquidity_detector import LiquidityDetector

REST_BASE = "https://api.elections.kalshi.com/trade-api/v2"
SUMMARY_INTERVAL = 300       # publish intel summary every 5 minutes
ORDERBOOK_MARKETS_MAX = 50   # subscribe order book for top-N markets by volume
TRADE_SUBSCRIBE_MAX = 200    # subscribe trade events for top-N markets


def _redis_url() -> str:
    host = os.getenv("REDIS_HOST", "redis")
    password = os.getenv("REDIS_PASSWORD", "cemini_redis_2026")
    return f"redis://:{password}@{host}:6379"


class WebSocketRover:
    """
    Main WebSocket-based market rover.

    Replaces rover_scanner's 15-minute REST polling with a single
    authenticated WebSocket connection.
    """

    def __init__(self, redis_client=None):
        # redis_client can be injected for tests; otherwise created lazily
        self._r = redis_client
        self._categorizer = MarketRover()
        self._ob_manager: OrderBookManager = None
        self._oi_tracker: OITracker = None
        self._liq_detector: LiquidityDetector = None
        self._ws_client: KalshiWebSocketClient = None
        self._active_tickers: list = []
        self._last_summary_ts = 0.0

    # ── Redis ──────────────────────────────────────────────────────────────────

    async def _redis(self):
        if self._r:
            return self._r
        if _REDIS_AVAILABLE:
            self._r = _aioredis.from_url(_redis_url(), decode_responses=True)
        return self._r

    # ── REST bootstrap ─────────────────────────────────────────────────────────

    async def bootstrap_markets(self) -> list:
        """
        One-time REST call to discover all active markets on startup.
        Populates Redis keys and returns list of tickers sorted by volume desc.
        REST is NOT used after this — WebSocket takes over.
        """
        logger.info("🚀 REST bootstrap: discovering active markets...")
        tickers_by_volume = []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                cursor = None
                for _ in range(15):  # up to 15 × 200 = 3 000 markets
                    params = {"status": "open", "limit": 200}
                    if cursor:
                        params["cursor"] = cursor

                    resp = await client.get(f"{REST_BASE}/markets", params=params)
                    if resp.status_code != 200:
                        logger.error("❌ REST bootstrap HTTP %d", resp.status_code)
                        break

                    data = resp.json()
                    markets = data.get("markets", [])
                    if not markets:
                        break

                    redis_client = await self._redis()
                    for mkt in markets:
                        ticker = mkt.get("ticker", "")
                        series = mkt.get("series_ticker", "")
                        title = mkt.get("title", "")
                        volume = int(mkt.get("volume", 0) or 0)

                        if not ticker or volume < MIN_VOLUME:
                            continue

                        category = self._categorizer._categorize(series, title)
                        if redis_client:
                            await redis_client.sadd("kalshi:markets:active", ticker)
                            await redis_client.hset(
                                "kalshi:markets:categories", ticker, category
                            )
                        tickers_by_volume.append((volume, ticker))

                    cursor = data.get("cursor")
                    if not cursor:
                        break

        except Exception as exc:
            logger.error("❌ REST bootstrap failed: %s", exc)

        tickers_by_volume.sort(reverse=True)
        result = [tk for _, tk in tickers_by_volume]
        logger.info("✅ Bootstrapped %d active markets", len(result))
        return result

    # ── Message dispatch ───────────────────────────────────────────────────────

    async def _on_message(self, msg: dict) -> None:
        """Route incoming WebSocket messages to the appropriate handler."""
        msg_type = msg.get("type", "")

        if msg_type == "orderbook_snapshot":
            ticker = msg.get("msg", {}).get("market_ticker", "")
            await self._ob_manager.apply_snapshot(msg)
            await self._liq_detector.on_orderbook_update(ticker)

        elif msg_type == "orderbook_delta":
            ticker = msg.get("msg", {}).get("market_ticker", "")
            ok = await self._ob_manager.apply_delta(msg)
            if not ok:
                # Sequence gap — re-subscribe to get a fresh snapshot
                logger.info("🔄 Seq gap on %s — re-subscribing", ticker)
                await self._ws_client.subscribe(
                    ["orderbook_delta"], [ticker], send_initial_snapshot=True
                )
            else:
                await self._liq_detector.on_orderbook_update(ticker)

        elif msg_type == "trade":
            await self._oi_tracker.process_trade(msg)

        elif msg_type == "market_lifecycle_v2":
            await self._handle_lifecycle(msg)

        # Periodic summary (non-blocking task so it doesn't stall the recv loop)
        now = time.time()
        if now - self._last_summary_ts >= SUMMARY_INTERVAL:
            self._last_summary_ts = now
            asyncio.create_task(self._publish_summary())

    async def _handle_lifecycle(self, msg: dict) -> None:
        """Update Redis market registry when markets open or close."""
        inner = msg.get("msg", {})
        ticker = inner.get("market_ticker") or inner.get("ticker", "")
        status = inner.get("status", "")
        redis_client = await self._redis()

        if not redis_client or not ticker:
            return

        if status == "open":
            await redis_client.sadd("kalshi:markets:active", ticker)
            logger.debug("📋 Market opened: %s", ticker)
        elif status in ("closed", "settled"):
            await redis_client.srem("kalshi:markets:active", ticker)
            logger.debug("📋 Market closed: %s", ticker)

    async def _publish_summary(self) -> None:
        """Publish a top-level market summary to the intel bus every 5 minutes."""
        redis_client = await self._redis()
        if not redis_client or not _INTEL_AVAILABLE:
            return
        try:
            active = await redis_client.smembers("kalshi:markets:active")
            categories = await redis_client.hgetall("kalshi:markets:categories")
            cat_counts: dict = {}
            for cat in categories.values():
                cat_counts[cat] = cat_counts.get(cat, 0) + 1

            payload = {
                "active_markets":     len(active),
                "category_breakdown": cat_counts,
                "orderbook_tickers":  self._active_tickers[:ORDERBOOK_MARKETS_MAX],
                "timestamp":          time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            await IntelPublisher.publish_async(
                "intel:kalshi_orderbook_summary", payload, "WebSocketRover"
            )
        except Exception as exc:
            logger.warning("⚠️  Summary publish failed: %s", exc)

    # ── Main entry point ───────────────────────────────────────────────────────

    async def start(self) -> None:
        """Bootstrap markets, connect WebSocket, run forever."""
        logger.info("🌐 Kalshi WebSocket Rover starting...")

        redis_client = await self._redis()
        self._ob_manager = OrderBookManager(redis_client)
        self._oi_tracker = OITracker(redis_client)
        self._liq_detector = LiquidityDetector(redis_client, self._ob_manager)

        # Seed market list via REST (one-time)
        self._active_tickers = await self.bootstrap_markets()

        # Build the WebSocket client
        self._ws_client = KalshiWebSocketClient(on_message=self._on_message)

        async def on_connected(client: KalshiWebSocketClient) -> None:
            # Market lifecycle — public, no market_ticker needed
            await client.subscribe(["market_lifecycle_v2"])

            # Trade events — public, subscribe to top markets for OI tracking
            if self._active_tickers:
                batch = self._active_tickers[:TRADE_SUBSCRIBE_MAX]
                await client.subscribe(["trade"], market_tickers=batch)

            # Order book — private, top-N markets for liquidity detection
            for ticker in self._active_tickers[:ORDERBOOK_MARKETS_MAX]:
                await client.subscribe(
                    ["orderbook_delta"], [ticker], send_initial_snapshot=True
                )

        try:
            await self._ws_client.run(on_connected=on_connected)
        except KeyboardInterrupt:
            logger.info("🛑 Rover stopped by keyboard interrupt")
        finally:
            self._ws_client.stop()
            if self._r and hasattr(self._r, "aclose"):
                await self._r.aclose()
