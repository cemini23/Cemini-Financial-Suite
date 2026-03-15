"""
Tests for trading_playbook/sector_rotation.py (Step 25).

All tests are pure — no network, no Redis, no Postgres.
All I/O is mocked via unittest.mock.
"""

from __future__ import annotations

import sys
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Ensure repo root on path for imports
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from trading_playbook.sector_rotation import (
    DEFENSIVE_SECTORS,
    OFFENSIVE_SECTORS,
    SECTOR_ROTATION_TTL,
    SECTOR_ETFS,
    classify_quadrant,
    compute_rotation_bias,
    compute_rs_momentum,
    compute_rs_ratio,
    rank_sectors,
    run_sector_rotation,
)
from cemini_contracts.sector import SectorRotationIntel, SectorSnapshot


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_prices(
    sector_prices: list[float],
    spy_prices: list[float],
    sector_sym: str = "XLK",
) -> pd.DataFrame:
    """Build a small price DataFrame with one sector + SPY."""
    n = min(len(sector_prices), len(spy_prices))
    dates = pd.date_range("2026-01-01", periods=n, freq="B")
    return pd.DataFrame(
        {sector_sym: sector_prices[:n], "SPY": spy_prices[:n]},
        index=dates,
    )


def _make_snapshot(
    symbol: str = "XLK",
    rs_ratio: float = 102.0,
    rs_momentum: float = 1.0,
    quadrant: str = "LEADING",
    rank: int = 1,
) -> SectorSnapshot:
    return SectorSnapshot(
        symbol=symbol,
        name=SECTOR_ETFS.get(symbol, "Unknown"),
        rs_ratio=rs_ratio,
        rs_momentum=rs_momentum,
        rank=rank,
        quadrant=quadrant,
    )


# ---------------------------------------------------------------------------
# RS Ratio tests
# ---------------------------------------------------------------------------


class TestComputeRsRatio:
    def test_sector_outperforms_spy(self):
        """ETF up 5%, SPY up 2% → RS Ratio > 100."""
        spy = [100.0, 101.0, 102.0]  # +2%
        etf = [100.0, 102.0, 105.0]  # +5%
        prices = _make_prices(etf, spy)
        result = compute_rs_ratio(prices, "XLK", lookback_days=3)
        assert result is not None
        assert result > 100.0

    def test_sector_underperforms_spy(self):
        """ETF up 1%, SPY up 4% → RS Ratio < 100."""
        spy = [100.0, 102.0, 104.0]  # +4%
        etf = [100.0, 100.5, 101.0]  # +1%
        prices = _make_prices(etf, spy)
        result = compute_rs_ratio(prices, "XLK", lookback_days=3)
        assert result is not None
        assert result < 100.0

    def test_sector_matches_spy(self):
        """ETF and SPY move identically → RS Ratio ≈ 100."""
        prices_list = [100.0, 101.0, 102.0, 103.0]
        prices = _make_prices(prices_list, prices_list)
        result = compute_rs_ratio(prices, "XLK", lookback_days=4)
        assert result is not None
        assert abs(result - 100.0) < 0.01

    def test_missing_sector_returns_none(self):
        """Missing sector column → returns None, no crash."""
        prices = pd.DataFrame({"SPY": [100.0, 101.0, 102.0]})
        result = compute_rs_ratio(prices, "XLK", lookback_days=3)
        assert result is None

    def test_missing_spy_returns_none(self):
        """Missing SPY column → returns None."""
        prices = pd.DataFrame({"XLK": [100.0, 101.0, 102.0]})
        result = compute_rs_ratio(prices, "XLK", lookback_days=3)
        assert result is None

    def test_single_row_returns_none(self):
        """Only 1 row → cannot compute ratio (div by self is trivial, need 2+)."""
        prices = _make_prices([100.0], [100.0])
        result = compute_rs_ratio(prices, "XLK", lookback_days=1)
        assert result is None

    def test_normalized_to_100_at_start(self):
        """RS Ratio of 100 means equal performance over the window."""
        spy = [200.0, 210.0, 220.0]
        etf = [50.0, 52.5, 55.0]  # same % moves as SPY
        prices = _make_prices(etf, spy)
        result = compute_rs_ratio(prices, "XLK", lookback_days=3)
        assert result is not None
        assert abs(result - 100.0) < 0.01


# ---------------------------------------------------------------------------
# RS Momentum tests
# ---------------------------------------------------------------------------


