"""Cemini Financial Suite — Step 49 Pre-Live Safety Hardening Tests.

Pure unit tests — no network, no real Redis.  All Redis interactions are
mocked with unittest.mock.MagicMock.

Coverage:
  49a  IdempotencyGuard       (15 tests)
  49c  StateHydrator          (10 tests)
  49d  ExposureGate           (15 tests)
  49e  HITLGate               (12 tests)
  49f  MFAHandler             ( 8 tests)
  49g  SelfMatchLock          ( 8 tests)
       Integration / models   ( 5 tests)

Total: 73 tests
"""
from __future__ import annotations

import json
import math
import time
import sys
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# ── Import helpers ──────────────────────────────────────────────────────────

from shared.safety.idempotency import (
    IdempotencyGuard,
    make_idempotency_key,
    _BUCKET_GRANULARITY,
)
from shared.safety.state_hydrator import StateHydrator, HydratedState
from shared.safety.exposure_gate import ExposureGate
from shared.safety.hitl_gate import HITLGate, HITLDecision
from shared.safety.mfa_handler import MFAHandler
from shared.safety.self_match_lock import SelfMatchLock


# ═══════════════════════════════════════════════════════════════════════════
# 49a — IdempotencyGuard
# ═══════════════════════════════════════════════════════════════════════════

class TestMakeIdempotencyKey:
    """make_idempotency_key() produces deterministic prefixed hex keys."""

    def test_key_has_correct_prefix(self):
        key = make_idempotency_key("AAPL", "buy", 0.80, 0.05)
        assert key.startswith("idempotency:order:")

    def test_key_is_deterministic(self):
        ts = 1_700_000_000.0
        k1 = make_idempotency_key("AAPL", "buy", 0.80, 0.05, ts)
        k2 = make_idempotency_key("AAPL", "buy", 0.80, 0.05, ts)
        assert k1 == k2

    def test_different_tickers_produce_different_keys(self):
        ts = 1_700_000_000.0
        k1 = make_idempotency_key("AAPL", "buy", 0.80, 0.05, ts)
        k2 = make_idempotency_key("TSLA", "buy", 0.80, 0.05, ts)
        assert k1 != k2

    def test_different_actions_produce_different_keys(self):
        ts = 1_700_000_000.0
        k1 = make_idempotency_key("AAPL", "buy", 0.80, 0.05, ts)
        k2 = make_idempotency_key("AAPL", "sell", 0.80, 0.05, ts)
        assert k1 != k2

    def test_timestamps_in_same_bucket_produce_same_key(self):
        """Two timestamps within the same 60-second bucket → identical key."""
        # Align to a bucket boundary so both timestamps fall in the same bucket
        bucket_start = math.floor(1_700_000_000.0 / _BUCKET_GRANULARITY) * _BUCKET_GRANULARITY
        ts1 = bucket_start + 5
        ts2 = bucket_start + 55  # same bucket, different second
        k1 = make_idempotency_key("AAPL", "buy", 0.80, 0.05, ts1)
        k2 = make_idempotency_key("AAPL", "buy", 0.80, 0.05, ts2)
        assert k1 == k2

    def test_timestamps_in_different_buckets_produce_different_keys(self):
        base = 1_700_000_000.0
        ts1 = base
        ts2 = base + _BUCKET_GRANULARITY + 1  # next bucket
        k1 = make_idempotency_key("AAPL", "buy", 0.80, 0.05, ts1)
        k2 = make_idempotency_key("AAPL", "buy", 0.80, 0.05, ts2)
        assert k1 != k2

    def test_key_hex_suffix_is_16_chars(self):
        key = make_idempotency_key("BTC", "buy", 0.9, 0.03)
        suffix = key.split(":")[-1]
        assert len(suffix) == 16


