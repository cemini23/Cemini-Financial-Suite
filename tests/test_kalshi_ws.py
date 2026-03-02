"""
tests/test_kalshi_ws.py — Pure unit tests for the Kalshi WebSocket migration.

All tests are pure (no network, no Redis, no real WebSocket).
Async coroutines are executed with asyncio.run() from sync test functions.

Modules tested:
  - modules/market_rover/ws_client.py   (auth headers, backoff constants)
  - modules/market_rover/orderbook.py   (snapshot, delta, seq-gap detection)
  - modules/market_rover/oi_tracker.py  (OI signal generation)
  - modules/market_rover/liquidity_detector.py (depth spike detection)
"""

import asyncio
import json
import sys
import time
from pathlib import Path

import pytest

# ── Import new rover modules directly from their files ────────────────────────
# We bypass "Kalshi by Cemini/modules/market_rover/__init__.py" to avoid
# triggering the rover.py → app.core.config → pydantic_settings import chain,
# which is only resolvable inside the Docker container (not the test runner).
_REPO_ROOT = str(Path(__file__).parent.parent)
_ROVER_DIR = str(
    Path(__file__).parent.parent / "Kalshi by Cemini" / "modules" / "market_rover"
)
for _p in (_REPO_ROOT, _ROVER_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Direct flat imports — no package __init__.py is triggered
import ws_client as _ws_mod  # noqa: E402  (needed to ensure the module loads)
from ws_client import BACKOFF_INITIAL, BACKOFF_MAX, build_auth_headers  # noqa: E402
from orderbook import OrderBookManager  # noqa: E402
from oi_tracker import OITracker  # noqa: E402
from liquidity_detector import LiquidityDetector  # noqa: E402


# ── In-memory Redis stub ───────────────────────────────────────────────────────

class FakeRedis:
    """
    Async-compatible in-memory Redis substitute for unit tests.
    Implements the sorted-set, hash, list, string, and plain-set commands
    used by the WebSocket rover modules.
    """

    def __init__(self):
        # sorted sets: {key: [(score, member), ...]}  sorted by score ascending
        self._zsets: dict = {}
        self._hashes: dict = {}
        self._lists: dict = {}
        self._strings: dict = {}
        self._sets: dict = {}      # plain sets (SADD / SMEMBERS)

    # ── Sorted set ─────────────────────────────────────────────────────────────

    async def zadd(self, key, mapping: dict):
        """mapping = {member: score}"""
        existing = {m: s for s, m in self._zsets.get(key, [])}
        existing.update(mapping)
        self._zsets[key] = sorted(
            [(s, m) for m, s in existing.items()], key=lambda x: x[0]
        )

    async def zrange(self, key, start, stop, withscores=False):
        items = self._zsets.get(key, [])
        sliced = items[start:] if stop == -1 else items[start: stop + 1]
        if withscores:
            return [(m, s) for s, m in sliced]
        return [m for _, m in sliced]

    async def zrevrange(self, key, start, stop, withscores=False):
        items = list(reversed(self._zsets.get(key, [])))
        sliced = items[start:] if stop == -1 else items[start: stop + 1]
        if withscores:
            return [(m, s) for s, m in sliced]
        return [m for _, m in sliced]

    async def zrangebyscore(self, key, min_score, max_score):
        return [
            m for s, m in self._zsets.get(key, [])
            if min_score <= s <= max_score
        ]

    async def zrem(self, key, *members):
        if key in self._zsets:
            self._zsets[key] = [
                (s, m) for s, m in self._zsets[key] if m not in members
            ]

    async def delete(self, *keys):
        for key in keys:
            self._zsets.pop(key, None)
            self._hashes.pop(key, None)
            self._lists.pop(key, None)
            self._strings.pop(key, None)

    # ── Hash ───────────────────────────────────────────────────────────────────

    async def hset(self, key, mapping=None, **kwargs):
        if key not in self._hashes:
            self._hashes[key] = {}
        if mapping:
            self._hashes[key].update(mapping)
        self._hashes[key].update(kwargs)

    async def hgetall(self, key):
        return dict(self._hashes.get(key, {}))

    # ── List ───────────────────────────────────────────────────────────────────

    async def lpush(self, key, *values):
        if key not in self._lists:
            self._lists[key] = []
        for val in values:
            self._lists[key].insert(0, str(val))

    async def lrange(self, key, start, stop):
        items = self._lists.get(key, [])
        return items[start:] if stop == -1 else items[start: stop + 1]

    async def expire(self, key, seconds):
        pass  # no-op in tests

    # ── Plain set ──────────────────────────────────────────────────────────────

    async def sadd(self, key, *members):
        if key not in self._sets:
            self._sets[key] = set()
        self._sets[key].update(members)

    async def smembers(self, key):
        return set(self._sets.get(key, set()))

    async def srem(self, key, *members):
        if key in self._sets:
            for member in members:
                self._sets[key].discard(member)

    # ── String ─────────────────────────────────────────────────────────────────

    async def set(self, key, value, ex=None):
        self._strings[key] = str(value)

    async def get(self, key):
        return self._strings.get(key)


# ── Helpers ────────────────────────────────────────────────────────────────────

def arun(coro):
    """Run a coroutine synchronously (no pytest-asyncio needed)."""
    return asyncio.run(coro)


def make_snapshot(ticker, yes_levels, no_levels, seq=0):
    """Build a fake orderbook_snapshot WebSocket message."""
    return {
        "type": "orderbook_snapshot",
        "seq":  seq,
        "msg":  {
            "market_ticker": ticker,
            "yes": yes_levels,   # [[price, qty], ...]
            "no":  no_levels,
        },
    }


def make_delta(ticker, price, delta, side="yes", seq=1):
    """Build a fake orderbook_delta WebSocket message."""
    return {
        "type": "orderbook_delta",
        "seq":  seq,
        "msg":  {
            "market_ticker": ticker,
            "price": price,
            "delta": delta,
            "side":  side,
        },
    }


def make_trade(ticker, count, taker_side="yes"):
    """Build a fake trade WebSocket message."""
    return {
        "type": "trade",
        "msg": {
            "market_ticker": ticker,
            "count":         count,
            "taker_side":    taker_side,
            "yes_price":     55,
            "no_price":      45,
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
# Auth / backoff tests (no async needed)
# ══════════════════════════════════════════════════════════════════════════════

class TestAuthHeaders:
    def test_backoff_sequence(self):
        """Exponential backoff must follow: 1, 2, 4, 8, 16, 32, 60."""
        backoff = BACKOFF_INITIAL
        result = [backoff]
        for _ in range(6):
            backoff = min(backoff * 2, BACKOFF_MAX)
            result.append(backoff)
        assert result == [1, 2, 4, 8, 16, 32, 60]

    def test_backoff_never_exceeds_max(self):
        """Backoff cap must never exceed BACKOFF_MAX."""
        backoff = BACKOFF_INITIAL
        for _ in range(20):
            backoff = min(backoff * 2, BACKOFF_MAX)
        assert backoff == BACKOFF_MAX

    def test_build_auth_headers_keys(self):
        """build_auth_headers must return all three required header keys."""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.backends import default_backend

        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        headers = build_auth_headers("test-key-id", private_key)
        assert "KALSHI-ACCESS-KEY" in headers
        assert "KALSHI-ACCESS-SIGNATURE" in headers
        assert "KALSHI-ACCESS-TIMESTAMP" in headers
        assert headers["KALSHI-ACCESS-KEY"] == "test-key-id"

    def test_build_auth_headers_timestamp_is_recent(self):
        """The timestamp in auth headers must be within 10 seconds of now."""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.backends import default_backend

        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        before = int(time.time() * 1000)
        headers = build_auth_headers("key", private_key)
        after = int(time.time() * 1000)

        ts = int(headers["KALSHI-ACCESS-TIMESTAMP"])
        assert before <= ts <= after + 10_000

    def test_build_auth_headers_signature_is_base64(self):
        """Signature must be non-empty base64-encoded string."""
        import base64
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.backends import default_backend

        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        headers = build_auth_headers("key", private_key)
        sig = headers["KALSHI-ACCESS-SIGNATURE"]
        assert len(sig) > 0
        # Must decode without error
        decoded = base64.b64decode(sig)
        assert len(decoded) > 0


# ══════════════════════════════════════════════════════════════════════════════
# OrderBook tests
# ══════════════════════════════════════════════════════════════════════════════

TICKER = "BTCX-24-01"


class TestOrderBookSnapshot:
    def _make_ob(self):
        return OrderBookManager(FakeRedis())

    def test_snapshot_populates_yes_sorted_set(self):
        """After applying a snapshot, the yes-side sorted set must have all price levels."""
        ob = self._make_ob()
        snap = make_snapshot(TICKER, yes_levels=[[45, 100], [50, 200]], no_levels=[], seq=0)
        arun(ob.apply_snapshot(snap))

        members = arun(ob._r.zrange(f"kalshi:ob:{TICKER}:yes", 0, -1))
        assert "100@45" in members
        assert "200@50" in members

    def test_snapshot_populates_no_sorted_set(self):
        """No-side levels must be stored correctly."""
        ob = self._make_ob()
        snap = make_snapshot(TICKER, yes_levels=[], no_levels=[[40, 50], [35, 80]], seq=0)
        arun(ob.apply_snapshot(snap))

        members = arun(ob._r.zrange(f"kalshi:ob:{TICKER}:no", 0, -1))
        assert "50@40" in members
        assert "80@35" in members

    def test_snapshot_clears_previous_book(self):
        """Applying a new snapshot must wipe the old book first."""
        ob = self._make_ob()
        snap1 = make_snapshot(TICKER, [[45, 100]], [], seq=0)
        snap2 = make_snapshot(TICKER, [[60, 50]], [], seq=10)
        arun(ob.apply_snapshot(snap1))
        arun(ob.apply_snapshot(snap2))

        members = arun(ob._r.zrange(f"kalshi:ob:{TICKER}:yes", 0, -1))
        assert "100@45" not in members
        assert "50@60" in members

    def test_snapshot_sets_expected_seq(self):
        """After snapshot with seq=5, expected next delta seq must be 6."""
        ob = self._make_ob()
        snap = make_snapshot(TICKER, [[45, 100]], [], seq=5)
        arun(ob.apply_snapshot(snap))
        assert ob._expected_seq[TICKER] == 6

    def test_snapshot_bbo_cached(self):
        """BBO hash must be populated after snapshot."""
        ob = self._make_ob()
        snap = make_snapshot(TICKER, yes_levels=[[45, 100]], no_levels=[[50, 80]], seq=0)
        arun(ob.apply_snapshot(snap))

        bbo = arun(ob._r.hgetall(f"kalshi:ob:{TICKER}:bbo"))
        assert bbo["best_bid"] == "45"
        assert bbo["best_ask"] == "50"   # 100 - 50 = 50
        assert bbo["spread"] == "5"


class TestOrderBookDelta:
    def _seeded_ob(self):
        ob = OrderBookManager(FakeRedis())
        snap = make_snapshot(TICKER, yes_levels=[[45, 100], [50, 200]], no_levels=[], seq=0)
        arun(ob.apply_snapshot(snap))
        return ob

    def test_delta_increases_qty_at_price_level(self):
        """Positive delta must increase the quantity at the given price level."""
        ob = self._seeded_ob()
        delta = make_delta(TICKER, price=45, delta=+50, side="yes", seq=1)
        ok = arun(ob.apply_delta(delta))
        assert ok is True

        members = arun(ob._r.zrange(f"kalshi:ob:{TICKER}:yes", 0, -1))
        assert "150@45" in members   # 100 + 50 = 150
        assert "100@45" not in members

    def test_delta_decreases_qty_at_price_level(self):
        """Negative delta must reduce the quantity at the price level."""
        ob = self._seeded_ob()
        delta = make_delta(TICKER, price=50, delta=-100, side="yes", seq=1)
        arun(ob.apply_delta(delta))

        members = arun(ob._r.zrange(f"kalshi:ob:{TICKER}:yes", 0, -1))
        assert "100@50" in members   # 200 - 100 = 100

    def test_delta_removes_level_when_qty_reaches_zero(self):
        """Depleting a level to zero must remove it from the sorted set."""
        ob = self._seeded_ob()
        delta = make_delta(TICKER, price=45, delta=-100, side="yes", seq=1)
        arun(ob.apply_delta(delta))

        members = arun(ob._r.zrange(f"kalshi:ob:{TICKER}:yes", 0, -1))
        assert not any("@45" in m for m in members), "Level should be removed at qty=0"

    def test_delta_adds_new_price_level(self):
        """Delta at a price with no existing qty should create a new level."""
        ob = self._seeded_ob()
        delta = make_delta(TICKER, price=55, delta=+75, side="yes", seq=1)
        arun(ob.apply_delta(delta))

        members = arun(ob._r.zrange(f"kalshi:ob:{TICKER}:yes", 0, -1))
        assert "75@55" in members

    def test_delta_seq_advances_expected(self):
        """Expected seq must increment by 1 for each valid delta."""
        ob = self._seeded_ob()
        assert ob._expected_seq[TICKER] == 1

        arun(ob.apply_delta(make_delta(TICKER, 45, +10, seq=1)))
        assert ob._expected_seq[TICKER] == 2

        arun(ob.apply_delta(make_delta(TICKER, 45, +10, seq=2)))
        assert ob._expected_seq[TICKER] == 3


class TestOrderBookSeqGap:
    def test_seq_gap_returns_false(self):
        """A delta with unexpected seq must return False to trigger re-snapshot."""
        ob = OrderBookManager(FakeRedis())
        snap = make_snapshot(TICKER, [[45, 100]], [], seq=0)
        arun(ob.apply_snapshot(snap))  # expects seq=1 next

        # Send seq=5 instead of 1 → gap
        delta = make_delta(TICKER, price=45, delta=+10, seq=5)
        ok = arun(ob.apply_delta(delta))
        assert ok is False

    def test_seq_gap_clears_expected_seq(self):
        """After a seq gap, expected_seq must be cleared so the next snapshot re-initialises."""
        ob = OrderBookManager(FakeRedis())
        snap = make_snapshot(TICKER, [[45, 100]], [], seq=0)
        arun(ob.apply_snapshot(snap))

        delta = make_delta(TICKER, price=45, delta=+10, seq=99)
        arun(ob.apply_delta(delta))

        assert TICKER not in ob._expected_seq

    def test_delta_without_prior_snapshot_succeeds(self):
        """A delta before any snapshot (no expected_seq) should apply without gap error."""
        ob = OrderBookManager(FakeRedis())
        delta = make_delta(TICKER, price=45, delta=+100, seq=1)
        ok = arun(ob.apply_delta(delta))
        assert ok is True  # no expected_seq set → no gap check


# ══════════════════════════════════════════════════════════════════════════════
# OI Tracker tests
# ══════════════════════════════════════════════════════════════════════════════

class TestOITracker:
    def test_get_signal_rising_conviction(self):
        """OI change > 2% of total must produce RISING_CONVICTION."""
        tracker = OITracker(FakeRedis(), publisher=None)
        signal = tracker.get_signal(total=1000, oi_1h_change=25)
        assert signal == "RISING_CONVICTION"

    def test_get_signal_falling_conviction(self):
        """This tests a negative volume signal; for rolling windows, still returns FALLING."""
        tracker = OITracker(FakeRedis(), publisher=None)
        signal = tracker.get_signal(total=1000, oi_1h_change=-25)
        assert signal == "FALLING_CONVICTION"

    def test_get_signal_below_threshold_returns_none(self):
        """OI change below the 2% threshold must return None (no signal)."""
        tracker = OITracker(FakeRedis(), publisher=None)
        signal = tracker.get_signal(total=1000, oi_1h_change=10)  # 1% < 2%
        assert signal is None

    def test_get_signal_zero_total_returns_none(self):
        """Division by zero guard: zero total must return None."""
        tracker = OITracker(FakeRedis(), publisher=None)
        signal = tracker.get_signal(total=0, oi_1h_change=100)
        assert signal is None

    def test_process_trade_accumulates_volume(self):
        """Each processed trade must increase total_contracts in Redis."""
        redis = FakeRedis()
        tracker = OITracker(redis, publisher=None)
        trade = make_trade("BTCX-24", count=50)

        arun(tracker.process_trade(trade))
        state = arun(redis.hgetall("kalshi:oi:BTCX-24"))
        assert int(state["total_contracts"]) == 50

        arun(tracker.process_trade(trade))
        state = arun(redis.hgetall("kalshi:oi:BTCX-24"))
        assert int(state["total_contracts"]) == 100

    def test_process_trade_publishes_signal_on_threshold(self):
        """When 1h volume exceeds 2% of total, the publisher must be called."""
        published = []

        class MockPublisher:
            @staticmethod
            async def publish_async(key, value, source, confidence=1.0):
                published.append((key, value))

        redis = FakeRedis()
        tracker = OITracker(redis, publisher=MockPublisher)

        # Seed total so 1h change crosses the 2% threshold
        # We'll do 26 trades of 1 contract each (total=26, 1h_change=26 → 100% > 2%)
        for _ in range(26):
            arun(tracker.process_trade(make_trade("ETH-24", count=1)))

        assert any(k == "intel:kalshi_oi" for k, _ in published), (
            "Signal should have been published to intel:kalshi_oi"
        )

    def test_process_trade_ignores_zero_count(self):
        """Trades with count=0 must not update state."""
        redis = FakeRedis()
        tracker = OITracker(redis, publisher=None)
        arun(tracker.process_trade(make_trade("BTCX-24", count=0)))
        state = arun(redis.hgetall("kalshi:oi:BTCX-24"))
        assert state == {}  # nothing written


# ══════════════════════════════════════════════════════════════════════════════
# Liquidity Detector tests
# ══════════════════════════════════════════════════════════════════════════════

class TestLiquidityDetector:
    def test_compute_sigma_normal_distribution(self):
        """Given history with known stats, compute_sigma must return correct value."""
        history = [100.0] * 10          # mean=100, stddev=0 → but we need nonzero stddev
        history[0] = 110.0              # slight variance
        sigma = LiquidityDetector.compute_sigma(history, current_depth=110.0)
        assert sigma > 0

    def test_compute_sigma_zero_returns_zero(self):
        """When all history values are identical (stddev=0), sigma must be 0."""
        history = [500.0] * 20
        sigma = LiquidityDetector.compute_sigma(history, current_depth=500.0)
        assert sigma == 0.0

    def test_compute_sigma_above_two_triggers(self):
        """Injecting a depth far above the mean must produce sigma > 2."""
        # mean=100, stddev=10 → depth=125 → sigma=(125-100)/10=2.5
        history = [90.0, 100.0, 110.0, 100.0, 100.0,
                   90.0, 100.0, 110.0, 100.0, 100.0]
        sigma = LiquidityDetector.compute_sigma(history, current_depth=125.0)
        assert sigma > 2.0

    def test_no_alert_below_threshold(self):
        """Depth changes within 2σ must not trigger any publish."""
        published = []

        class MockPub:
            @staticmethod
            async def publish_async(key, value, source, confidence=1.0):
                published.append(value)

        class MockOB:
            async def get_total_depth(self, ticker, side="yes"):
                return 100  # always 100 → no spike

        redis = FakeRedis()
        detector = LiquidityDetector(redis, MockOB(), publisher=MockPub)

        # Seed 15 history entries with slight variation (mean≈100, σ≈3)
        # MockOB returns 100 as current depth → within 2σ → no alert
        hist_key = "kalshi:liq:BTC-X:yes_hist"
        now = time.time()
        base_depths = [97, 100, 103, 100, 98, 102, 99, 101, 100, 100,
                       97, 103, 100, 100, 100]
        for idx, depth_val in enumerate(base_depths):
            entry = json.dumps({"depth": depth_val, "ts": now - (15 - idx) * 60})
            arun(redis.lpush(hist_key, entry))

        arun(detector.on_orderbook_update("BTC-X"))
        assert published == [], "No spike should be published when depth matches history"

    def test_alert_on_large_spike(self):
        """Injecting depth >> mean must trigger a liquidity spike alert."""
        published = []

        class MockPub:
            @staticmethod
            async def publish_async(key, value, source, confidence=1.0):
                published.append((key, value))

        class MockOB:
            async def get_total_depth(self, ticker, side="yes"):
                return 5000 if side == "yes" else 100  # massive spike on yes side

        redis = FakeRedis()
        detector = LiquidityDetector(redis, MockOB(), publisher=MockPub)

        # Seed history: 15 entries with slight variation around 100
        # (need non-zero stddev so the spike at 5000 registers)
        hist_key = "kalshi:liq:TICKER:yes_hist"
        now = time.time()
        base_depths = [95, 100, 105, 100, 98, 102, 99, 101, 100, 100,
                       97, 103, 100, 100, 100]
        for idx, depth_val in enumerate(base_depths):
            entry = json.dumps({"depth": depth_val, "ts": now - (15 - idx) * 60})
            arun(redis.lpush(hist_key, entry))

        arun(detector.on_orderbook_update("TICKER"))

        spike_keys = [k for k, _ in published if k == "intel:kalshi_liquidity_spike"]
        assert spike_keys, "Liquidity spike alert must be published for 5000 vs mean=100"


# ══════════════════════════════════════════════════════════════════════════════
# Total depth helper tests
# ══════════════════════════════════════════════════════════════════════════════

class TestTotalDepth:
    def test_get_total_depth_sums_all_levels(self):
        """get_total_depth must sum quantities across all price levels."""
        redis = FakeRedis()
        ob = OrderBookManager(redis)
        snap = make_snapshot(
            "ETH-24",
            yes_levels=[[45, 100], [50, 200], [55, 150]],
            no_levels=[],
            seq=0,
        )
        arun(ob.apply_snapshot(snap))

        depth = arun(ob.get_total_depth("ETH-24", "yes"))
        assert depth == 450   # 100 + 200 + 150

    def test_get_total_depth_empty_book_returns_zero(self):
        """Empty order book must return zero depth."""
        redis = FakeRedis()
        ob = OrderBookManager(redis)
        depth = arun(ob.get_total_depth("EMPTY-MKT", "yes"))
        assert depth == 0
