"""Cemini Financial Suite — Cryptographic Order Idempotency (Step 49a).

Every live order gets a deterministic idempotency key derived from the
signal's immutable fields (ticker + action + confidence + allocation + ts_bucket).
The key is written to Redis via SET NX with a 24-hour TTL.

  * First call  → key absent → order proceeds → key stored → returns True
  * Repeat call → key present → order is a duplicate → returns False

This prevents double-execution caused by network retries, service restarts,
or Redis Streams at-least-once delivery.

Key pattern:  idempotency:order:{sha256(canonical_str)[:16]}
TTL:          86400 s (24 h)
"""
from __future__ import annotations

import hashlib
import logging
import math
import os
import time
from typing import Optional

logger = logging.getLogger("shared.safety.idempotency")

_DEFAULT_TTL = 86_400          # 24 h
_BUCKET_GRANULARITY = 60       # seconds — rounds timestamp to 1-minute bucket


def _canonical(ticker: str, action: str, confidence: float,
                allocation_pct: float, ts_bucket: int) -> str:
    """Deterministic string representation of an order intent."""
    conf = round(confidence, 4)
    alloc = round(allocation_pct, 4)
    return f"{ticker}|{action}|{conf}|{alloc}|{ts_bucket}"


def make_idempotency_key(
    ticker: str,
    action: str,
    confidence: float,
    allocation_pct: float,
    timestamp: Optional[float] = None,
) -> str:
    """Return the Redis key for this order intent.

    The timestamp is bucketed to *_BUCKET_GRANULARITY* seconds so that
    rapid retries within the same minute share the same key.
    """
    ts = timestamp if timestamp is not None else time.time()
    bucket = math.floor(ts / _BUCKET_GRANULARITY) * _BUCKET_GRANULARITY
    raw = _canonical(ticker, action, confidence, allocation_pct, bucket)
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"idempotency:order:{digest}"


class IdempotencyGuard:
    """Redis-backed idempotency guard for live order execution.

    Args:
        redis_client: A sync ``redis.Redis`` client (or compatible mock).
        ttl:          Key TTL in seconds (default 86400 = 24 h).
    """

    def __init__(self, redis_client, ttl: int = _DEFAULT_TTL) -> None:
        self.redis = redis_client
        self.ttl = ttl

    def is_duplicate(
        self,
        ticker: str,
        action: str,
        confidence: float,
        allocation_pct: float,
        timestamp: Optional[float] = None,
    ) -> bool:
        """Return True if this order has already been submitted.

        Uses SET NX (set-if-not-exists) atomically: if the key is absent the
        guard claims it and returns False (proceed).  If already present it
        returns True (duplicate — skip).
        """
        key = make_idempotency_key(ticker, action, confidence, allocation_pct, timestamp)
        try:
            # SET key "1" NX EX ttl → returns True on first set, None on duplicate
            result = self.redis.set(key, "1", nx=True, ex=self.ttl)
            if result is None:
                logger.warning(
                    "🔁 Idempotency: duplicate order blocked — ticker=%s action=%s key=%s",
                    ticker, action, key,
                )
                return True
            logger.debug("✅ Idempotency: new order accepted — key=%s", key)
            return False
        except Exception as exc:  # noqa: BLE001
            # Fail-open: if Redis is down we let the order through and log
            logger.error(
                "⚠️ Idempotency: Redis error (%s) — failing open for ticker=%s",
                exc, ticker,
            )
            return False

    def clear(
        self,
        ticker: str,
        action: str,
        confidence: float,
        allocation_pct: float,
        timestamp: Optional[float] = None,
    ) -> None:
        """Manually remove an idempotency key (e.g. after order cancellation)."""
        key = make_idempotency_key(ticker, action, confidence, allocation_pct, timestamp)
        try:
            self.redis.delete(key)
            logger.debug("🗑️ Idempotency: key cleared — %s", key)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Idempotency clear failed: %s", exc)