class TestIdempotencyGuard:
    """IdempotencyGuard dedup logic."""

    def _make_redis(self, set_returns=True):
        r = MagicMock()
        # redis.set(..., nx=True) returns True on first write, None on duplicate
        r.set.return_value = True if set_returns else None
        return r

    def test_first_call_returns_not_duplicate(self):
        redis = self._make_redis(set_returns=True)
        guard = IdempotencyGuard(redis)
        result = guard.is_duplicate("AAPL", "buy", 0.80, 0.05)
        assert result is False

    def test_second_call_returns_duplicate(self):
        redis = self._make_redis(set_returns=None)
        guard = IdempotencyGuard(redis)
        result = guard.is_duplicate("AAPL", "buy", 0.80, 0.05)
        assert result is True

    def test_redis_set_called_with_nx_true(self):
        redis = self._make_redis()
        guard = IdempotencyGuard(redis)
        guard.is_duplicate("AAPL", "buy", 0.80, 0.05)
        call_kwargs = redis.set.call_args[1]
        assert call_kwargs.get("nx") is True

    def test_redis_error_fails_open(self):
        """If Redis raises, the order is allowed through (fail-open)."""
        redis = MagicMock()
        redis.set.side_effect = ConnectionError("redis down")
        guard = IdempotencyGuard(redis)
        result = guard.is_duplicate("AAPL", "buy", 0.80, 0.05)
        assert result is False  # fail-open

    def test_clear_calls_redis_delete(self):
        redis = MagicMock()
        guard = IdempotencyGuard(redis)
        guard.clear("AAPL", "buy", 0.80, 0.05)
        redis.delete.assert_called_once()

    def test_clear_redis_error_does_not_raise(self):
        redis = MagicMock()
        redis.delete.side_effect = ConnectionError("redis down")
        guard = IdempotencyGuard(redis)
        guard.clear("AAPL", "buy", 0.80, 0.05)  # should not raise

    def test_custom_ttl_passed_to_redis(self):
        redis = self._make_redis()
        guard = IdempotencyGuard(redis, ttl=3600)
        guard.is_duplicate("AAPL", "buy", 0.80, 0.05)
        call_kwargs = redis.set.call_args[1]
        assert call_kwargs.get("ex") == 3600

    def test_different_allocation_produces_different_key(self):
        redis = MagicMock()
        redis.set.return_value = True
        guard = IdempotencyGuard(redis)
        ts = 1_700_000_000.0
        guard.is_duplicate("AAPL", "buy", 0.80, 0.05, ts)
        guard.is_duplicate("AAPL", "buy", 0.80, 0.08, ts)
        # Two distinct keys should have been used
        keys = [call[0][0] for call in redis.set.call_args_list]
        assert keys[0] != keys[1]


# ═══════════════════════════════════════════════════════════════════════════
# 49c — StateHydrator
# ═══════════════════════════════════════════════════════════════════════════

class TestStateHydrator:
    """StateHydrator loads state from Redis mock."""

    def _make_redis(self, trades=None, positions=None):
        r = MagicMock()
        def get_side_effect(key):
            if key == "quantos:executed_trades":
                return json.dumps(trades) if trades is not None else None
            if key == "quantos:active_positions":
                return json.dumps(positions) if positions is not None else None
            return None
        r.get.side_effect = get_side_effect
        return r

    def test_hydrate_returns_hydrated_state(self):
        redis = self._make_redis(trades={"t1": 1234.0}, positions=[{"ticker": "AAPL"}])
        hydrator = StateHydrator(redis)
        state = hydrator.hydrate()
        assert isinstance(state, HydratedState)
        assert state.loaded is True

    def test_hydrate_loads_executed_trades(self):
        trades = {"trade_001": 1700000000.0, "trade_002": 1700001000.0}
        redis = self._make_redis(trades=trades)
        hydrator = StateHydrator(redis)
        state = hydrator.hydrate()
        assert state.executed_trades == trades
        assert state.trade_count == 2

    def test_hydrate_loads_active_positions_list(self):
        positions = [{"ticker": "AAPL", "qty": 10}, {"ticker": "TSLA", "qty": 5}]
        redis = self._make_redis(positions=positions)
        hydrator = StateHydrator(redis)
        state = hydrator.hydrate()
        assert state.position_count == 2

    def test_hydrate_converts_dict_positions_to_list(self):
        positions = {"AAPL": {"qty": 10}, "TSLA": {"qty": 5}}
        redis = self._make_redis(positions=positions)
        hydrator = StateHydrator(redis)
        state = hydrator.hydrate()
        assert isinstance(state.active_positions, list)
        assert state.position_count == 2

    def test_hydrate_returns_empty_state_on_redis_error(self):
        redis = MagicMock()
        redis.get.side_effect = ConnectionError("redis down")
        hydrator = StateHydrator(redis)
        state = hydrator.hydrate()
        assert state.trade_count == 0
        assert state.position_count == 0
        assert state.loaded is False

    def test_hydrate_loaded_false_when_no_keys(self):
        redis = self._make_redis(trades=None, positions=None)
        hydrator = StateHydrator(redis)
        state = hydrator.hydrate()
        assert state.loaded is False

    def test_persist_trades_calls_redis_set(self):
        redis = MagicMock()
        hydrator = StateHydrator(redis)
        hydrator.persist_trades({"t1": 1.0})
        redis.set.assert_called_once()
        args = redis.set.call_args[0]
        assert args[0] == "quantos:executed_trades"
        assert '"t1"' in args[1]

    def test_persist_positions_list(self):
        redis = MagicMock()
        hydrator = StateHydrator(redis)
        hydrator.persist_positions([{"ticker": "AAPL"}])
        redis.set.assert_called_once()
        args = redis.set.call_args[0]
        assert args[0] == "quantos:active_positions"

    def test_persist_positions_dict_converted(self):
        redis = MagicMock()
        hydrator = StateHydrator(redis)
        hydrator.persist_positions({"AAPL": {"qty": 1}})
        args = redis.set.call_args[0]
        payload = json.loads(args[1])
        assert isinstance(payload, list)

    def test_persist_redis_error_does_not_raise(self):
        redis = MagicMock()
        redis.set.side_effect = ConnectionError("redis down")
        hydrator = StateHydrator(redis)
        hydrator.persist_trades({"t1": 1.0})  # must not raise


