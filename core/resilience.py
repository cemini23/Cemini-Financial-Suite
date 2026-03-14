"""Cemini Financial Suite — Shared Resilience Module (Step 48).

Provides:
- create_resilient_client()       → hishel-cached httpx.AsyncClient (async harvesters)
- create_resilient_sync_client()  → hishel-cached httpx.Client (sync harvesters)
- create_circuit_breaker()        → aiobreaker.CircuitBreaker (async)
- SyncCircuitBreaker              → thread-safe sync circuit breaker
- create_retry_decorator()        → tenacity retry (sync)
- create_async_retry_decorator()  → tenacity retry (async)
- create_scheduler()              → APScheduler AsyncIOScheduler
- add_harvester_job()             → register interval job
- dead_letter()                   → write failed payloads to intel_dead_letters
"""
from __future__ import annotations

import datetime
import json
import logging
import os
import threading
import time
from typing import Any, Optional

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

try:
    import aiobreaker as _aiobreaker
    _AIOBREAKER_AVAILABLE = True
except ImportError:  # pragma: no cover
    _AIOBREAKER_AVAILABLE = False

try:
    from hishel._async_httpx import AsyncCacheClient
    from hishel._sync_httpx import SyncCacheClient
    from hishel import AsyncSqliteStorage, SyncSqliteStorage
    _HISHEL_AVAILABLE = True
except ImportError:  # pragma: no cover
    _HISHEL_AVAILABLE = False

logger = logging.getLogger("cemini.resilience")


# ── 2a: Hishel HTTP caching client factories ──────────────────────────────────

def create_resilient_client(
    service_name: str,
    cache_ttl: int = 300,
    timeout: float = 30.0,
) -> httpx.AsyncClient:
    """Return an hishel-cached httpx.AsyncClient for async harvesters.

    Cache stored in /tmp/hishel_cache/{service_name}/cache.db (SQLite).
    Falls back to plain httpx.AsyncClient if hishel is unavailable.
    """
    cache_dir = f"/tmp/hishel_cache/{service_name}"  # noqa: S108 — intentional per-service HTTP cache dir
    os.makedirs(cache_dir, exist_ok=True)
    db_path = os.path.join(cache_dir, "cache.db")

    if _HISHEL_AVAILABLE:
        storage = AsyncSqliteStorage(database_path=db_path, default_ttl=float(cache_ttl))
        return AsyncCacheClient(storage=storage, timeout=timeout)

    return httpx.AsyncClient(timeout=timeout)  # pragma: no cover


def create_resilient_sync_client(
    service_name: str,
    cache_ttl: int = 300,
    timeout: float = 30.0,
) -> httpx.Client:
    """Return an hishel-cached httpx.Client for sync harvesters.

    Cache stored in /tmp/hishel_cache/{service_name}/cache.db (SQLite).
    Falls back to plain httpx.Client if hishel is unavailable.
    """
    cache_dir = f"/tmp/hishel_cache/{service_name}"  # noqa: S108 — intentional per-service HTTP cache dir
    os.makedirs(cache_dir, exist_ok=True)
    db_path = os.path.join(cache_dir, "cache.db")

    if _HISHEL_AVAILABLE:
        storage = SyncSqliteStorage(database_path=db_path, default_ttl=float(cache_ttl))
        return SyncCacheClient(storage=storage, timeout=timeout)

    return httpx.Client(timeout=timeout)  # pragma: no cover


# ── 2b: Circuit breakers ──────────────────────────────────────────────────────

