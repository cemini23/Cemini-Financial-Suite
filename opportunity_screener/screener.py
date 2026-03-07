"""
opportunity_screener/screener.py — Core Screening Loop (Step 26.1e)

Polls all intel:* channels every SCREENER_POLL_INTERVAL_SECONDS seconds.
On each message: extract tickers → update Bayesian conviction → evaluate watchlist.

Every SCREENER_DECAY_INTERVAL_SECONDS (5 min default): decay all convictions,
enforce stale TTLs, publish intel:discovery_snapshot.

Startup: reloads conviction state and watchlist from Redis.
Shutdown: graceful flush of audit buffer.
"""
import asyncio
import json
import logging
import signal
import time
from datetime import datetime, timezone
from typing import Any, Optional

import redis

from cemini_contracts.discovery import DiscoverySnapshot
from opportunity_screener.config import (
    CORE_WATCHLIST,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
    INTEL_CHANNELS,
    REDIS_HOST,
    REDIS_PASSWORD,
    REDIS_PORT,
    SCREENER_DECAY_INTERVAL_SECONDS,
    SCREENER_POLL_INTERVAL_SECONDS,
)
from opportunity_screener.conviction_scorer import ConvictionState
from opportunity_screener.discovery_logger import DiscoveryLogger
from opportunity_screener.entity_extractor import extract_tickers
from opportunity_screener.watchlist_manager import WatchlistManager

logger = logging.getLogger("screener.core")


def _make_redis() -> redis.Redis:
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
    )


def _make_db_conn():
    """Best-effort Postgres connection. Returns None if unavailable."""
    try:
        import psycopg2
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_NAME,
            connect_timeout=5,
        )
    except Exception as exc:
        logger.warning("Postgres connection failed (audit log to JSONL only): %s", exc)
        return None