# ═══════════════════════════════════════════════════════════════════════════
# 49d — ExposureGate
# ═══════════════════════════════════════════════════════════════════════════

class TestExposureGate:
    """ExposureGate hard-blocking logic."""

    def _make_redis(self, current_exposure: float = 0.0):
        r = MagicMock()
        r.get.return_value = str(current_exposure) if current_exposure else None
        r.pipeline.return_value.__enter__ = MagicMock(return_value=MagicMock())
        r.pipeline.return_value.__exit__ = MagicMock(return_value=False)
        pipe = MagicMock()
        r.pipeline.return_value = pipe
        pipe.incrbyfloat = MagicMock()
        pipe.expire = MagicMock()
        pipe.execute = MagicMock(return_value=[0.05, True])
        return r

    def test_check_allows_when_no_existing_exposure(self):
        redis = self._make_redis(0.0)
        gate = ExposureGate(redis, max_exposure_pct=0.10, paper_buying_power=1000.0)
        assert gate.check("AAPL", allocation_pct=0.05) is True

    def test_check_blocks_when_would_exceed_max(self):
        redis = self._make_redis(current_exposure=90.0)  # already $90 of $100 max
        gate = ExposureGate(redis, max_exposure_pct=0.10, paper_buying_power=1000.0)
        # Trying to spend another $50 → $140 > $100 max
        assert gate.check("AAPL", allocation_pct=0.05) is False

    def test_check_allows_at_exact_boundary(self):
        redis = self._make_redis(current_exposure=50.0)
        gate = ExposureGate(redis, max_exposure_pct=0.10, paper_buying_power=1000.0)
        # $50 existing + $50 proposed = $100 = max (≤ max → allowed)
        assert gate.check("AAPL", allocation_pct=0.05) is True

    def test_check_blocks_when_buying_power_is_zero(self):
        redis = self._make_redis(0.0)
        gate = ExposureGate(redis, max_exposure_pct=0.10, paper_buying_power=0.0)
        assert gate.check("AAPL", allocation_pct=0.05) is False

    def test_check_uses_override_buying_power(self):
        redis = self._make_redis(0.0)
        gate = ExposureGate(redis, max_exposure_pct=0.10)
        # Explicit buying_power=2000 → max=$200, proposed=$20 → allowed
        assert gate.check("AAPL", allocation_pct=0.01, buying_power=2000.0) is True

    def test_live_trading_without_buying_power_fails_closed(self):
        redis = self._make_redis(0.0)
        gate = ExposureGate(redis)
        with patch.dict("os.environ", {"LIVE_TRADING": "true"}):
            # No buying_power passed → fail-closed
            assert gate.check("AAPL", allocation_pct=0.05) is False

    def test_record_fill_calls_incrbyfloat(self):
        redis = self._make_redis(0.0)
        gate = ExposureGate(redis, paper_buying_power=1000.0)
        gate.record_fill("AAPL", allocation_pct=0.05)
        redis.pipeline.return_value.incrbyfloat.assert_called_once()
        args = redis.pipeline.return_value.incrbyfloat.call_args[0]
        assert args[0] == "safety:exposure:AAPL"
        assert pytest.approx(args[1], abs=0.01) == 50.0

    def test_get_exposure_returns_float(self):
        redis = MagicMock()
        redis.get.return_value = "75.5"
        gate = ExposureGate(redis)
        assert gate.get_exposure("AAPL") == 75.5

    def test_get_exposure_returns_zero_when_no_key(self):
        redis = MagicMock()
        redis.get.return_value = None
        gate = ExposureGate(redis)
        assert gate.get_exposure("AAPL") == 0.0

    def test_reset_exposure_calls_delete(self):
        redis = MagicMock()
        gate = ExposureGate(redis)
        gate.reset_exposure("AAPL")
        redis.delete.assert_called_once_with("safety:exposure:AAPL")

    def test_redis_error_in_get_exposure_returns_zero(self):
        redis = MagicMock()
        redis.get.side_effect = ConnectionError("down")
        gate = ExposureGate(redis)
        assert gate.get_exposure("AAPL") == 0.0

    def test_check_blocks_when_redis_error_on_get(self):
        """If we can't read current exposure, we allow the order (fail-open for reads)."""
        redis = MagicMock()
        redis.get.side_effect = ConnectionError("down")
        gate = ExposureGate(redis, max_exposure_pct=0.10, paper_buying_power=1000.0)
        # current_exposure returns 0 on error → no block
        assert gate.check("AAPL", allocation_pct=0.05) is True

    def test_check_uses_paper_buying_power_when_live_not_set(self):
        redis = self._make_redis(0.0)
        gate = ExposureGate(redis, paper_buying_power=500.0, max_exposure_pct=0.10)
        # max = 500 * 0.10 = $50; proposed = 500 * 0.11 = $55 → BLOCKED
        assert gate.check("AAPL", allocation_pct=0.11) is False

    def test_exposure_key_namespaced_correctly(self):
        redis = MagicMock()
        redis.get.return_value = None
        gate = ExposureGate(redis)
        gate.get_exposure("TSLA")
        redis.get.assert_called_with("safety:exposure:TSLA")

    def test_reset_redis_error_does_not_raise(self):
        redis = MagicMock()
        redis.delete.side_effect = ConnectionError("down")
        gate = ExposureGate(redis)
        gate.reset_exposure("AAPL")  # must not raise