class _RedisStateListener:
    """Publishes circuit state changes to intel:circuit_breaker (optional)."""

    def __init__(self, service_name: str, redis_client: Any = None) -> None:
        self._service_name = service_name
        self._redis = redis_client

    def state_change(self, cb: Any, old_state: Any, new_state: Any) -> None:  # noqa: ARG002
        new_name = type(new_state).__name__
        logger.warning(
            "Circuit breaker [%s]: %s → %s",
            self._service_name,
            type(old_state).__name__,
            new_name,
        )
        if self._redis:
            try:
                payload = json.dumps({
                    "service": self._service_name,
                    "state": new_name,
                    "ts": datetime.datetime.utcnow().isoformat(),
                })
                self._redis.set("intel:circuit_breaker", payload, ex=300)
            except Exception:  # noqa: BLE001
                pass

    # aiobreaker calls these; no-op defaults keep the listener interface happy
    def before_call(self, cb: Any, func: Any, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        pass

    def success(self, cb: Any) -> None:  # noqa: ARG002
        pass

    def failure(self, cb: Any, exc: BaseException) -> None:  # noqa: ARG002
        pass


if _AIOBREAKER_AVAILABLE:
    class _AioListener(_aiobreaker.CircuitBreakerListener, _RedisStateListener):
        def __init__(self, service_name: str, redis_client: Any = None) -> None:
            _aiobreaker.CircuitBreakerListener.__init__(self)
            _RedisStateListener.__init__(self, service_name, redis_client)

        def state_change(self, cb: Any, old_state: Any, new_state: Any) -> None:
            _RedisStateListener.state_change(self, cb, old_state, new_state)


def create_circuit_breaker(
    service_name: str,
    fail_max: int = 3,
    timeout_duration: float = 60.0,
    redis_client: Any = None,
) -> Any:
    """Return an aiobreaker.CircuitBreaker for async harvesters.

    When open: logs WARNING and raises CircuitBreakerError.
    State changes published to intel:circuit_breaker Redis key.
    """
    if not _AIOBREAKER_AVAILABLE:  # pragma: no cover
        raise ImportError("aiobreaker is required for create_circuit_breaker()")

    listener = _AioListener(service_name, redis_client)
    return _aiobreaker.CircuitBreaker(
        fail_max=fail_max,
        timeout_duration=datetime.timedelta(seconds=timeout_duration),
        listeners=[listener],
        name=service_name,
    )


class SyncCircuitBreaker:
    """Thread-safe sync circuit breaker for sync harvesters.

    States: CLOSED → OPEN (after fail_max failures) → HALF_OPEN (after timeout) → CLOSED/OPEN

    Usage::

        cb = SyncCircuitBreaker("polygon")
        result = cb.call(my_api_func, arg1, arg2)  # returns None if OPEN
    """

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(
        self,
        service_name: str,
        fail_max: int = 3,
        timeout_duration: float = 60.0,
        redis_client: Any = None,
    ) -> None:
        self._service_name = service_name
        self._fail_max = fail_max
        self._timeout = timeout_duration
        self._redis = redis_client
        self._state = self.CLOSED
        self._failures = 0
        self._opened_at: Optional[float] = None
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        with self._lock:
            if self._state == self.OPEN:
                if (
                    self._opened_at is not None
                    and (time.monotonic() - self._opened_at) >= self._timeout
                ):
                    self._state = self.HALF_OPEN
                    self._publish_state(self.HALF_OPEN)
            return self._state

    def is_open(self) -> bool:
        return self.state == self.OPEN

    def record_success(self) -> None:
        with self._lock:
            prev = self._state
            self._failures = 0
            self._state = self.CLOSED
            self._opened_at = None
        if prev != self.CLOSED:
            self._publish_state(self.CLOSED)

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self._fail_max:
                prev = self._state
                self._state = self.OPEN
                self._opened_at = time.monotonic()
                if prev != self.OPEN:
                    logger.warning(
                        "Circuit breaker OPEN for %s after %d failures",
                        self._service_name,
                        self._failures,
                    )
                    self._publish_state(self.OPEN)

    def call(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute *func* through this breaker. Returns None when OPEN."""
        current = self.state
        if current == self.OPEN:
            logger.warning(
                "Circuit breaker OPEN for %s — skipping call", self._service_name
            )
            return None
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception:
            self.record_failure()
            raise

    def _publish_state(self, state: str) -> None:
        logger.info("Circuit breaker [%s] state: %s", self._service_name, state)
        if self._redis:
            try:
                payload = json.dumps({
                    "service": self._service_name,
                    "state": state,
                    "ts": datetime.datetime.utcnow().isoformat(),
                })
                self._redis.set("intel:circuit_breaker", payload, ex=300)
            except Exception:  # noqa: BLE001
                pass


# ── 2c: Tenacity retry decorators ─────────────────────────────────────────────

def _build_retry_condition(retryable_statuses: tuple):  # type: ignore[return]
    """Build a tenacity retry_if_exception filter for HTTP status codes + transport errors."""

    def _should_retry(exc: BaseException) -> bool:
        # Our own status sentinel
        if isinstance(exc, HttpStatusRetryError):
            return exc.status_code in retryable_statuses
        # httpx transport errors
        if isinstance(exc, (httpx.TransportError, httpx.TimeoutException)):
            return True
        # requests exceptions (sync harvesters)
        try:
            import requests  # noqa: PLC0415
            if isinstance(exc, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
                return True
        except ImportError:
            pass
        return False

    return retry_if_exception(_should_retry)


class HttpStatusRetryError(Exception):
    """Raise this to signal a retryable HTTP status code to Tenacity."""

    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}")


def create_retry_decorator(
    service_name: str,
    max_attempts: int = 3,
    base_wait: float = 2.0,
    max_wait: float = 30.0,
    retryable_statuses: tuple = (429, 500, 502, 503, 504),
):
    """Return a tenacity retry decorator for **sync** functions.

    Retries on: httpx transport errors, requests ConnectionError/Timeout,
    and HTTP responses with status in *retryable_statuses*.
    After final failure: logs ERROR and re-raises.
    """
    _svc = service_name  # captured for logging

    def _before_sleep(retry_state: Any) -> None:
        logger.warning(
            "[%s] Retry attempt %d/%d after: %s",
            _svc,
            retry_state.attempt_number,
            max_attempts,
            retry_state.outcome.exception(),
        )

    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=base_wait, max=max_wait),
        retry=_build_retry_condition(retryable_statuses),
        before_sleep=_before_sleep,
        reraise=True,
    )


def create_async_retry_decorator(
    service_name: str,
    max_attempts: int = 3,
    base_wait: float = 2.0,
    max_wait: float = 30.0,
    retryable_statuses: tuple = (429, 500, 502, 503, 504),
):
    """Return a tenacity retry decorator for **async** functions."""
    _svc = service_name

    def _before_sleep(retry_state: Any) -> None:
        logger.warning(
            "[%s] Retry attempt %d/%d after: %s",
            _svc,
            retry_state.attempt_number,
            max_attempts,
            retry_state.outcome.exception(),
        )

    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=base_wait, max=max_wait),
        retry=_build_retry_condition(retryable_statuses),
        before_sleep=_before_sleep,
        reraise=True,
    )


# ── 2d: APScheduler factory ───────────────────────────────────────────────────

def create_scheduler() -> AsyncIOScheduler:
    """Return a UTC AsyncIOScheduler with coalesce=True, misfire_grace_time=30."""
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.configure(
        job_defaults={
            "misfire_grace_time": 30,
            "coalesce": True,
        }
    )
    return scheduler


def add_harvester_job(
    scheduler: AsyncIOScheduler,
    func: Any,
    interval_seconds: int,
    job_id: str,
) -> None:
    """Register an async interval job on *scheduler* (replaces existing if any)."""
    scheduler.add_job(
        func,
        "interval",
        seconds=interval_seconds,
        id=job_id,
        replace_existing=True,
        next_run_time=datetime.datetime.now(datetime.timezone.utc),
    )
    logger.info("Registered harvester job: %s (interval=%ds)", job_id, interval_seconds)


# ── 3: Dead-letter helper ─────────────────────────────────────────────────────

async def dead_letter(
    service_name: str,
    channel: str,
    raw_payload: dict,
    error: Exception,
    db_pool: Any,
) -> None:
    """Write a failed payload to intel_dead_letters.

    *db_pool* can be:
    - asyncpg Pool / Connection (uses .execute with $N placeholders)
    - psycopg2 connection (uses .cursor() with %s placeholders)
    """
    error_type = type(error).__name__
    error_message = str(error)[:1000]

    logger.error(
        "DEAD_LETTER [%s/%s]: %s — %s",
        service_name,
        channel,
        error_type,
        error_message,
    )

    if db_pool is None:
        return

    try:
        payload_json = json.dumps(raw_payload, default=str)

        # asyncpg pool/connection
        if hasattr(db_pool, "execute") and not hasattr(db_pool, "cursor"):
            sql = """
                INSERT INTO intel_dead_letters
                    (service_name, channel, raw_payload, error_message, error_type)
                VALUES ($1, $2, $3::jsonb, $4, $5)
            """
            await db_pool.execute(
                sql, service_name, channel, payload_json, error_message, error_type
            )
        # psycopg2 connection
        elif hasattr(db_pool, "cursor"):
            sql = """
                INSERT INTO intel_dead_letters
                    (service_name, channel, raw_payload, error_message, error_type)
                VALUES (%s, %s, %s::jsonb, %s, %s)
            """
            cur = db_pool.cursor()
            cur.execute(sql, (service_name, channel, payload_json, error_message, error_type))
            db_pool.commit()
    except Exception as dl_err:  # noqa: BLE001
        logger.error("Dead-letter write failed: %s", dl_err)
