"""Tests for core/resilience.py — pure, no network / Redis / Postgres."""
from __future__ import annotations

import asyncio
import datetime
import json
import os
import sys
import threading
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Make sure repo root is on sys.path
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core.resilience import (
    HttpStatusRetryError,
    SyncCircuitBreaker,
    add_harvester_job,
    create_async_retry_decorator,
    create_circuit_breaker,
    create_resilient_client,
    create_resilient_sync_client,
    create_retry_decorator,
    create_scheduler,
    dead_letter,
)


# ── Hishel client tests ────────────────────────────────────────────────────────

class TestCreateResilientClient:
    def test_returns_async_client(self, tmp_path):
        import httpx
        with patch("core.resilience._HISHEL_AVAILABLE", True):
            client = create_resilient_client("test_svc", cache_ttl=60, timeout=10.0)
        assert hasattr(client, "get")
        assert hasattr(client, "aclose")

    def test_cache_directory_created_per_service(self, tmp_path):
        svc = f"test_svc_{id(tmp_path)}"
        cache_dir = f"/tmp/hishel_cache/{svc}"  # noqa: S108
        create_resilient_client(svc, cache_ttl=60, timeout=5.0)
        assert os.path.isdir(cache_dir)

    def test_resilient_client_custom_timeout(self):
        client = create_resilient_client("timeout_test", timeout=42.0)
        # httpx stores timeout as Timeout object; check it was accepted (no error)
        assert client is not None

    def test_falls_back_to_plain_httpx_when_hishel_unavailable(self):
        import httpx
        with patch("core.resilience._HISHEL_AVAILABLE", False):
            client = create_resilient_client("fallback_svc", timeout=5.0)
        assert isinstance(client, httpx.AsyncClient)


class TestCreateResilientSyncClient:
    def test_returns_sync_client(self):
        import httpx
        client = create_resilient_sync_client("sync_test", cache_ttl=60, timeout=10.0)
        assert hasattr(client, "get")
        # httpx.Client is sync
        assert not asyncio.iscoroutinefunction(client.get)

    def test_cache_dir_per_service(self, tmp_path):
        svc = f"sync_svc_{id(tmp_path)}"
        create_resilient_sync_client(svc, cache_ttl=60)
        assert os.path.isdir(f"/tmp/hishel_cache/{svc}")  # noqa: S108

    def test_resilient_sync_client_custom_timeout(self):
        client = create_resilient_sync_client("sync_timeout", timeout=99.0)
        assert client is not None


# ── SyncCircuitBreaker tests ───────────────────────────────────────────────────

class TestSyncCircuitBreaker:
    def test_initial_state_is_closed(self):
        cb = SyncCircuitBreaker("svc", fail_max=3, timeout_duration=60.0)
        assert cb.state == SyncCircuitBreaker.CLOSED

    def test_opens_after_consecutive_failures(self):
        cb = SyncCircuitBreaker("svc", fail_max=3, timeout_duration=60.0)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == SyncCircuitBreaker.OPEN

    def test_does_not_open_before_fail_max(self):
        cb = SyncCircuitBreaker("svc", fail_max=5, timeout_duration=60.0)
        for _ in range(4):
            cb.record_failure()
        assert cb.state == SyncCircuitBreaker.CLOSED

    def test_half_open_after_timeout(self):
        cb = SyncCircuitBreaker("svc", fail_max=2, timeout_duration=0.05)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == SyncCircuitBreaker.OPEN
        time.sleep(0.1)
        assert cb.state == SyncCircuitBreaker.HALF_OPEN

    def test_closes_on_success_after_half_open(self):
        cb = SyncCircuitBreaker("svc", fail_max=2, timeout_duration=0.05)
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.1)
        assert cb.state == SyncCircuitBreaker.HALF_OPEN
        cb.record_success()
        assert cb.state == SyncCircuitBreaker.CLOSED

    def test_returns_none_when_open(self):
        cb = SyncCircuitBreaker("svc", fail_max=2, timeout_duration=60.0)
        cb.record_failure()
        cb.record_failure()
        result = cb.call(lambda: "should_not_run")
        assert result is None

    def test_call_executes_func_when_closed(self):
        cb = SyncCircuitBreaker("svc", fail_max=3)
        result = cb.call(lambda: 42)
        assert result == 42

    def test_call_records_success(self):
        cb = SyncCircuitBreaker("svc", fail_max=3)
        cb.record_failure()
        cb.record_failure()
        # Still closed (fail_max=3, only 2 failures)
        cb.call(lambda: None)
        assert cb._failures == 0  # reset on success

    def test_call_records_failure_on_exception(self):
        cb = SyncCircuitBreaker("svc", fail_max=3)

        def boom():
            raise ValueError("oops")

        with pytest.raises(ValueError):
            cb.call(boom)
        assert cb._failures == 1

    def test_publishes_state_to_redis_on_open(self):
        mock_redis = MagicMock()
        cb = SyncCircuitBreaker("redis_test", fail_max=2, redis_client=mock_redis)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == SyncCircuitBreaker.OPEN
        mock_redis.set.assert_called()
        call_args = mock_redis.set.call_args
        payload_str = call_args[0][1]  # second positional arg
        payload = json.loads(payload_str)
        assert payload["service"] == "redis_test"
        assert payload["state"] == SyncCircuitBreaker.OPEN

    def test_is_open_returns_true_when_open(self):
        cb = SyncCircuitBreaker("svc", fail_max=1)
        cb.record_failure()
        assert cb.is_open() is True

    def test_is_open_returns_false_when_closed(self):
        cb = SyncCircuitBreaker("svc", fail_max=3)
        assert cb.is_open() is False

    def test_thread_safe_concurrent_failures(self):
        cb = SyncCircuitBreaker("threaded", fail_max=10)
        errors = []

        def fail_once():
            try:
                cb.record_failure()
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=fail_once) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
        assert cb._failures == 10
        assert cb.state == SyncCircuitBreaker.OPEN