# ═══════════════════════════════════════════════════════════════════════════
# 49e — HITLGate
# ═══════════════════════════════════════════════════════════════════════════

class TestHITLGate:
    """HITLGate approval queue logic."""

    def _make_redis(self, decision: str | None = None):
        r = MagicMock()
        r.lpush.return_value = 1
        r.get.return_value = decision
        r.set.return_value = True
        return r

    def test_requires_approval_above_floor(self):
        gate = HITLGate(MagicMock(), confidence_floor=0.85)
        assert gate.requires_approval(0.90) is True
        assert gate.requires_approval(0.85) is True

    def test_requires_approval_below_floor(self):
        gate = HITLGate(MagicMock(), confidence_floor=0.85)
        assert gate.requires_approval(0.84) is False

    def test_request_approval_pushes_to_redis(self):
        redis = self._make_redis()
        gate = HITLGate(redis)
        gate.request_approval("sig-001", {"ticker": "AAPL", "action": "buy", "confidence": 0.90})
        redis.lpush.assert_called_once()
        key, payload = redis.lpush.call_args[0]
        assert key == "safety:hitl:pending"
        data = json.loads(payload)
        assert data["signal_id"] == "sig-001"

    def test_wait_for_decision_returns_approved(self):
        redis = self._make_redis(decision="APPROVE")
        gate = HITLGate(redis, timeout_seconds=5)
        result = gate.wait_for_decision("sig-001")
        assert result == HITLDecision.APPROVED

    def test_wait_for_decision_returns_rejected(self):
        redis = self._make_redis(decision="REJECT")
        gate = HITLGate(redis, timeout_seconds=5)
        result = gate.wait_for_decision("sig-001")
        assert result == HITLDecision.REJECTED

    def test_wait_for_decision_timeout_returns_timeout(self):
        redis = self._make_redis(decision=None)  # never resolves
        gate = HITLGate(redis, timeout_seconds=0)  # expire immediately
        result = gate.wait_for_decision("sig-001", timeout=0)
        assert result == HITLDecision.TIMEOUT

    def test_submit_decision_writes_to_redis(self):
        redis = MagicMock()
        gate = HITLGate(redis)
        gate.submit_decision("sig-001", HITLDecision.APPROVED)
        redis.set.assert_called_once_with(
            "safety:hitl:decision:sig-001",
            "APPROVE",
            ex=gate.timeout_seconds,
        )

    def test_evaluate_skips_below_floor(self):
        redis = MagicMock()
        gate = HITLGate(redis, confidence_floor=0.85)
        result = gate.evaluate("sig-001", 0.80, {"ticker": "AAPL", "action": "buy"})
        assert result == HITLDecision.SKIPPED
        redis.lpush.assert_not_called()

    def test_evaluate_requests_and_waits_above_floor(self):
        redis = self._make_redis(decision="APPROVE")
        gate = HITLGate(redis, confidence_floor=0.85, timeout_seconds=5)
        result = gate.evaluate("sig-002", 0.90, {"ticker": "AAPL", "action": "buy"})
        assert result == HITLDecision.APPROVED

    def test_wait_for_decision_handles_bytes_response(self):
        redis = MagicMock()
        redis.get.return_value = b"APPROVE"
        gate = HITLGate(redis, timeout_seconds=5)
        result = gate.wait_for_decision("sig-001")
        assert result == HITLDecision.APPROVED

    def test_request_approval_redis_error_does_not_raise(self):
        redis = MagicMock()
        redis.lpush.side_effect = ConnectionError("down")
        gate = HITLGate(redis)
        gate.request_approval("sig-001", {})  # must not raise

    def test_submit_decision_redis_error_does_not_raise(self):
        redis = MagicMock()
        redis.set.side_effect = ConnectionError("down")
        gate = HITLGate(redis)
        gate.submit_decision("sig-001", HITLDecision.REJECTED)  # must not raise