class TestComputeRsMomentum:
    def test_positive_momentum_when_accelerating(self):
        """Sector gaining vs SPY over time → positive momentum."""
        # SPY flat, sector rising
        spy = [100.0] * 10
        etf = [100.0, 100.5, 101.0, 101.5, 102.0, 102.5, 103.0, 103.5, 104.0, 104.5]
        prices = _make_prices(etf, spy)
        result = compute_rs_momentum(prices, "XLK", momentum_window=5)
        assert result is not None
        assert result > 0.0

    def test_negative_momentum_when_decelerating(self):
        """Sector losing vs SPY over time → negative momentum."""
        spy = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0]
        etf = [100.0] * 10  # flat while SPY rises
        prices = _make_prices(etf, spy)
        result = compute_rs_momentum(prices, "XLK", momentum_window=5)
        assert result is not None
        assert result < 0.0

    def test_insufficient_data_returns_none(self):
        """Fewer rows than momentum_window+1 → None."""
        prices = _make_prices([100.0, 101.0], [100.0, 101.0])
        result = compute_rs_momentum(prices, "XLK", momentum_window=5)
        assert result is None

    def test_missing_sector_returns_none(self):
        prices = pd.DataFrame({"SPY": [100.0] * 10})
        result = compute_rs_momentum(prices, "XLK")
        assert result is None


# ---------------------------------------------------------------------------
# Quadrant classification tests
# ---------------------------------------------------------------------------


class TestClassifyQuadrant:
    def test_leading(self):
        assert classify_quadrant(rs_ratio=102.0, rs_momentum=1.5) == "LEADING"

    def test_weakening(self):
        assert classify_quadrant(rs_ratio=101.0, rs_momentum=-0.5) == "WEAKENING"

    def test_lagging(self):
        assert classify_quadrant(rs_ratio=98.0, rs_momentum=-1.0) == "LAGGING"

    def test_improving(self):
        assert classify_quadrant(rs_ratio=99.0, rs_momentum=0.5) == "IMPROVING"

    def test_boundary_exactly_100_ratio(self):
        """RS Ratio = exactly 100 with positive momentum → LEADING."""
        assert classify_quadrant(rs_ratio=100.0, rs_momentum=0.1) == "LEADING"

    def test_boundary_zero_momentum(self):
        """RS Ratio > 100 with exactly zero momentum → LEADING (not WEAKENING)."""
        assert classify_quadrant(rs_ratio=101.0, rs_momentum=0.0) == "LEADING"


# ---------------------------------------------------------------------------
# Ranking tests
# ---------------------------------------------------------------------------


class TestRankSectors:
    def test_basic_ranking(self):
        rs = {"XLK": 105.0, "XLF": 103.0, "XLP": 98.0}
        ranks = rank_sectors(rs)
        assert ranks["XLK"] == 1
        assert ranks["XLF"] == 2
        assert ranks["XLP"] == 3

    def test_empty_input(self):
        assert rank_sectors({}) == {}

    def test_ties_get_same_rank(self):
        rs = {"XLK": 105.0, "XLF": 105.0, "XLP": 98.0}
        ranks = rank_sectors(rs)
        assert ranks["XLK"] == ranks["XLF"] == 1
        # XLP should be rank 3 (dense rank)
        assert ranks["XLP"] == 3

    def test_single_sector(self):
        ranks = rank_sectors({"XLK": 103.0})
        assert ranks["XLK"] == 1

    def test_all_equal(self):
        rs = {"XLK": 100.0, "XLF": 100.0, "XLP": 100.0}
        ranks = rank_sectors(rs)
        assert all(v == 1 for v in ranks.values())


# ---------------------------------------------------------------------------
# Offensive/defensive bias tests
# ---------------------------------------------------------------------------


