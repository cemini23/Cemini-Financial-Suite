"""
tests/test_kalshi_rewards.py — Pure unit tests for scripts/kalshi_rewards.py

All tests are pure (no network, no Redis, no disk I/O) using mocked dependencies.
Run: PYTHONPATH=/opt/cemini pytest tests/test_kalshi_rewards.py -v
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Path setup ─────────────────────────────────────────────────────────────────
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# ── Minimal cryptography stub so tests run without PEM files ──────────────────
# We need to import the module before patching, so we mock at module level.

class _FakePrivateKey:
    """Minimal RSA key stub for signing tests."""
    def sign(self, msg, pss_padding, hash_algo):
        # Include full message digest so different msgs produce different signatures
        import hashlib
        digest = hashlib.sha256(msg).digest()
        return b"fakesig_" + digest


# Patch _load_private_key at module import time by pre-providing the env var
# (the actual key loading is tested via _load_private_key directly, mocked below)

from scripts.kalshi_rewards import (  # noqa: E402
    INTEL_KEY,
    detect_changes,
    summarise_programs,
    write_jsonl,
    _build_headers,
    _load_prev_ids,
    _save_prev_ids,
    send_discord_alert,
    publish_to_redis,
    fetch_incentive_programs,
    fetch_balance,
    run,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

SAMPLE_PROGRAM_1 = {
    "id": "prog-vol-001",
    "market_ticker": "KXBTC-24NOV-T30000",
    "series_ticker": "KXBTC",
    "incentive_type": "volume",
    "start_date": "2026-01-01T00:00:00Z",
    "end_date": "2026-12-31T23:59:59Z",
    "period_reward": 500000,    # 500 000 centi-cents = $50 pool
    "paid_out": False,
    "target_size": 1000,
    "discount_factor_bps": None,
}

SAMPLE_PROGRAM_2 = {
    "id": "prog-liq-002",
    "market_ticker": "KXSPY-24NOV-T450",
    "series_ticker": "KXSPY",
    "incentive_type": "liquidity",
    "start_date": "2026-02-01T00:00:00Z",
    "end_date": "2026-06-30T23:59:59Z",
    "period_reward": 1000000,
    "paid_out": False,
    "target_size": None,
    "discount_factor_bps": 50,
}

SAMPLE_PROGRAM_PAID = {
    "id": "prog-vol-000",
    "market_ticker": "KXOLD-001",
    "series_ticker": "KXOLD",
    "incentive_type": "volume",
    "start_date": "2025-10-01T00:00:00Z",
    "end_date": "2025-12-31T23:59:59Z",
    "period_reward": 200000,
    "paid_out": True,
    "target_size": 500,
    "discount_factor_bps": None,
}


# ═══════════════════════════════════════════════════════════════════════════════
# _build_headers
# ═══════════════════════════════════════════════════════════════════════════════

class TestBuildHeaders:
    def test_returns_required_keys(self):
        fake_key = _FakePrivateKey()
        headers = _build_headers("key-abc", fake_key, "GET", "/trade-api/v2/incentive_programs")
        assert "KALSHI-ACCESS-KEY" in headers
        assert "KALSHI-ACCESS-SIGNATURE" in headers
        assert "KALSHI-ACCESS-TIMESTAMP" in headers
        assert "Content-Type" in headers

    def test_access_key_matches_input(self):
        fake_key = _FakePrivateKey()
        headers = _build_headers("my-key-id", fake_key, "GET", "/trade-api/v2/portfolio/balance")
        assert headers["KALSHI-ACCESS-KEY"] == "my-key-id"

    def test_timestamp_is_numeric_string(self):
        fake_key = _FakePrivateKey()
        headers = _build_headers("k", fake_key, "GET", "/trade-api/v2/incentive_programs")
        ts = headers["KALSHI-ACCESS-TIMESTAMP"]
        assert ts.isdigit()
        # Timestamp should be in milliseconds (13 digits)
        assert 12 <= len(ts) <= 14

    def test_signature_is_base64_encoded(self):
        import base64
        fake_key = _FakePrivateKey()
        headers = _build_headers("k", fake_key, "GET", "/trade-api/v2/incentive_programs")
        sig = headers["KALSHI-ACCESS-SIGNATURE"]
        # Should be decodeable as base64
        decoded = base64.b64decode(sig)
        assert len(decoded) > 0

    def test_different_paths_different_signatures(self):
        """Each path produces a different signed message."""
        fake_key = _FakePrivateKey()
        h1 = _build_headers("k", fake_key, "GET", "/trade-api/v2/incentive_programs")
        h2 = _build_headers("k", fake_key, "GET", "/trade-api/v2/portfolio/balance")
        assert h1["KALSHI-ACCESS-SIGNATURE"] != h2["KALSHI-ACCESS-SIGNATURE"]


# ═══════════════════════════════════════════════════════════════════════════════
# detect_changes
# ═══════════════════════════════════════════════════════════════════════════════

class TestDetectChanges:
    def test_new_programs_detected(self):
        result = detect_changes(
            current_ids=["a", "b", "c"],
            prev_ids=["a", "b"],
        )
        assert result["new_ids"] == ["c"]
        assert result["lost_ids"] == []

    def test_lost_programs_detected(self):
        result = detect_changes(
            current_ids=["a"],
            prev_ids=["a", "b", "c"],
        )
        assert result["new_ids"] == []
        assert sorted(result["lost_ids"]) == ["b", "c"]

    def test_no_changes(self):
        result = detect_changes(
            current_ids=["x", "y"],
            prev_ids=["x", "y"],
        )
        assert result["new_ids"] == []
        assert result["lost_ids"] == []

    def test_completely_replaced(self):
        result = detect_changes(
            current_ids=["new1", "new2"],
            prev_ids=["old1", "old2"],
        )
        assert set(result["new_ids"]) == {"new1", "new2"}
        assert set(result["lost_ids"]) == {"old1", "old2"}

    def test_empty_prev(self):
        result = detect_changes(current_ids=["a", "b"], prev_ids=[])
        assert set(result["new_ids"]) == {"a", "b"}
        assert result["lost_ids"] == []

    def test_empty_current(self):
        result = detect_changes(current_ids=[], prev_ids=["a"])
        assert result["new_ids"] == []
        assert result["lost_ids"] == ["a"]

    def test_both_empty(self):
        result = detect_changes(current_ids=[], prev_ids=[])
        assert result == {"new_ids": [], "lost_ids": []}

    def test_duplicate_ids_treated_as_set(self):
        """Duplicate IDs in input should not produce duplicate changes."""
        result = detect_changes(
            current_ids=["a", "a", "b"],
            prev_ids=["a"],
        )
        assert result["new_ids"] == ["b"]

    def test_results_are_sorted(self):
        result = detect_changes(
            current_ids=["c", "a", "b"],
            prev_ids=[],
        )
        assert result["new_ids"] == sorted(result["new_ids"])


# ═══════════════════════════════════════════════════════════════════════════════
# summarise_programs
# ═══════════════════════════════════════════════════════════════════════════════

class TestSummarisePrograms:
    def test_basic_fields_present(self):
        result = summarise_programs([SAMPLE_PROGRAM_1])
        assert len(result) == 1
        prog = result[0]
        assert prog["id"] == "prog-vol-001"
        assert prog["market_ticker"] == "KXBTC-24NOV-T30000"
        assert prog["incentive_type"] == "volume"
        assert prog["period_reward_cents"] == 500000
        assert prog["paid_out"] is False
        assert prog["target_size"] == 1000
        assert prog["discount_factor_bps"] is None

    def test_liquidity_program(self):
        result = summarise_programs([SAMPLE_PROGRAM_2])
        prog = result[0]
        assert prog["incentive_type"] == "liquidity"
        assert prog["discount_factor_bps"] == 50
        assert prog["target_size"] is None

    def test_multiple_programs(self):
        result = summarise_programs([SAMPLE_PROGRAM_1, SAMPLE_PROGRAM_2])
        assert len(result) == 2

    def test_empty_list(self):
        assert summarise_programs([]) == []

    def test_missing_fields_default_gracefully(self):
        """A program dict missing optional fields should not raise."""
        minimal = {"id": "min-001"}
        result = summarise_programs([minimal])
        assert result[0]["id"] == "min-001"
        assert result[0]["market_ticker"] == ""
        assert result[0]["period_reward_cents"] == 0
        assert result[0]["paid_out"] is False

    def test_paid_out_program(self):
        result = summarise_programs([SAMPLE_PROGRAM_PAID])
        assert result[0]["paid_out"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# Redis helpers (_load_prev_ids, _save_prev_ids)
# ═══════════════════════════════════════════════════════════════════════════════

class TestRedisHelpers:
    def test_load_prev_ids_returns_list_from_json(self):
        fake_r = MagicMock()
        fake_r.get.return_value = json.dumps(["id1", "id2"])
        result = _load_prev_ids(fake_r)
        assert result == ["id1", "id2"]

    def test_load_prev_ids_returns_empty_when_none(self):
        fake_r = MagicMock()
        fake_r.get.return_value = None
        result = _load_prev_ids(fake_r)
        assert result == []

    def test_load_prev_ids_returns_empty_on_exception(self):
        fake_r = MagicMock()
        fake_r.get.side_effect = Exception("connection refused")
        result = _load_prev_ids(fake_r)
        assert result == []

    def test_save_prev_ids_calls_set(self):
        fake_r = MagicMock()
        _save_prev_ids(fake_r, ["a", "b", "c"])
        fake_r.set.assert_called_once()
        call_args = fake_r.set.call_args
        assert call_args[0][0] == "kalshi:rewards_prev_ids"
        stored = json.loads(call_args[0][1])
        assert set(stored) == {"a", "b", "c"}

    def test_save_prev_ids_sets_ttl(self):
        fake_r = MagicMock()
        _save_prev_ids(fake_r, ["x"])
        call_kwargs = fake_r.set.call_args[1]
        assert call_kwargs.get("ex") == 172800  # 48h

    def test_save_prev_ids_does_not_raise_on_failure(self):
        fake_r = MagicMock()
        fake_r.set.side_effect = Exception("redis down")
        _save_prev_ids(fake_r, ["a"])  # should not raise


# ═══════════════════════════════════════════════════════════════════════════════
# publish_to_redis
# ═══════════════════════════════════════════════════════════════════════════════

class TestPublishToRedis:
    def test_publishes_correct_key(self):
        fake_r = MagicMock()
        with patch("scripts.kalshi_rewards._sync_client", return_value=fake_r):
            publish_to_redis({"active_promotions": [], "timestamp": "2026-03-07T12:00:00Z"})
        call_args = fake_r.set.call_args[0]
        assert call_args[0] == INTEL_KEY

    def test_published_payload_is_valid_json(self):
        fake_r = MagicMock()
        with patch("scripts.kalshi_rewards._sync_client", return_value=fake_r):
            publish_to_redis({"test": "value"})
        raw = fake_r.set.call_args[0][1]
        parsed = json.loads(raw)
        assert "value" in parsed
        assert "source_system" in parsed
        assert "timestamp" in parsed
        assert "confidence" in parsed

    def test_source_system_is_kalshi_rewards(self):
        fake_r = MagicMock()
        with patch("scripts.kalshi_rewards._sync_client", return_value=fake_r):
            publish_to_redis({"x": 1})
        raw = fake_r.set.call_args[0][1]
        parsed = json.loads(raw)
        assert parsed["source_system"] == "kalshi_rewards"

    def test_ttl_is_86400(self):
        fake_r = MagicMock()
        with patch("scripts.kalshi_rewards._sync_client", return_value=fake_r):
            publish_to_redis({})
        call_kwargs = fake_r.set.call_args[1]
        assert call_kwargs.get("ex") == 86400

    def test_does_not_raise_on_redis_failure(self):
        fake_r = MagicMock()
        fake_r.set.side_effect = Exception("timeout")
        with patch("scripts.kalshi_rewards._sync_client", return_value=fake_r):
            publish_to_redis({"test": 1})  # should not raise

    def test_value_field_contains_original_payload(self):
        fake_r = MagicMock()
        inner = {"active_promotions": [{"id": "p1"}], "timestamp": "2026-03-07T00:00:00Z"}
        with patch("scripts.kalshi_rewards._sync_client", return_value=fake_r):
            publish_to_redis(inner)
        raw = fake_r.set.call_args[0][1]
        parsed = json.loads(raw)
        assert parsed["value"]["active_promotions"][0]["id"] == "p1"


# ═══════════════════════════════════════════════════════════════════════════════
# write_jsonl
# ═══════════════════════════════════════════════════════════════════════════════

class TestWriteJsonl:
    def test_writes_valid_json_line(self, tmp_path):
        record = {
            "active_promotions": [{"id": "p1"}],
            "timestamp": "2026-03-07T12:00:00Z",
        }
        with patch("scripts.kalshi_rewards.ARCHIVE_DIR", str(tmp_path)):
            write_jsonl(record)

        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        filepath = tmp_path / f"rewards_{date_str}.jsonl"
        assert filepath.exists()
        line = filepath.read_text().strip()
        parsed = json.loads(line)
        assert parsed["active_promotions"][0]["id"] == "p1"

    def test_appends_multiple_records(self, tmp_path):
        with patch("scripts.kalshi_rewards.ARCHIVE_DIR", str(tmp_path)):
            write_jsonl({"run": 1})
            write_jsonl({"run": 2})

        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        lines = (tmp_path / f"rewards_{date_str}.jsonl").read_text().strip().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["run"] == 1
        assert json.loads(lines[1])["run"] == 2

    def test_does_not_raise_on_write_failure(self):
        with patch("scripts.kalshi_rewards.os.makedirs", side_effect=PermissionError("no")):
            write_jsonl({"test": 1})  # should not raise

    def test_jsonl_file_named_by_current_utc_date(self, tmp_path):
        with patch("scripts.kalshi_rewards.ARCHIVE_DIR", str(tmp_path)):
            write_jsonl({"x": 1})
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        expected = tmp_path / f"rewards_{date_str}.jsonl"
        assert expected.exists()


# ═══════════════════════════════════════════════════════════════════════════════
# send_discord_alert
# ═══════════════════════════════════════════════════════════════════════════════

class TestSendDiscordAlert:
    def test_no_op_when_no_webhook(self):
        with patch("scripts.kalshi_rewards.DISCORD_WEBHOOK_URL", ""):
            with patch("scripts.kalshi_rewards.requests.post") as mock_post:
                send_discord_alert({"new_ids": ["x"]}, [])
                mock_post.assert_not_called()

    def test_no_op_when_no_changes(self):
        with patch("scripts.kalshi_rewards.DISCORD_WEBHOOK_URL", "https://discord.invalid"):
            with patch("scripts.kalshi_rewards.requests.post") as mock_post:
                send_discord_alert({"new_ids": [], "lost_ids": []}, [])
                mock_post.assert_not_called()

    def test_sends_alert_on_new_programs(self):
        with patch("scripts.kalshi_rewards.DISCORD_WEBHOOK_URL", "https://discord.invalid/hook"), \
             patch.dict(os.environ, {"DISCORD_WEBHOOK_URL": "https://discord.invalid/hook"}), \
             patch("core.discord_notifier._default_notifier", None), \
             patch("core.discord_notifier.requests.post") as mock_post, \
             patch("core.discord_notifier.IntelReader.read", return_value=None):
            mock_post.return_value = MagicMock(status_code=204)
            send_discord_alert({"new_ids": ["prog-001"], "lost_ids": []}, [SAMPLE_PROGRAM_1])
            mock_post.assert_called_once()
            payload = mock_post.call_args[1]["json"]
            assert len(payload["embeds"]) == 1

    def test_sends_alert_on_lost_programs(self):
        with patch("scripts.kalshi_rewards.DISCORD_WEBHOOK_URL", "https://discord.invalid/hook"), \
             patch.dict(os.environ, {"DISCORD_WEBHOOK_URL": "https://discord.invalid/hook"}), \
             patch("core.discord_notifier._default_notifier", None), \
             patch("core.discord_notifier.requests.post") as mock_post, \
             patch("core.discord_notifier.IntelReader.read", return_value=None):
            mock_post.return_value = MagicMock(status_code=204)
            send_discord_alert({"new_ids": [], "lost_ids": ["old-001"]}, [])
            mock_post.assert_called_once()

    def test_does_not_raise_on_request_failure(self):
        with patch("scripts.kalshi_rewards.DISCORD_WEBHOOK_URL", "https://discord.invalid/hook"):
            with patch("scripts.kalshi_rewards.requests.post", side_effect=Exception("timeout")):
                send_discord_alert({"new_ids": ["x"], "lost_ids": []}, [])  # must not raise


# ═══════════════════════════════════════════════════════════════════════════════
# fetch_incentive_programs (mocked HTTP)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFetchIncentivePrograms:
    def _mock_response(self, programs):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"incentive_programs": programs}
        mock_resp.raise_for_status.return_value = None
        return mock_resp

    def test_returns_program_list(self):
        fake_key = _FakePrivateKey()
        with patch("scripts.kalshi_rewards.requests.get", return_value=self._mock_response([SAMPLE_PROGRAM_1])):
            result = fetch_incentive_programs("key-id", fake_key)
        assert len(result) == 1
        assert result[0]["id"] == "prog-vol-001"

    def test_returns_empty_list_on_http_error(self):
        fake_key = _FakePrivateKey()
        with patch("scripts.kalshi_rewards.requests.get", side_effect=Exception("timeout")):
            result = fetch_incentive_programs("key-id", fake_key)
        assert result == []

    def test_returns_empty_list_when_api_returns_no_key(self):
        fake_key = _FakePrivateKey()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}  # missing "incentive_programs" key
        mock_resp.raise_for_status.return_value = None
        with patch("scripts.kalshi_rewards.requests.get", return_value=mock_resp):
            result = fetch_incentive_programs("key-id", fake_key)
        assert result == []

    def test_uses_correct_status_param(self):
        fake_key = _FakePrivateKey()
        with patch("scripts.kalshi_rewards.requests.get", return_value=self._mock_response([])) as mock_get:
            fetch_incentive_programs("key-id", fake_key, status="paid_out")
        params = mock_get.call_args[1]["params"]
        assert params["status"] == "paid_out"

    def test_type_param_omitted_when_all(self):
        fake_key = _FakePrivateKey()
        with patch("scripts.kalshi_rewards.requests.get", return_value=self._mock_response([])) as mock_get:
            fetch_incentive_programs("key-id", fake_key, program_type="all")
        params = mock_get.call_args[1]["params"]
        assert "type" not in params

    def test_type_param_included_when_specific(self):
        fake_key = _FakePrivateKey()
        with patch("scripts.kalshi_rewards.requests.get", return_value=self._mock_response([])) as mock_get:
            fetch_incentive_programs("key-id", fake_key, program_type="volume")
        params = mock_get.call_args[1]["params"]
        assert params["type"] == "volume"


# ═══════════════════════════════════════════════════════════════════════════════
# fetch_balance (mocked HTTP)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFetchBalance:
    def test_returns_balance_dict(self):
        fake_key = _FakePrivateKey()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"balance": 125000, "portfolio_value": 50000}
        mock_resp.raise_for_status.return_value = None
        with patch("scripts.kalshi_rewards.requests.get", return_value=mock_resp):
            result = fetch_balance("key-id", fake_key)
        assert result["balance_cents"] == 125000
        assert result["portfolio_value_cents"] == 50000

    def test_returns_empty_dict_on_failure(self):
        fake_key = _FakePrivateKey()
        with patch("scripts.kalshi_rewards.requests.get", side_effect=Exception("network error")):
            result = fetch_balance("key-id", fake_key)
        assert result == {}

    def test_returns_zero_balance_when_missing_keys(self):
        fake_key = _FakePrivateKey()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status.return_value = None
        with patch("scripts.kalshi_rewards.requests.get", return_value=mock_resp):
            result = fetch_balance("key-id", fake_key)
        assert result["balance_cents"] == 0
        assert result["portfolio_value_cents"] == 0


# ═══════════════════════════════════════════════════════════════════════════════
# run() — end-to-end integration (all external I/O mocked)
# ═══════════════════════════════════════════════════════════════════════════════

class TestRun:
    def _patch_all(self, active=None, paid_out=None, upcoming=None, balance=None, prev_ids=None):
        """Helper to set up all mocks for run()."""
        if active is None:
            active = [SAMPLE_PROGRAM_1, SAMPLE_PROGRAM_2]
        if paid_out is None:
            paid_out = [SAMPLE_PROGRAM_PAID]
        if upcoming is None:
            upcoming = []
        if balance is None:
            balance = {"balance_cents": 10000, "portfolio_value_cents": 5000}
        if prev_ids is None:
            prev_ids = []

        patches = {
            "kalshi_api_key": patch("scripts.kalshi_rewards.KALSHI_API_KEY", "test-key-id"),
            "load_key": patch("scripts.kalshi_rewards._load_private_key", return_value=_FakePrivateKey()),
            "fetch_active": patch(
                "scripts.kalshi_rewards.fetch_incentive_programs",
                side_effect=lambda key, pk, status="active", **kw: (
                    active if status == "active"
                    else paid_out if status == "paid_out"
                    else upcoming
                ),
            ),
            "fetch_balance": patch("scripts.kalshi_rewards.fetch_balance", return_value=balance),
            "sync_client": patch("scripts.kalshi_rewards._sync_client"),
            "publish_redis": patch("scripts.kalshi_rewards.publish_to_redis"),
            "write_jsonl": patch("scripts.kalshi_rewards.write_jsonl"),
            "discord": patch("scripts.kalshi_rewards.send_discord_alert"),
        }
        return patches

    def test_returns_payload_dict(self):
        p = self._patch_all()
        with p["kalshi_api_key"], p["load_key"], p["fetch_active"], \
                p["fetch_balance"], p["sync_client"] as mock_rc, \
                p["publish_redis"], p["write_jsonl"], p["discord"]:
            # Mock Redis state methods
            mock_rc.return_value.__enter__ = MagicMock(return_value=mock_rc.return_value)
            mock_rc.return_value.get.return_value = None
            result = run()
        assert isinstance(result, dict)

    def test_payload_has_required_keys(self):
        p = self._patch_all()
        with p["kalshi_api_key"], p["load_key"], p["fetch_active"], \
                p["fetch_balance"], p["sync_client"] as mock_rc, \
                p["publish_redis"], p["write_jsonl"], p["discord"]:
            mock_rc.return_value.get.return_value = None
            result = run()
        assert "active_promotions" in result
        assert "recently_paid_out" in result
        assert "unclaimed_rewards" in result
        assert "program_counts" in result
        assert "changes" in result
        assert "timestamp" in result

    def test_active_promotions_are_summarised(self):
        p = self._patch_all()
        with p["kalshi_api_key"], p["load_key"], p["fetch_active"], \
                p["fetch_balance"], p["sync_client"] as mock_rc, \
                p["publish_redis"], p["write_jsonl"], p["discord"]:
            mock_rc.return_value.get.return_value = None
            result = run()
        assert len(result["active_promotions"]) == 2
        ids = {prog["id"] for prog in result["active_promotions"]}
        assert "prog-vol-001" in ids
        assert "prog-liq-002" in ids

    def test_program_counts_correct(self):
        p = self._patch_all()
        with p["kalshi_api_key"], p["load_key"], p["fetch_active"], \
                p["fetch_balance"], p["sync_client"] as mock_rc, \
                p["publish_redis"], p["write_jsonl"], p["discord"]:
            mock_rc.return_value.get.return_value = None
            result = run()
        assert result["program_counts"]["active"] == 2
        assert result["program_counts"]["recently_paid_out"] == 1

    def test_publish_redis_called_once(self):
        p = self._patch_all()
        with p["kalshi_api_key"], p["load_key"], p["fetch_active"], \
                p["fetch_balance"], p["sync_client"] as mock_rc, \
                p["publish_redis"] as mock_pub, p["write_jsonl"], p["discord"]:
            mock_rc.return_value.get.return_value = None
            run()
        mock_pub.assert_called_once()

    def test_write_jsonl_called_once(self):
        p = self._patch_all()
        with p["kalshi_api_key"], p["load_key"], p["fetch_active"], \
                p["fetch_balance"], p["sync_client"] as mock_rc, \
                p["publish_redis"], p["write_jsonl"] as mock_wj, p["discord"]:
            mock_rc.return_value.get.return_value = None
            run()
        mock_wj.assert_called_once()

    def test_returns_empty_dict_when_no_api_key(self):
        with patch("scripts.kalshi_rewards.KALSHI_API_KEY", ""):
            result = run()
        assert result == {}

    def test_returns_empty_dict_when_key_load_fails(self):
        with patch("scripts.kalshi_rewards.KALSHI_API_KEY", "test-key"), \
                patch("scripts.kalshi_rewards._load_private_key", return_value=None):
            result = run()
        assert result == {}

    def test_timestamp_is_iso_format(self):
        p = self._patch_all()
        with p["kalshi_api_key"], p["load_key"], p["fetch_active"], \
                p["fetch_balance"], p["sync_client"] as mock_rc, \
                p["publish_redis"], p["write_jsonl"], p["discord"]:
            mock_rc.return_value.get.return_value = None
            result = run()
        # Should be parseable as ISO datetime
        ts = result.get("timestamp", "")
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        assert parsed.year >= 2026

    def test_changes_new_ids_detected(self):
        """When prev snapshot is empty, all current programs are 'new'."""
        p = self._patch_all(prev_ids=[])
        with p["kalshi_api_key"], p["load_key"], p["fetch_active"], \
                p["fetch_balance"], p["sync_client"] as mock_rc, \
                p["publish_redis"], p["write_jsonl"], p["discord"]:
            mock_rc.return_value.get.return_value = None  # empty prev
            result = run()
        # All current IDs should appear as new
        assert set(result["changes"]["new_ids"]) == {"prog-vol-001", "prog-liq-002"}

    def test_balance_data_in_unclaimed_rewards(self):
        p = self._patch_all(balance={"balance_cents": 99999, "portfolio_value_cents": 11111})
        with p["kalshi_api_key"], p["load_key"], p["fetch_active"], \
                p["fetch_balance"], p["sync_client"] as mock_rc, \
                p["publish_redis"], p["write_jsonl"], p["discord"]:
            mock_rc.return_value.get.return_value = None
            result = run()
        assert result["unclaimed_rewards"]["balance_cents"] == 99999
