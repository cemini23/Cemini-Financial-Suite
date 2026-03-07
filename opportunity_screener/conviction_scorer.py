"""
opportunity_screener/conviction_scorer.py — Sequential Bayesian Conviction Scorer (Step 26.1c)

Formula:
    prior_odds        = prior / (1 - prior)
    likelihood_ratio  = source_weight * extraction_confidence * recency_factor * convergence_bonus
    posterior_odds    = prior_odds * likelihood_ratio
    conviction        = posterior_odds / (1 + posterior_odds)

Conviction is clamped to [0.01, 0.99] to prevent log(0) numerical issues.
State is stored in Redis hash `discovery:convictions`.
"""

import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Optional

from beartype import beartype

from opportunity_screener.config import (
    CORE_WATCHLIST,
    SCREENER_CONVERGENCE_MULTIPLIER,
    SCREENER_CONVERGENCE_WINDOW_MINUTES,
    SCREENER_DECAY_RATE,
)

logger = logging.getLogger("screener.conviction")

# ── Source weight map ─────────────────────────────────────────────────────────
SOURCE_WEIGHTS: dict[str, float] = {
    "intel:playbook_snapshot": 1.5,
    "intel:geo_risk_score": 1.3,
    "intel:btc_sentiment": 1.2,
    "intel:fed_bias": 1.2,
    "intel:spy_trend": 1.1,
    "intel:vix_level": 1.1,
    "intel:weather_edge": 0.9,
    "intel:kalshi_oi": 1.0,
    "intel:kalshi_liquidity_spike": 1.0,
    "intel:social_score": 0.8,
    "intel:portfolio_heat": 0.9,
    "intel:btc_volume_spike": 1.0,
    "intel:kalshi_rewards": 0.3,
}
_DEFAULT_SOURCE_WEIGHT = 0.7

# Recency decay thresholds (seconds)
_1H = 3600
_6H = 21600
_24H = 86400


def _recency_factor(age_seconds: float) -> float:
    """Return recency multiplier based on message age."""
    if age_seconds <= _1H:
        return 1.0
    if age_seconds <= _6H:
        return 0.8
    if age_seconds <= _24H:
        return 0.5
    return 0.2