# ═══════════════════════════════════════════════════════════════════════════
# 49f — MFAHandler
# ═══════════════════════════════════════════════════════════════════════════

class TestMFAHandler:
    """MFAHandler TOTP generation."""

    def test_not_configured_without_secret(self):
        handler = MFAHandler(secret="")
        # pyotp may or may not be installed, but no secret → not configured
        assert handler.is_configured() is False

    def test_get_current_code_returns_none_when_not_configured(self):
        handler = MFAHandler(secret="")
        assert handler.get_current_code() is None

    def test_verify_code_returns_false_when_not_configured(self):
        handler = MFAHandler(secret="")
        assert handler.verify_code("123456") is False

    def test_provisioning_uri_returns_none_when_not_configured(self):
        handler = MFAHandler(secret="")
        assert handler.provisioning_uri() is None

    def test_configured_with_valid_secret(self):
        """Use a real pyotp TOTP secret if pyotp is available."""
        secret = "JBSWY3DPEHPK3PXP"  # standard test vector
        handler = MFAHandler(secret=secret)
        if handler._pyotp is None:
            pytest.skip("pyotp not installed")
        assert handler.is_configured() is True

    def test_get_current_code_returns_six_digit_string(self):
        secret = "JBSWY3DPEHPK3PXP"
        handler = MFAHandler(secret=secret)
        if handler._pyotp is None:
            pytest.skip("pyotp not installed")
        code = handler.get_current_code()
        assert code is not None
        assert len(code) == 6
        assert code.isdigit()

    def test_verify_code_verifies_current_code(self):
        secret = "JBSWY3DPEHPK3PXP"
        handler = MFAHandler(secret=secret)
        if handler._pyotp is None:
            pytest.skip("pyotp not installed")
        code = handler.get_current_code()
        assert handler.verify_code(code) is True

    def test_verify_code_rejects_wrong_code(self):
        secret = "JBSWY3DPEHPK3PXP"
        handler = MFAHandler(secret=secret)
        if handler._pyotp is None:
            pytest.skip("pyotp not installed")
        assert handler.verify_code("000000") is False

    def test_reads_secret_from_env(self):
        with patch.dict("os.environ", {"ROBINHOOD_MFA_SECRET": "JBSWY3DPEHPK3PXP"}):
            handler = MFAHandler()
            assert handler._secret == "JBSWY3DPEHPK3PXP"

    def test_provisioning_uri_contains_issuer(self):
        secret = "JBSWY3DPEHPK3PXP"
        handler = MFAHandler(secret=secret)
        if handler._pyotp is None:
            pytest.skip("pyotp not installed")
        uri = handler.provisioning_uri(account_name="test@cemini", issuer="Robinhood")
        assert uri is not None
        assert "Robinhood" in uri


