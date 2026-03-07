"""
opportunity_screener/watchlist_manager.py — Dynamic 50-Ticker Watchlist (Step 26.1d)

Redis layout:
  discovery:watchlist              — sorted set, score=conviction, member=ticker
  discovery:watchlist_meta:{ticker}— hash: promoted_at, last_intel_at, source_channels, promotion_reason
  intel:watchlist_update           — published on every promotion/demotion/eviction

Rules:
  - 50 dynamic slots + 6 core tickers (SPY, QQQ, IWM, DIA, BTC-USD, ETH-USD)
  - Core tickers never evicted, don't count against cap
  - Promotion: conviction ≥ 0.65
  - Demotion: conviction < 0.45 OR stale > 72h with no new intel
  - Eviction (cap full): new ticker conviction must exceed lowest by ≥ 0.05
"""
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

from beartype import beartype

from cemini_contracts.discovery import WatchlistUpdate
from opportunity_screener.config import (
    CORE_WATCHLIST,
    SCREENER_DEMOTION_THRESHOLD,
    SCREENER_EVICTION_HYSTERESIS,
    SCREENER_MAX_DYNAMIC_TICKERS,
    SCREENER_PROMOTION_THRESHOLD,
    SCREENER_STALE_TTL_HOURS,
)

logger = logging.getLogger("screener.watchlist")

_WATCHLIST_KEY = "discovery:watchlist"
_META_PREFIX = "discovery:watchlist_meta:"
_UPDATE_CHANNEL = "intel:watchlist_update"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_epoch() -> float:
    return time.time()