# ── Tenacity retry decorator tests ────────────────────────────────────────────

class TestCreateRetryDecorator:
    def test_returns_callable_decorator(self):
        dec = create_retry_decorator("svc")
        assert callable(dec)

    def test_retries_on_429(self):
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise HttpStatusRetryError(429)
            return "ok"

        dec = create_retry_decorator("svc", max_attempts=3, base_wait=0.001, max_wait=0.01)
        decorated = dec(flaky)
        result = decorated()
        assert result == "ok"
        assert call_count == 3

    def test_retries_on_503(self):
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise HttpStatusRetryError(503)
            return "done"

        dec = create_retry_decorator("svc", max_attempts=3, base_wait=0.001, max_wait=0.01)
        decorated = dec(flaky)
        result = decorated()
        assert result == "done"
        assert call_count == 2

    def test_gives_up_after_max_attempts(self):
        call_count = 0

        def always_fail():
            nonlocal call_count
            call_count += 1
            raise HttpStatusRetryError(500)

        dec = create_retry_decorator("svc", max_attempts=3, base_wait=0.001, max_wait=0.01)
        decorated = dec(always_fail)
        with pytest.raises(HttpStatusRetryError):
            decorated()
        assert call_count == 3

    def test_custom_retryable_statuses(self):
        """400 is not in default statuses, but we can add it."""
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise HttpStatusRetryError(400)
            return "ok"

        dec = create_retry_decorator(
            "svc", max_attempts=3, base_wait=0.001, max_wait=0.01,
            retryable_statuses=(400,),
        )
        result = dec(flaky)()
        assert result == "ok"
        assert call_count == 2

    def test_does_not_retry_on_non_retryable_status(self):
        """400 with default statuses should not retry."""
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            raise HttpStatusRetryError(400)

        dec = create_retry_decorator(
            "svc", max_attempts=3, base_wait=0.001, max_wait=0.01,
            retryable_statuses=(500, 502, 503, 504),  # no 400
        )
        with pytest.raises(HttpStatusRetryError):
            dec(flaky)()
        assert call_count == 1  # no retry

    def test_retries_on_httpx_transport_error(self):
        import httpx
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.ConnectError("connect failed")
            return "ok"

        dec = create_retry_decorator("svc", max_attempts=3, base_wait=0.001, max_wait=0.01)
        result = dec(flaky)()
        assert result == "ok"


# ── APScheduler factory tests ─────────────────────────────────────────────────

