"""Cemini Financial Suite — Resilience Metrics (Step 48).

Tracks per-service counters and publishes a JSON snapshot to
intel:resilience_metrics every 60 seconds.

Counters tracked:
- circuit_breaker_opens   — times a circuit breaker went OPEN
- retry_attempts          — total retry attempts (not initial calls)
- dead_letters_total      — payloads routed to intel_dead_letters
- cache_hits              — hishel cache HITs
- cache_misses            — hishel cache MISSes
"""
from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from collections import defaultdict
from typing import Any

logger = logging.getLogger("cemini.resilience_metrics")

# ── Metric store ──────────────────────────────────────────────────────────────

_lock = threading.Lock()
_counters: dict[str, dict[str, int]] = defaultdict(
    lambda: {
        "circuit_breaker_opens": 0,
        "retry_attempts": 0,
        "dead_letters_total": 0,
        "cache_hits": 0,
        "cache_misses": 0,
    }
)


def increment(service_name: str, metric: str, by: int = 1) -> None:
    """Increment a counter for *service_name*."""
    with _lock:
        _counters[service_name][metric] += by


def get_snapshot() -> dict:
    """Return a deep copy of all counters as a plain dict."""
    with _lock:
        return {svc: dict(counts) for svc, counts in _counters.items()}


def reset() -> None:
    """Reset all counters (useful in tests)."""
    with _lock:
        _counters.clear()


# ── Convenience wrappers used by harvesters ───────────────────────────────────

def record_circuit_open(service_name: str) -> None:
    increment(service_name, "circuit_breaker_opens")


def record_retry(service_name: str) -> None:
    increment(service_name, "retry_attempts")


def record_dead_letter(service_name: str) -> None:
    increment(service_name, "dead_letters_total")


def record_cache_hit(service_name: str) -> None:
    increment(service_name, "cache_hits")


def record_cache_miss(service_name: str) -> None:
    increment(service_name, "cache_misses")


# ── Publisher ─────────────────────────────────────────────────────────────────

def publish_snapshot(redis_client: Any) -> None:
    """Publish current metrics snapshot to intel:resilience_metrics (sync)."""
    try:
        snapshot = get_snapshot()
        payload = json.dumps({
            "metrics": snapshot,
            "published_at": time.time(),
        })
        redis_client.set("intel:resilience_metrics", payload, ex=120)
        logger.debug("Resilience metrics published: %d services", len(snapshot))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Resilience metrics publish failed: %s", exc)


async def publish_snapshot_async(redis_client: Any) -> None:
    """Publish current metrics snapshot to intel:resilience_metrics (async)."""
    try:
        snapshot = get_snapshot()
        payload = json.dumps({
            "metrics": snapshot,
            "published_at": time.time(),
        })
        await redis_client.set("intel:resilience_metrics", payload, ex=120)
        logger.debug("Resilience metrics published: %d services", len(snapshot))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Resilience metrics publish failed: %s", exc)


async def run_metrics_publisher(redis_client: Any, interval: int = 60) -> None:
    """Async task: publish metrics every *interval* seconds indefinitely."""
    logger.info("Resilience metrics publisher started (interval=%ds)", interval)
    while True:
        await publish_snapshot_async(redis_client)
        await asyncio.sleep(interval)