class OpportunityScreener:
    """
    Coordinates the full screening pipeline:
      1. Redis polling → entity extraction
      2. Bayesian conviction scoring
      3. Dynamic watchlist management
      4. Discovery audit logging
      5. Periodic decay + snapshot publishing
    """

    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._conviction = ConvictionState()
        self._watchlist = WatchlistManager()
        self._logger: Optional[DiscoveryLogger] = None
        self._running = False

        # Stats
        self.messages_processed: int = 0
        self.extractions_total: int = 0
        self.start_time: float = time.time()

        # State for snapshot: track conviction at last snapshot for rising/fading
        self._conviction_snapshot: dict[str, float] = {}

        # Track last value seen per channel (de-duplicate re-reads)
        self._channel_last_ts: dict[str, float] = {}

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def startup(self) -> None:
        logger.info("Connecting to Redis %s:%d", REDIS_HOST, REDIS_PORT)
        self._redis = _make_redis()
        self._conviction = ConvictionState(redis_client=self._redis)
        self._watchlist = WatchlistManager(redis_client=self._redis)

        db = _make_db_conn()
        self._logger = DiscoveryLogger(db_conn=db)

        # Reload persisted state
        loaded_convictions = self._conviction.load_from_redis()
        loaded_watchlist = self._watchlist.load_from_redis()
        logger.info(
            "Startup recovery: %d convictions, %d watchlist entries",
            loaded_convictions, loaded_watchlist,
        )

        # Seed core tickers
        for ticker in CORE_WATCHLIST:
            if ticker not in self._conviction.all_tickers():
                # Initialize conviction state for core tickers
                self._conviction._state[ticker] = {
                    "conviction": 0.5,
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "source_count": 0,
                    "sources": [],
                    "first_seen": datetime.now(timezone.utc).isoformat(),
                }

        self._running = True

    def shutdown(self) -> None:
        logger.info("Graceful shutdown: flushing audit buffer...")
        self._running = False
        if self._logger:
            self._logger.flush()
        logger.info("Shutdown complete.")

    # ── Main loops ────────────────────────────────────────────────────────────

    async def run_screening_loop(self) -> None:
        """Poll intel channels and process new messages."""
        logger.info("Screening loop started (poll every %ds)", SCREENER_POLL_INTERVAL_SECONDS)
        while self._running:
            try:
                await self._poll_channels()
            except Exception as exc:
                logger.error("Screening loop error: %s", exc)
            await asyncio.sleep(SCREENER_POLL_INTERVAL_SECONDS)

    async def run_decay_loop(self) -> None:
        """Every 5 min: decay convictions, enforce stale TTL, publish snapshot."""
        logger.info("Decay loop started (every %ds)", SCREENER_DECAY_INTERVAL_SECONDS)
        while self._running:
            await asyncio.sleep(SCREENER_DECAY_INTERVAL_SECONDS)
            try:
                await self._run_decay_cycle()
            except Exception as exc:
                logger.error("Decay loop error: %s", exc)

    # ── Channel polling ───────────────────────────────────────────────────────

    async def _poll_channels(self) -> None:
        """Read all intel channels and process any new messages."""
        if self._redis is None:
            return
        for channel in INTEL_CHANNELS:
            try:
                raw = self._redis.get(channel)
                if not raw:
                    continue
                envelope = json.loads(raw)
                msg_ts = float(envelope.get("timestamp", time.time()))

                # Skip if same timestamp as last time we saw this channel
                last_ts = self._channel_last_ts.get(channel, 0.0)
                if msg_ts <= last_ts:
                    continue
                self._channel_last_ts[channel] = msg_ts

                self._process_message(channel, envelope, msg_ts)
            except Exception as exc:
                logger.warning("Error processing channel %s: %s", channel, exc)

    def _process_message(self, channel: str, envelope: dict, msg_ts: float) -> None:
        """Process one intel message: extract tickers → score → evaluate watchlist."""
        self.messages_processed += 1
        value = envelope.get("value")
        if value is None:
            return

        tickers = extract_tickers(channel, value, msg_ts)
        if not tickers:
            return

        self.extractions_total += len(tickers)
        watchlist_size = self._watchlist.get_size()

        for et in tickers:
            try:
                before, after, lr = self._conviction.update(
                    ticker=et.symbol,
                    source_channel=channel,
                    extraction_confidence=et.confidence,
                    message_timestamp=msg_ts,
                )
                # Evaluate watchlist promotion/demotion
                action = self._watchlist.evaluate(
                    ticker=et.symbol,
                    conviction=after,
                    source_channel=channel,
                )
                # Audit log
                if self._logger:
                    is_bonus = after > before * 1.25  # heuristic for bonus indicator
                    self._logger.log(
                        ticker=et.symbol,
                        action=action or "conviction_update",
                        conviction_before=before,
                        conviction_after=after,
                        source_channel=channel,
                        extraction_confidence=et.confidence,
                        likelihood_ratio=lr,
                        multi_source_bonus=is_bonus,
                        payload={"channel": channel, "value": value},
                        watchlist_size=watchlist_size,
                    )
            except Exception as exc:
                logger.warning("Error scoring %s from %s: %s", et.symbol, channel, exc)

    # ── Decay cycle ───────────────────────────────────────────────────────────

    async def _run_decay_cycle(self) -> None:
        """Decay convictions, enforce stale TTL, publish snapshot."""
        logger.debug("Running decay cycle")

        # 1. Decay
        changes = self._conviction.decay_all()
        for ticker, before, after in changes:
            if self._logger:
                self._logger.log(
                    ticker=ticker, action="decayed",
                    conviction_before=before, conviction_after=after,
                    watchlist_size=self._watchlist.get_size(),
                )
            # Check demotion after decay
            if ticker in self._watchlist._dynamic:
                self._watchlist.evaluate(ticker, after, source_channel="decay")

        # 2. Stale TTL enforcement
        evicted = self._watchlist.enforce_stale_ttl()
        for t in evicted:
            if self._logger:
                self._logger.log(
                    ticker=t, action="evicted",
                    watchlist_size=self._watchlist.get_size(),
                )

        # 3. Flush audit log
        if self._logger:
            self._logger.flush()

        # 4. Publish snapshot
        await self._publish_snapshot()

    async def _publish_snapshot(self) -> None:
        """Compute and publish intel:discovery_snapshot."""
        if self._redis is None:
            return
        watchlist = self._watchlist.get_watchlist()
        all_tickers = self._conviction.all_tickers()
        tickers_tracked = len(all_tickers)

        # Rising: biggest conviction increase since last snapshot
        now_convictions = {t: self._conviction.get_conviction(t) for t in all_tickers}
        deltas = []
        for t, conv in now_convictions.items():
            prev = self._conviction_snapshot.get(t, 0.5)
            deltas.append((t, conv, conv - prev))
        deltas.sort(key=lambda x: x[2], reverse=True)
        rising = [{"ticker": t, "conviction": c, "delta": d} for t, c, d in deltas[:10] if d > 0]
        fading = [{"ticker": t, "conviction": c, "delta": d} for t, c, d in deltas[-5:] if d < 0]
        self._conviction_snapshot = now_convictions

        snapshot = DiscoverySnapshot(
            watchlist=watchlist,
            rising=rising,
            fading=fading,
            tickers_tracked=tickers_tracked,
            messages_processed=self.messages_processed,
        )
        payload = json.dumps({
            "value": snapshot.model_dump(),
            "source_system": "opportunity_screener",
            "timestamp": time.time(),
            "confidence": 1.0,
        })
        try:
            self._redis.set("intel:discovery_snapshot", payload, ex=600)
            logger.info(
                "Snapshot: watchlist=%d tracked=%d processed=%d",
                len(watchlist), tickers_tracked, self.messages_processed,
            )
        except Exception as exc:
            logger.warning("Snapshot publish failed: %s", exc)

    # ── API helpers ───────────────────────────────────────────────────────────

    def get_stats(self) -> dict[str, Any]:
        uptime = time.time() - self.start_time
        return {
            "messages_processed": self.messages_processed,
            "extractions_total": self.extractions_total,
            "tickers_tracked": len(self._conviction.all_tickers()),
            "watchlist_size": self._watchlist.get_size(),
            "dynamic_slots_used": self._watchlist.dynamic_count(),
            "uptime_seconds": round(uptime, 1),
            "msgs_per_minute": round(self.messages_processed / (uptime / 60 + 1e-9), 2),
        }