class TestComputeRotationBias:
    def test_risk_on_when_offensive_leads(self):
        snapshots = {
            "XLK": _make_snapshot("XLK", quadrant="LEADING"),
            "XLY": _make_snapshot("XLY", quadrant="IMPROVING"),
            "XLF": _make_snapshot("XLF", quadrant="LEADING"),
            "XLP": _make_snapshot("XLP", quadrant="LAGGING"),
            "XLU": _make_snapshot("XLU", quadrant="LAGGING"),
        }
        off, defn, bias = compute_rotation_bias(snapshots)
        assert off == 3
        assert defn == 0
        assert bias == "RISK_ON"

    def test_risk_off_when_defensive_leads(self):
        snapshots = {
            "XLP": _make_snapshot("XLP", quadrant="LEADING"),
            "XLU": _make_snapshot("XLU", quadrant="IMPROVING"),
            "XLV": _make_snapshot("XLV", quadrant="LEADING"),
            "XLK": _make_snapshot("XLK", quadrant="LAGGING"),
            "XLY": _make_snapshot("XLY", quadrant="LAGGING"),
        }
        off, defn, bias = compute_rotation_bias(snapshots)
        assert defn == 3
        assert off == 0
        assert bias == "RISK_OFF"

    def test_neutral_when_tied(self):
        snapshots = {
            "XLK": _make_snapshot("XLK", quadrant="LEADING"),
            "XLP": _make_snapshot("XLP", quadrant="LEADING"),
        }
        off, defn, bias = compute_rotation_bias(snapshots)
        assert off == 1
        assert defn == 1
        assert bias == "NEUTRAL"

    def test_xle_does_not_count_as_offensive_or_defensive(self):
        """XLE is cyclical — should not affect offensive or defensive score."""
        snapshots = {
            "XLE": _make_snapshot("XLE", quadrant="LEADING"),
        }
        off, defn, bias = compute_rotation_bias(snapshots)
        assert off == 0
        assert defn == 0
        assert bias == "NEUTRAL"

    def test_weakening_and_lagging_do_not_score(self):
        """Only LEADING and IMPROVING quadrants score."""
        snapshots = {
            "XLK": _make_snapshot("XLK", quadrant="WEAKENING"),
            "XLY": _make_snapshot("XLY", quadrant="LAGGING"),
            "XLP": _make_snapshot("XLP", quadrant="IMPROVING"),
        }
        off, defn, bias = compute_rotation_bias(snapshots)
        assert off == 0   # XLK weakening, XLY lagging — neither scores
        assert defn == 1  # XLP improving scores
        assert bias == "RISK_OFF"


# ---------------------------------------------------------------------------
# run_sector_rotation integration tests (mocked DB + Redis)
# ---------------------------------------------------------------------------


class TestRunSectorRotation:
    def _mock_conn(self, rows):
        """Build a mock psycopg2 connection that returns *rows* from fetchall."""
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = rows
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        return mock_conn

    def _sector_rows(self, n_days: int = 25) -> list[tuple]:
        """Generate synthetic DB rows for SPY + all 11 sector ETFs."""
        import datetime as dt
        rows = []
        base_date = dt.date(2026, 1, 1)
        for day_offset in range(n_days):
            trade_date = base_date + dt.timedelta(days=day_offset)
            # SPY flat at 500
            rows.append(("SPY", trade_date, 500.0 + day_offset * 0.1))
            for sym in SECTOR_ETFS:
                # Sector ETFs all slightly outperform SPY
                rows.append((sym, trade_date, 100.0 + day_offset * 0.15))
        return rows

    @patch("trading_playbook.sector_rotation.IntelPublisher.publish")
    def test_publishes_to_intel_bus(self, mock_publish):
        conn = self._mock_conn(self._sector_rows(25))
        result = run_sector_rotation(conn)
        assert result is not None
        mock_publish.assert_called_once()
        call_kwargs = mock_publish.call_args
        assert call_kwargs.kwargs.get("key") == "intel:sector_rotation" or call_kwargs.args[0] == "intel:sector_rotation"

    @patch("trading_playbook.sector_rotation.IntelPublisher.publish")
    def test_publishes_with_correct_ttl(self, mock_publish):
        conn = self._mock_conn(self._sector_rows(25))
        run_sector_rotation(conn)
        call_kwargs = mock_publish.call_args
        ttl = call_kwargs.kwargs.get("ttl", None)
        if ttl is None and len(call_kwargs.args) > 4:
            ttl = call_kwargs.args[4]
        assert ttl == SECTOR_ROTATION_TTL

    @patch("trading_playbook.sector_rotation.IntelPublisher.publish")
    def test_returns_sector_rotation_intel(self, mock_publish):
        conn = self._mock_conn(self._sector_rows(25))
        result = run_sector_rotation(conn)
        assert isinstance(result, SectorRotationIntel)
        assert len(result.sectors) > 0
        assert result.rotation_bias in ("RISK_ON", "RISK_OFF", "NEUTRAL")

    @patch("trading_playbook.sector_rotation.IntelPublisher.publish")
    def test_top_3_and_bottom_3_populated(self, mock_publish):
        conn = self._mock_conn(self._sector_rows(25))
        result = run_sector_rotation(conn)
        assert result is not None
        assert len(result.top_3) <= 3
        assert len(result.bottom_3) <= 3

    @patch("trading_playbook.sector_rotation.IntelPublisher.publish")
    def test_no_spy_data_returns_none(self, mock_publish):
        """If SPY missing from ticks, returns None gracefully."""
        rows = [("XLK", "2026-01-01", 100.0), ("XLK", "2026-01-02", 101.0)]
        conn = self._mock_conn(rows)
        result = run_sector_rotation(conn)
        assert result is None
        mock_publish.assert_not_called()

    @patch("trading_playbook.sector_rotation.IntelPublisher.publish")
    def test_empty_db_returns_none(self, mock_publish):
        conn = self._mock_conn([])
        result = run_sector_rotation(conn)
        assert result is None
        mock_publish.assert_not_called()

    @patch("trading_playbook.sector_rotation.IntelPublisher.publish")
    def test_db_exception_returns_none(self, mock_publish):
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = Exception("DB error")
        result = run_sector_rotation(mock_conn)
        assert result is None
        mock_publish.assert_not_called()

    @patch("trading_playbook.sector_rotation.IntelPublisher.publish")
    def test_missing_some_etfs_still_runs(self, mock_publish):
        """If only SPY + a few ETFs have data, the rest are excluded gracefully."""
        import datetime as dt
        rows = []
        base = dt.date(2026, 1, 1)
        for i in range(25):
            d = base + dt.timedelta(days=i)
            rows.append(("SPY", d, 500.0 + i * 0.1))
            rows.append(("XLK", d, 100.0 + i * 0.2))  # only XLK has data
        conn = self._mock_conn(rows)
        result = run_sector_rotation(conn)
        # Should succeed with just XLK
        assert result is not None
        assert "XLK" in result.sectors

    @patch("trading_playbook.sector_rotation.IntelPublisher.publish")
    def test_all_sectors_flat_produces_100_rs_ratio(self, mock_publish):
        """When sector and SPY move identically, RS Ratio ≈ 100."""
        import datetime as dt
        rows = []
        base = dt.date(2026, 1, 1)
        for i in range(25):
            d = base + dt.timedelta(days=i)
            price = 100.0 + i * 0.5
            rows.append(("SPY", d, price))
            rows.append(("XLK", d, price))  # identical to SPY
        conn = self._mock_conn(rows)
        result = run_sector_rotation(conn)
        assert result is not None
        if "XLK" in result.sectors:
            assert abs(result.sectors["XLK"].rs_ratio - 100.0) < 0.5