class WatchlistManager:
    """
    Manages the dynamic 50-slot watchlist with Redis persistence.
    All Redis operations are best-effort — caller is responsible for connection.
    """

    def __init__(self, redis_client=None):
        self._redis = redis_client
        # In-memory shadow for fast path decisions (avoids Redis RTT per message)
        self._dynamic: dict[str, dict[str, Any]] = {}  # ticker → meta
        self._core: set[str] = set(CORE_WATCHLIST)

    # ── Read ──────────────────────────────────────────────────────────────────

    @beartype
    def is_watched(self, ticker: str) -> bool:
        return ticker in self._core or ticker in self._dynamic

    @beartype
    def dynamic_count(self) -> int:
        return len(self._dynamic)

    @beartype
    def get_watchlist(self) -> list[dict[str, Any]]:
        """Return full watchlist sorted by conviction descending."""
        result = []
        # Core tickers
        for t in self._core:
            result.append({"ticker": t, "is_core": True, "conviction": 0.5})
        # Dynamic tickers
        for t, meta in self._dynamic.items():
            result.append({
                "ticker": t,
                "is_core": False,
                "conviction": meta.get("conviction", 0.5),
                "promoted_at": meta.get("promoted_at"),
                "last_intel_at": meta.get("last_intel_at"),
                "source_channels": meta.get("source_channels", []),
                "promotion_reason": meta.get("promotion_reason", ""),
            })
        result.sort(key=lambda x: x.get("conviction", 0), reverse=True)
        return result

    @beartype
    def get_size(self) -> int:
        return len(self._core) + len(self._dynamic)

    # ── Promotion / Demotion ──────────────────────────────────────────────────

    @beartype
    def evaluate(
        self,
        ticker: str,
        conviction: float,
        source_channel: str,
        reason: str = "",
    ) -> Optional[str]:
        """
        Evaluate ticker for promotion/demotion based on current conviction.

        Returns action taken: "promoted", "demoted", "evicted", or None.
        """
        if ticker in self._core:
            self._update_core_intel_time(ticker, source_channel)
            return None

        currently_watched = ticker in self._dynamic

        # Demotion check
        if currently_watched and conviction < SCREENER_DEMOTION_THRESHOLD:
            self._demote(ticker, conviction, "conviction_floor")
            return "demoted"

        # Already watched → update conviction + last_intel_at
        if currently_watched:
            self._update_dynamic(ticker, conviction, source_channel)
            return None

        # Promotion check
        if conviction >= SCREENER_PROMOTION_THRESHOLD:
            if len(self._dynamic) < SCREENER_MAX_DYNAMIC_TICKERS:
                self._promote(ticker, conviction, source_channel, reason or "threshold_crossed")
                return "promoted"
            else:
                # Cap reached → eviction check
                lowest_ticker, lowest_conviction = self._find_lowest_dynamic()
                if lowest_ticker and conviction >= lowest_conviction + SCREENER_EVICTION_HYSTERESIS:
                    self._evict(lowest_ticker, lowest_conviction, f"evicted_for_{ticker}")
                    self._promote(ticker, conviction, source_channel, "eviction_promotion")
                    return "promoted"

        return None

    def _promote(self, ticker: str, conviction: float, channel: str, reason: str) -> None:
        now = _now_epoch()
        meta = {
            "conviction": conviction,
            "promoted_at": now,
            "last_intel_at": now,
            "source_channels": [channel],
            "promotion_reason": reason,
        }
        self._dynamic[ticker] = meta
        self._redis_zset_add(ticker, conviction)
        self._redis_meta_set(ticker, meta)
        self._publish_update("promoted", ticker, conviction, reason)
        logger.info("PROMOTED %s (conviction=%.3f via %s)", ticker, conviction, channel)

    def _demote(self, ticker: str, conviction: float, reason: str) -> None:
        self._dynamic.pop(ticker, None)
        self._redis_zset_remove(ticker)
        self._redis_meta_delete(ticker)
        self._publish_update("demoted", ticker, conviction, reason)
        logger.info("DEMOTED %s (conviction=%.3f reason=%s)", ticker, conviction, reason)

    def _evict(self, ticker: str, conviction: float, reason: str) -> None:
        self._dynamic.pop(ticker, None)
        self._redis_zset_remove(ticker)
        self._redis_meta_delete(ticker)
        self._publish_update("evicted", ticker, conviction, reason)
        logger.info("EVICTED %s (conviction=%.3f reason=%s)", ticker, conviction, reason)

    def _update_dynamic(self, ticker: str, conviction: float, channel: str) -> None:
        meta = self._dynamic[ticker]
        meta["conviction"] = conviction
        meta["last_intel_at"] = _now_epoch()
        channels = meta.get("source_channels", [])
        if channel not in channels:
            channels.append(channel)
            meta["source_channels"] = channels
        self._redis_zset_add(ticker, conviction)
        self._redis_meta_set(ticker, meta)

    def _update_core_intel_time(self, ticker: str, channel: str) -> None:
        """Track last intel time for core tickers (no promotion logic needed)."""
        pass

    def _find_lowest_dynamic(self) -> tuple[Optional[str], float]:
        """Return (ticker, conviction) of the lowest-conviction dynamic ticker."""
        if not self._dynamic:
            return None, 0.0
        t = min(self._dynamic.items(), key=lambda x: x[1].get("conviction", 0))
        return t[0], t[1].get("conviction", 0.0)

    # ── Stale TTL enforcement ─────────────────────────────────────────────────

    @beartype
    def enforce_stale_ttl(self) -> list[str]:
        """Force-demote tickers with no intel in SCREENER_STALE_TTL_HOURS. Returns demoted list."""
        ttl_seconds = SCREENER_STALE_TTL_HOURS * 3600
        now = _now_epoch()
        demoted = []
        for ticker in list(self._dynamic.keys()):
            last = self._dynamic[ticker].get("last_intel_at", 0)
            if now - last > ttl_seconds:
                conviction = self._dynamic[ticker].get("conviction", 0.0)
                self._demote(ticker, conviction, "stale_ttl")
                demoted.append(ticker)
        return demoted

    # ── Redis ops ─────────────────────────────────────────────────────────────

    def _redis_zset_add(self, ticker: str, score: float) -> None:
        if self._redis is None:
            return
        try:
            self._redis.zadd(_WATCHLIST_KEY, {ticker: score})
        except Exception as exc:
            logger.debug("Redis zadd failed for %s: %s", ticker, exc)

    def _redis_zset_remove(self, ticker: str) -> None:
        if self._redis is None:
            return
        try:
            self._redis.zrem(_WATCHLIST_KEY, ticker)
        except Exception as exc:
            logger.debug("Redis zrem failed for %s: %s", ticker, exc)

    def _redis_meta_set(self, ticker: str, meta: dict) -> None:
        if self._redis is None:
            return
        try:
            key = f"{_META_PREFIX}{ticker}"
            self._redis.hset(key, mapping={k: json.dumps(v) for k, v in meta.items()})
            self._redis.expire(key, 345600)  # 96h TTL
        except Exception as exc:
            logger.debug("Redis meta_set failed for %s: %s", ticker, exc)

    def _redis_meta_delete(self, ticker: str) -> None:
        if self._redis is None:
            return
        try:
            self._redis.delete(f"{_META_PREFIX}{ticker}")
        except Exception as exc:
            logger.debug("Redis meta_delete failed for %s: %s", ticker, exc)

    def _publish_update(self, action: str, ticker: str, conviction: float, reason: str) -> None:
        if self._redis is None:
            return
        try:
            update = WatchlistUpdate(
                action=action, ticker=ticker, conviction=conviction, reason=reason
            )
            payload = json.dumps({
                "value": update.model_dump(),
                "source_system": "opportunity_screener",
                "timestamp": _now_epoch(),
                "confidence": 1.0,
            })
            self._redis.set(_UPDATE_CHANNEL, payload, ex=300)
        except Exception as exc:
            logger.debug("Redis watchlist_update publish failed: %s", exc)

    @beartype
    def load_from_redis(self) -> int:
        """Reload dynamic watchlist from Redis sorted set on startup."""
        if self._redis is None:
            return 0
        try:
            members = self._redis.zrangebyscore(
                _WATCHLIST_KEY, "-inf", "+inf", withscores=True
            )
            count = 0
            for ticker, score in (members or []):
                if ticker in self._core:
                    continue
                meta_raw = self._redis.hgetall(f"{_META_PREFIX}{ticker}") or {}
                meta = {
                    "conviction": score,
                    "promoted_at": float(json.loads(meta_raw.get("promoted_at", "0") or "0")),
                    "last_intel_at": float(json.loads(meta_raw.get("last_intel_at", "0") or "0")),
                    "source_channels": json.loads(meta_raw.get("source_channels", "[]") or "[]"),
                    "promotion_reason": json.loads(meta_raw.get("promotion_reason", '""') or '""'),
                }
                self._dynamic[ticker] = meta
                count += 1
            logger.info("Loaded %d dynamic watchlist entries from Redis", count)
            return count
        except Exception as exc:
            logger.warning("Failed to load watchlist from Redis: %s", exc)
            return 0