class TestSchedulerFactory:
    def test_returns_asyncio_scheduler(self):
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        scheduler = create_scheduler()
        assert isinstance(scheduler, AsyncIOScheduler)

    def test_coalesce_enabled(self):
        scheduler = create_scheduler()
        defaults = scheduler._job_defaults
        assert defaults.get("coalesce") is True

    def test_misfire_grace_time(self):
        scheduler = create_scheduler()
        defaults = scheduler._job_defaults
        assert defaults.get("misfire_grace_time") == 30

    def test_add_harvester_job_registers_job(self):
        scheduler = create_scheduler()

        async def dummy_job():
            pass

        add_harvester_job(scheduler, dummy_job, 900, "test_job")
        job = scheduler.get_job("test_job")
        assert job is not None
        assert job.id == "test_job"

    def test_add_harvester_job_interval(self):
        from apscheduler.triggers.interval import IntervalTrigger
        scheduler = create_scheduler()

        async def dummy_job():
            pass

        add_harvester_job(scheduler, dummy_job, 300, "interval_job")
        job = scheduler.get_job("interval_job")
        assert isinstance(job.trigger, IntervalTrigger)


# ── Dead-letter tests ─────────────────────────────────────────────────────────

class TestDeadLetter:
    def test_writes_to_psycopg2_conn(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        # psycopg2 connections have cursor() but not asyncpg-style execute
        mock_conn.execute = None  # not asyncio-style

        error = ValueError("schema changed")

        asyncio.run(
            dead_letter(
                service_name="test_svc",
                channel="intel:test",
                raw_payload={"key": "val"},
                error=error,
                db_pool=mock_conn,
            )
        )

        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0]
        assert "intel_dead_letters" in call_args[0]
        assert call_args[1][0] == "test_svc"
        assert call_args[1][1] == "intel:test"
        assert "val" in call_args[1][2]
        assert "schema changed" in call_args[1][3]
        assert call_args[1][4] == "ValueError"

    def test_captures_service_name_and_channel(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.execute = None

        asyncio.run(
            dead_letter(
                service_name="polygon_ingestor",
                channel="intel:ticks",
                raw_payload={},
                error=RuntimeError("boom"),
                db_pool=mock_conn,
            )
        )

        args = mock_cursor.execute.call_args[0][1]
        assert args[0] == "polygon_ingestor"
        assert args[1] == "intel:ticks"

    def test_captures_validation_error(self):
        from pydantic import BaseModel, ValidationError

        class Strict(BaseModel):
            price: float

        try:
            Strict(price="not_a_float")
        except ValidationError as exc:
            error = exc

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.execute = None

        asyncio.run(
            dead_letter("svc", "chan", {"bad": "data"}, error, mock_conn)
        )

        args = mock_cursor.execute.call_args[0][1]
        assert args[4] == "ValidationError"

    def test_noop_when_db_pool_is_none(self):
        """Should log but not raise when db_pool is None."""
        asyncio.run(
            dead_letter("svc", "chan", {}, ValueError("x"), None)
        )
        # If no exception raised, test passes

    def test_handles_db_write_failure_gracefully(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("DB down")
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.execute = None

        # Should not raise even if DB write fails
        asyncio.run(
            dead_letter("svc", "chan", {}, ValueError("x"), mock_conn)
        )


# ── Async circuit breaker tests ───────────────────────────────────────────────

class TestCreateCircuitBreaker:
    def test_returns_circuit_breaker(self):
        cb = create_circuit_breaker("async_svc", fail_max=3)
        import aiobreaker
        assert isinstance(cb, aiobreaker.CircuitBreaker)

    def test_opens_after_consecutive_async_failures(self):
        import aiobreaker
        from aiobreaker.state import CircuitBreakerError

        cb = create_circuit_breaker("async_open_test", fail_max=2, timeout_duration=60.0)

        @cb
        async def always_fail():
            raise RuntimeError("fail")

        async def run():
            # First failure: RuntimeError propagates (breaker still closed)
            with pytest.raises(RuntimeError):
                await always_fail()
            # Second failure: breaker opens → raises CircuitBreakerError
            with pytest.raises((RuntimeError, CircuitBreakerError)):
                await always_fail()

        asyncio.run(run())
        # current_state is a CircuitBreakerState enum — check its name
        assert cb.current_state.name == "OPEN"

    def test_publishes_state_change_to_redis(self):
        import aiobreaker
        from aiobreaker.state import CircuitBreakerError

        mock_redis = MagicMock()
        cb = create_circuit_breaker("redis_async_test", fail_max=1, redis_client=mock_redis)

        @cb
        async def fail():
            raise RuntimeError("fail")

        async def run():
            # fail_max=1: first call opens the breaker and raises CircuitBreakerError
            with pytest.raises((RuntimeError, CircuitBreakerError)):
                await fail()

        asyncio.run(run())
        # State changed to Open — listener should have called redis.set
        mock_redis.set.assert_called()