# ---------------------------------------------------------------------------
# Pydantic contract validation tests
# ---------------------------------------------------------------------------


class TestSectorContracts:
    def test_sector_snapshot_valid(self):
        snap = SectorSnapshot(
            symbol="XLK",
            name="Technology",
            rs_ratio=105.3,
            rs_momentum=2.1,
            rank=1,
            quadrant="LEADING",
        )
        assert snap.symbol == "XLK"
        assert snap.quadrant == "LEADING"

    def test_sector_snapshot_quadrant_validation(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SectorSnapshot(
                symbol="XLK",
                name="Technology",
                rs_ratio=105.0,
                rs_momentum=1.0,
                rank=1,
                quadrant="INVALID_QUADRANT",  # type: ignore[arg-type]
            )

    def test_sector_rotation_intel_valid(self):
        snap = _make_snapshot("XLK")
        intel = SectorRotationIntel(
            timestamp=datetime.now(timezone.utc),
            lookback_days=21,
            sectors={"XLK": snap},
            top_3=["XLK"],
            bottom_3=["XLU"],
            rotation_bias="RISK_ON",
            offensive_score=3,
            defensive_score=1,
        )
        assert intel.rotation_bias == "RISK_ON"
        assert intel.lookback_days == 21

    def test_sector_rotation_intel_bias_validation(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SectorRotationIntel(
                rotation_bias="UNKNOWN_BIAS",  # type: ignore[arg-type]
            )

    def test_sector_rotation_intel_defaults(self):
        """SectorRotationIntel can be created with minimal args."""
        intel = SectorRotationIntel()
        assert intel.rotation_bias == "NEUTRAL"
        assert intel.sectors == {}
        assert isinstance(intel.timestamp, datetime)


# ---------------------------------------------------------------------------
# Sector definitions sanity tests
# ---------------------------------------------------------------------------


class TestSectorDefinitions:
    def test_offensive_and_defensive_are_disjoint(self):
        assert OFFENSIVE_SECTORS.isdisjoint(DEFENSIVE_SECTORS)

    def test_xle_is_neither_offensive_nor_defensive(self):
        assert "XLE" not in OFFENSIVE_SECTORS
        assert "XLE" not in DEFENSIVE_SECTORS

    def test_all_11_sector_etfs_defined(self):
        expected = {"XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"}
        assert set(SECTOR_ETFS.keys()) == expected

    def test_sector_rotation_ttl_greater_than_default_intel_ttl(self):
        """Sector rotation TTL (3600) must exceed the default IntelBus TTL (300)."""
        assert SECTOR_ROTATION_TTL > 300