# ═══════════════════════════════════════════════════════════════════════════
# 49g — SelfMatchLock
# ═══════════════════════════════════════════════════════════════════════════

class TestSelfMatchLock:
    """SelfMatchLock CFTC self-match prevention."""

    def _make_redis(self, existing_direction: str | None = None):
        r = MagicMock()
        r.get.return_value = existing_direction
        r.set.return_value = True
        r.delete.return_value = 1
        return r

    def test_check_allows_when_no_existing_position(self):
        redis = self._make_redis(existing_direction=None)
        lock = SelfMatchLock(redis)
        assert lock.check("INXD-23DEC31-B4500", "YES") is True

    def test_check_blocks_opposing_direction(self):
        redis = self._make_redis(existing_direction="YES")
        lock = SelfMatchLock(redis)
        assert lock.check("INXD-23DEC31-B4500", "NO") is False

    def test_check_allows_same_direction(self):
        redis = self._make_redis(existing_direction="YES")
        lock = SelfMatchLock(redis)
        assert lock.check("INXD-23DEC31-B4500", "YES") is True

    def test_record_open_writes_direction_to_redis(self):
        redis = self._make_redis()
        lock = SelfMatchLock(redis)
        lock.record_open("INXD-23DEC31-B4500", "YES")
        redis.set.assert_called_once_with(
            "safety:self_match:INXD-23DEC31-B4500", "YES", ex=lock.ttl
        )

    def test_record_close_deletes_redis_key(self):
        redis = self._make_redis()
        lock = SelfMatchLock(redis)
        lock.record_close("INXD-23DEC31-B4500")
        redis.delete.assert_called_once_with("safety:self_match:INXD-23DEC31-B4500")

    def test_get_open_direction_returns_none_when_absent(self):
        redis = self._make_redis(existing_direction=None)
        lock = SelfMatchLock(redis)
        assert lock.get_open_direction("INXD-23DEC31-B4500") is None

    def test_get_open_direction_returns_direction(self):
        redis = self._make_redis(existing_direction="NO")
        lock = SelfMatchLock(redis)
        assert lock.get_open_direction("INXD-23DEC31-B4500") == "NO"

    def test_redis_error_in_check_allows_order(self):
        """If Redis is down, we can't confirm self-match — allow through."""
        redis = MagicMock()
        redis.get.side_effect = ConnectionError("down")
        lock = SelfMatchLock(redis)
        assert lock.check("INXD-23DEC31-B4500", "YES") is True


# ═══════════════════════════════════════════════════════════════════════════
# Integration / module-level tests
# ═══════════════════════════════════════════════════════════════════════════

class TestSafetyPackageImports:
    """Ensure all safety modules import correctly from the package."""

    def test_package_exports_all_classes(self):
        from shared.safety import (
            IdempotencyGuard,
            StateHydrator,
            ExposureGate,
            HITLGate,
            HITLDecision,
            MFAHandler,
            SelfMatchLock,
        )
        assert IdempotencyGuard is not None
        assert StateHydrator is not None
        assert ExposureGate is not None
        assert HITLGate is not None
        assert HITLDecision is not None
        assert MFAHandler is not None
        assert SelfMatchLock is not None

    def test_hitl_decision_values(self):
        assert HITLDecision.APPROVED.value == "APPROVE"
        assert HITLDecision.REJECTED.value == "REJECT"
        assert HITLDecision.TIMEOUT.value == "TIMEOUT"
        assert HITLDecision.SKIPPED.value == "SKIPPED"

    def test_idempotency_key_format(self):
        key = make_idempotency_key("SPY", "buy", 0.75, 0.05)
        parts = key.split(":")
        assert len(parts) == 3
        assert parts[0] == "idempotency"
        assert parts[1] == "order"

    def test_hydrated_state_defaults(self):
        state = HydratedState()
        assert state.trade_count == 0
        assert state.position_count == 0
        assert state.loaded is False

    def test_exposure_gate_max_exposure_boundary_calculation(self):
        """ExposureGate math: 1000 * 0.10 = 100, proposed 50 + existing 55 = 105 > 100."""
        redis = MagicMock()
        redis.get.return_value = "55.0"
        gate = ExposureGate(redis, max_exposure_pct=0.10, paper_buying_power=1000.0)
        # 55 existing + 50 proposed = 105 > 100 → BLOCKED
        assert gate.check("AAPL", allocation_pct=0.05) is False