def _clamp(v: float) -> float:
    return max(0.01, min(0.99, v))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConvictionState:
    """
    In-memory conviction store with optional Redis persistence.

    Redis layout:
      discovery:convictions   — hash, field={ticker}, value=JSON(conviction state)
      discovery:source_times  — hash, field="{ticker}:{channel}", value=epoch float
    """

    def __init__(self, redis_client=None):
        # ticker → {conviction, last_updated, source_count, sources, first_seen}
        self._state: dict[str, dict[str, Any]] = {}
        # ticker → channel → list[epoch float] for convergence detection
        self._source_times: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        self._redis = redis_client

    # ── State access ──────────────────────────────────────────────────────────

    @beartype
    def get_conviction(self, ticker: str) -> float:
        """Return current conviction for ticker. New tickers start at 0.5 (flat prior)."""
        return self._state.get(ticker, {}).get("conviction", 0.5)

    @beartype
    def get_state(self, ticker: str) -> Optional[dict]:
        return self._state.get(ticker)

    @beartype
    def all_tickers(self) -> list[str]:
        return list(self._state.keys())

    # ── Core Bayesian update ──────────────────────────────────────────────────

    @beartype
    def update(
        self,
        ticker: str,
        source_channel: str,
        extraction_confidence: float,
        message_timestamp: float,
    ) -> tuple[float, float, float]:
        """
        Apply one Bayesian update for ticker given a new intel mention.

        Returns (conviction_before, conviction_after, likelihood_ratio).
        """
        prior = self.get_conviction(ticker)
        before = prior
        now = time.time()

        # 1. Source weight
        sw = SOURCE_WEIGHTS.get(source_channel, _DEFAULT_SOURCE_WEIGHT)

        # 2. Recency decay
        age = max(0.0, now - message_timestamp)
        rf = _recency_factor(age)

        # 3. Multi-source convergence bonus
        cb = self._convergence_bonus(ticker, source_channel, now)

        # 4. Likelihood ratio
        lr = sw * extraction_confidence * rf * cb

        # 5. Bayesian update (odds form)
        prior_odds = prior / (1.0 - prior)
        posterior_odds = prior_odds * lr
        posterior = posterior_odds / (1.0 + posterior_odds)
        conviction = _clamp(posterior)

        # 6. Update state
        existing = self._state.get(ticker, {})
        sources = existing.get("sources", [])
        if source_channel not in sources:
            sources = sources + [source_channel]

        self._state[ticker] = {
            "conviction": conviction,
            "last_updated": _now_iso(),
            "source_count": existing.get("source_count", 0) + 1,
            "sources": sources[:20],  # cap stored source list
            "first_seen": existing.get("first_seen", _now_iso()),
        }

        # 7. Record time for convergence detection
        self._source_times[ticker][source_channel].append(now)

        # 8. Persist to Redis (best-effort)
        self._persist_ticker(ticker)

        logger.debug(
            "Bayesian update %s: %.3f→%.3f via %s (lr=%.3f sw=%.2f rf=%.2f cb=%.2f)",
            ticker, before, conviction, source_channel, lr, sw, rf, cb,
        )
        return before, conviction, lr

    def _convergence_bonus(self, ticker: str, channel: str, now: float) -> float:
        """Return convergence multiplier if 2+ distinct channels mentioned ticker recently."""
        window = SCREENER_CONVERGENCE_WINDOW_MINUTES * 60
        cutoff = now - window
        seen_channels = set()
        for ch, times in self._source_times[ticker].items():
            # purge old entries
            fresh = [t for t in times if t >= cutoff]
            self._source_times[ticker][ch] = fresh
            if fresh:
                seen_channels.add(ch)
        # Count distinct channels INCLUDING the current one
        seen_channels.add(channel)
        if len(seen_channels) >= 2:
            return SCREENER_CONVERGENCE_MULTIPLIER
        return 1.0

    # ── Decay ─────────────────────────────────────────────────────────────────

    @beartype
    def decay_all(self) -> list[tuple[str, float, float]]:
        """
        Apply per-tick conviction decay to all non-core tickers.
        Returns list of (ticker, before, after) for tickers that changed.
        """
        changes = []
        rate = SCREENER_DECAY_RATE
        for ticker in list(self._state.keys()):
            if ticker in CORE_WATCHLIST:
                continue
            before = self._state[ticker]["conviction"]
            after = _clamp(before * rate)
            if abs(after - before) > 1e-6:
                self._state[ticker]["conviction"] = after
                self._state[ticker]["last_updated"] = _now_iso()
                self._persist_ticker(ticker)
                changes.append((ticker, before, after))
        return changes

    # ── Redis persistence ─────────────────────────────────────────────────────

    def _persist_ticker(self, ticker: str) -> None:
        """Best-effort write to Redis. Silently skips if no Redis."""
        if self._redis is None:
            return
        try:
            payload = json.dumps(self._state[ticker])
            self._redis.hset("discovery:convictions", ticker, payload)
            self._redis.expire("discovery:convictions", 172800)  # 48h TTL
        except Exception as exc:
            logger.debug("Redis persist failed for %s: %s", ticker, exc)

    @beartype
    def load_from_redis(self) -> int:
        """Reload state from Redis on startup. Returns count of tickers loaded."""
        if self._redis is None:
            return 0
        try:
            raw = self._redis.hgetall("discovery:convictions")
            count = 0
            for ticker, payload in (raw or {}).items():
                try:
                    self._state[ticker] = json.loads(payload)
                    count += 1
                except Exception:
                    pass
            logger.info("Loaded %d conviction records from Redis", count)
            return count
        except Exception as exc:
            logger.warning("Failed to load convictions from Redis: %s", exc)
            return 0
