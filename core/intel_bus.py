"""
Cemini Financial Suite — Shared Intelligence Bus

Redis-backed signal exchange between QuantOS and Kalshi modules.
Both systems run in the same Docker network sharing the same Redis instance.

Keys
----
intel:btc_sentiment    float -1 to 1         SatoshiAnalyzer
intel:btc_volume_spike dict {detected, mult}  CloudSignalEngine
intel:fed_bias         dict {bias, conf}      PowellAnalyzer
intel:social_score     dict {score, ticker}   SocialAnalyzer
intel:weather_edge     dict {city: edge_pct}  WeatherAnalyzer
intel:vix_level        float                  analyzer.py
intel:spy_trend        str bullish/bearish/neutral  analyzer.py
intel:portfolio_heat   float 0-1              analyzer.py

Payload schema
--------------
{
    "value":         <mixed>,
    "source_system": <str>,
    "timestamp":     <float epoch>,
    "confidence":    <float 0-1>
}

TTL: 300 s — stale signals auto-expire.

Import paths
------------
Root scripts  (analyzer.py):             from core.intel_bus import ...
QuantOS files (QuantOS/core/engine.py):  sys.path.append(repo_root) then same
Kalshi files  (Kalshi by Cemini/...):    sys.path.append(repo_root) then same
"""

import json
import logging
import os
import time

logger = logging.getLogger("intel_bus")

INTEL_TTL = 300  # 5 minutes — stale signals auto-expire

try:
    import redis
    import redis.asyncio as _aioredis
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False
    logger.warning("[IntelBus] redis package not found — bus disabled")


def _redis_url() -> str:
    host = os.getenv("REDIS_HOST", "redis")
    password = os.getenv("REDIS_PASSWORD", "cemini_redis_2026")
    return f"redis://:{password}@{host}:6379"


def _sync_client():
    host = os.getenv("REDIS_HOST", "redis")
    password = os.getenv("REDIS_PASSWORD", "cemini_redis_2026")
    return redis.Redis(
        host=host, port=6379, password=password,
        decode_responses=True, socket_connect_timeout=2
    )


class IntelPublisher:
    """
    Writes signals to the Intel Bus.
    All methods fail silently — never raises, never blocks the caller.
    """

    @staticmethod
    def publish(key: str, value, source_system: str, confidence: float = 1.0) -> None:
        """Synchronous publish. Use from threads and sync scripts (analyzer.py, bq_signals.py)."""
        if not _REDIS_AVAILABLE:
            return
        payload = json.dumps({
            "value": value,
            "source_system": source_system,
            "timestamp": time.time(),
            "confidence": confidence,
        })
        try:
            r = _sync_client()
            r.set(key, payload, ex=INTEL_TTL)
            r.close()
        except Exception as e:
            logger.debug(f"[IntelBus] publish failed ({key}): {e}")

    @staticmethod
    async def publish_async(key: str, value, source_system: str, confidence: float = 1.0) -> None:
        """Async publish. Use from coroutines (all async analyzers)."""
        if not _REDIS_AVAILABLE:
            return
        payload = json.dumps({
            "value": value,
            "source_system": source_system,
            "timestamp": time.time(),
            "confidence": confidence,
        })
        try:
            r = _aioredis.from_url(
                _redis_url(), decode_responses=True, socket_connect_timeout=2
            )
            try:
                await r.set(key, payload, ex=INTEL_TTL)
            finally:
                await r.aclose()
        except Exception as e:
            logger.debug(f"[IntelBus] publish_async failed ({key}): {e}")


class IntelReader:
    """
    Reads signals from the Intel Bus.
    Always returns None on any failure — callers must treat None as "no bus signal".
    """

    @staticmethod
    def read(key: str):
        """
        Synchronous read. Returns the full payload dict or None.
        Example: {"value": 0.72, "source_system": "SatoshiAnalyzer",
                  "timestamp": 1740000000.0, "confidence": 0.9}
        """
        if not _REDIS_AVAILABLE:
            return None
        try:
            r = _sync_client()
            try:
                raw = r.get(key)
            finally:
                r.close()
            return json.loads(raw) if raw else None
        except Exception as e:
            logger.debug(f"[IntelBus] read failed ({key}): {e}")
            return None

    @staticmethod
    async def read_async(key: str):
        """
        Async read. Returns the full payload dict or None.
        Example: {"value": "bearish", "source_system": "analyzer",
                  "timestamp": 1740000000.0, "confidence": 0.7}
        """
        if not _REDIS_AVAILABLE:
            return None
        try:
            r = _aioredis.from_url(
                _redis_url(), decode_responses=True, socket_connect_timeout=2
            )
            try:
                raw = await r.get(key)
            finally:
                await r.aclose()
            return json.loads(raw) if raw else None
        except Exception as e:
            logger.debug(f"[IntelBus] read_async failed ({key}): {e}")
            return None
