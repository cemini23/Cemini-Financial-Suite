"""
Cemini Financial Suite — Sector Rotation Monitor (Step 25)

Computes relative strength (RS) of 11 SPDR sector ETFs vs SPY using
RRG-style quadrant classification (Leading / Weakening / Lagging / Improving).

Data source: raw_market_ticks PostgreSQL table (TimescaleDB).
No external API calls — all data from existing ingestion pipeline.

Published to: intel:sector_rotation (TTL=3600, refresh every 30 min)

Usage:
    from trading_playbook.sector_rotation import run_sector_rotation
    run_sector_rotation(db_conn)   # pass existing psycopg2 connection
"""

from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from cemini_contracts._compat import safe_dump, safe_validate
from cemini_contracts.sector import SectorRotationIntel, SectorSnapshot
from core.intel_bus import IntelPublisher

logger = logging.getLogger("playbook.sector_rotation")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SECTOR_ETFS: dict[str, str] = {
    "XLB": "Materials",
    "XLC": "Communication",
    "XLE": "Energy",
    "XLF": "Financials",
    "XLI": "Industrials",
    "XLK": "Technology",
    "XLP": "Consumer Staples",
    "XLRE": "Real Estate",
    "XLU": "Utilities",
    "XLV": "Healthcare",
    "XLY": "Consumer Discretionary",
}

OFFENSIVE_SECTORS: frozenset[str] = frozenset({"XLK", "XLY", "XLC", "XLF", "XLI"})
DEFENSIVE_SECTORS: frozenset[str] = frozenset({"XLP", "XLU", "XLV", "XLRE", "XLB"})
# XLE is cyclical/commodity — not classified as offensive or defensive

SECTOR_ROTATION_INTEL_KEY = "intel:sector_rotation"
SECTOR_ROTATION_TTL = 3600   # 1 hour; refresh every 30 min so TTL > refresh interval
LOOKBACK_DAYS = 21           # ~1 trading month; also tested at 5d and 10d

SOURCE_SYSTEM = "sector_rotation"

# ---------------------------------------------------------------------------
# Data retrieval
# ---------------------------------------------------------------------------


def _fetch_closes(conn, symbols: list[str], lookback_days: int) -> pd.DataFrame:
    """Pull daily close prices from raw_market_ticks for the given symbols.

    Returns a DataFrame indexed by date with one column per symbol.
    Missing symbols produce all-NaN columns (not a crash).
    """
    placeholders = ",".join(["%s"] * len(symbols))
    sql = f"""
        SELECT
            symbol,
            DATE(created_at AT TIME ZONE 'UTC') AS trade_date,
            AVG(price) AS close_price
        FROM raw_market_ticks
        WHERE symbol IN ({placeholders})
          AND created_at >= NOW() - INTERVAL '{lookback_days + 5} days'
        GROUP BY symbol, trade_date
        ORDER BY trade_date ASC
    """
    try:
        cur = conn.cursor()
        cur.execute(sql, symbols)
        rows = cur.fetchall()
        cur.close()
    except Exception as exc:
        logger.warning("[SectorRotation] DB query failed: %s", exc)
        return pd.DataFrame()

    if not rows:
        logger.warning("[SectorRotation] No rows returned from raw_market_ticks for sector ETFs")
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=["symbol", "trade_date", "close"])
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    pivot = df.pivot(index="trade_date", columns="symbol", values="close")
    pivot = pivot.sort_index()

    # Keep only the most recent lookback_days rows (after grouping by day)
    if len(pivot) > lookback_days:
        pivot = pivot.iloc[-lookback_days:]

    return pivot


# ---------------------------------------------------------------------------
# RS calculations
# ---------------------------------------------------------------------------


def compute_rs_ratio(prices: pd.DataFrame, sector: str, lookback_days: int) -> Optional[float]:
    """Return RS Ratio for *sector* vs SPY, normalized to 100 at window start.

    RS Ratio > 100 means sector outperformed SPY over the window.
    Returns None if not enough data.
    """
    if sector not in prices.columns or "SPY" not in prices.columns:
        return None

    sector_series = prices[sector].dropna()
    spy_series = prices["SPY"].dropna()

    # Align on common dates
    combined = pd.concat([sector_series, spy_series], axis=1, join="inner")
    combined.columns = ["sector", "spy"]

    if len(combined) < 2:
        return None

    # Relative series: sector / SPY each day, normalized to 100 at start
    rel = combined["sector"] / combined["spy"]
    rs_ratio = (rel.iloc[-1] / rel.iloc[0]) * 100.0
    return float(rs_ratio)


def compute_rs_momentum(prices: pd.DataFrame, sector: str, momentum_window: int = 5) -> Optional[float]:
    """Return RS Momentum = rate of change of RS Ratio.

    Measures whether relative strength is accelerating (+) or decelerating (-).
    Returns None if not enough data.
    """
    if sector not in prices.columns or "SPY" not in prices.columns:
        return None

    sector_series = prices[sector].dropna()
    spy_series = prices["SPY"].dropna()

    combined = pd.concat([sector_series, spy_series], axis=1, join="inner")
    combined.columns = ["sector", "spy"]

    # Need at least momentum_window + 1 rows
    if len(combined) < momentum_window + 1:
        return None

    rel = combined["sector"] / combined["spy"]
    # RS Momentum = today's RS ratio vs N-days-ago RS ratio, expressed as change
    rs_now = (rel.iloc[-1] / rel.iloc[0]) * 100.0
    rs_prev = (rel.iloc[-(momentum_window + 1)] / rel.iloc[0]) * 100.0
    momentum = rs_now - rs_prev
    return float(momentum)


def classify_quadrant(rs_ratio: float, rs_momentum: float) -> str:
    """Return RRG-style quadrant label."""
    if rs_ratio >= 100.0 and rs_momentum >= 0.0:
        return "LEADING"
    elif rs_ratio >= 100.0 and rs_momentum < 0.0:
        return "WEAKENING"
    elif rs_ratio < 100.0 and rs_momentum < 0.0:
        return "LAGGING"
    else:
        return "IMPROVING"


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------


def rank_sectors(rs_ratios: dict[str, float]) -> dict[str, int]:
    """Return ordinal ranks 1..N by RS Ratio (1 = strongest).

    Ties: sectors with equal RS ratio share the same rank (dense ranking).
    """
    if not rs_ratios:
        return {}
    sorted_symbols = sorted(rs_ratios.keys(), key=lambda sym: rs_ratios[sym], reverse=True)
    ranks: dict[str, int] = {}
    current_rank = 1
    prev_rs: Optional[float] = None
    for idx, sym in enumerate(sorted_symbols):
        if prev_rs is not None and rs_ratios[sym] < prev_rs:
            current_rank = idx + 1
        ranks[sym] = current_rank
        prev_rs = rs_ratios[sym]
    return ranks


# ---------------------------------------------------------------------------
# Offensive/Defensive scoring
# ---------------------------------------------------------------------------


def compute_rotation_bias(
    snapshots: dict[str, SectorSnapshot],
) -> tuple[int, int, str]:
    """Return (offensive_score, defensive_score, bias).

    Offensive score: count of OFFENSIVE sectors in LEADING or IMPROVING.
    Defensive score: count of DEFENSIVE sectors in LEADING or IMPROVING.
    bias: RISK_ON / RISK_OFF / NEUTRAL
    """
    offensive_score = 0
    defensive_score = 0
    active_quadrants = {"LEADING", "IMPROVING"}

    for sym, snap in snapshots.items():
        if snap.quadrant in active_quadrants:
            if sym in OFFENSIVE_SECTORS:
                offensive_score += 1
            elif sym in DEFENSIVE_SECTORS:
                defensive_score += 1

    if offensive_score > defensive_score:
        bias = "RISK_ON"
    elif defensive_score > offensive_score:
        bias = "RISK_OFF"
    else:
        bias = "NEUTRAL"

    return offensive_score, defensive_score, bias


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------


def run_sector_rotation(conn, lookback_days: int = LOOKBACK_DAYS) -> Optional[SectorRotationIntel]:
    """Compute sector rotation intel and publish to Redis.

    Args:
        conn: Active psycopg2 connection. Caller owns the connection lifecycle.
        lookback_days: RS lookback window (default 21 trading days).

    Returns:
        SectorRotationIntel instance, or None on failure.
    """
    start = time.time()
    logger.info("[SectorRotation] Starting sector rotation scan (lookback=%d days)", lookback_days)

    all_symbols = ["SPY"] + list(SECTOR_ETFS.keys())
    prices = _fetch_closes(conn, all_symbols, lookback_days)

    if prices.empty or "SPY" not in prices.columns:
        logger.warning("[SectorRotation] No SPY data available — skipping rotation scan")
        return None

    # Compute RS metrics per sector
    snapshots: dict[str, SectorSnapshot] = {}
    rs_ratios: dict[str, float] = {}
    missing: list[str] = []

    for sym, name in SECTOR_ETFS.items():
        rs_ratio = compute_rs_ratio(prices, sym, lookback_days)
        rs_momentum = compute_rs_momentum(prices, sym)

        if rs_ratio is None or rs_momentum is None:
            logger.warning("[SectorRotation] Insufficient data for %s — excluded from ranking", sym)
            missing.append(sym)
            continue

        rs_ratios[sym] = rs_ratio
        snapshots[sym] = SectorSnapshot(
            symbol=sym,
            name=name,
            rs_ratio=rs_ratio,
            rs_momentum=rs_momentum,
            rank=0,  # filled after ranking
            quadrant=classify_quadrant(rs_ratio, rs_momentum),
        )

    if missing:
        logger.info("[SectorRotation] Missing ETFs (no ticks yet): %s", missing)

    if not snapshots:
        logger.warning("[SectorRotation] No sectors with sufficient data — aborting")
        return None

    # Assign ranks
    ranks = rank_sectors(rs_ratios)
    for sym, snap in snapshots.items():
        snapshots[sym] = snap.model_copy(update={"rank": ranks.get(sym, 0)})

    # Top/bottom 3
    sorted_by_rank = sorted(snapshots.keys(), key=lambda sym: rs_ratios[sym], reverse=True)
    top_3 = sorted_by_rank[:3]
    bottom_3 = sorted_by_rank[-3:] if len(sorted_by_rank) >= 3 else sorted_by_rank

    # Offensive/defensive bias
    offensive_score, defensive_score, rotation_bias = compute_rotation_bias(snapshots)

    intel = SectorRotationIntel(
        timestamp=datetime.now(timezone.utc),
        lookback_days=lookback_days,
        sectors=snapshots,
        top_3=top_3,
        bottom_3=bottom_3,
        rotation_bias=rotation_bias,
        offensive_score=offensive_score,
        defensive_score=defensive_score,
    )

    # Publish to Intel Bus
    intel_value = {
        "lookback_days": intel.lookback_days,
        "rotation_bias": intel.rotation_bias,
        "offensive_score": intel.offensive_score,
        "defensive_score": intel.defensive_score,
        "top_3": intel.top_3,
        "bottom_3": intel.bottom_3,
        "sectors": {
            sym: {
                "name": snap.name,
                "rs_ratio": snap.rs_ratio,
                "rs_momentum": snap.rs_momentum,
                "rank": snap.rank,
                "quadrant": snap.quadrant,
            }
            for sym, snap in intel.sectors.items()
        },
        "timestamp": intel.timestamp.isoformat(),
    }

    IntelPublisher.publish(
        key=SECTOR_ROTATION_INTEL_KEY,
        value=intel_value,
        source_system=SOURCE_SYSTEM,
        confidence=1.0,
        ttl=SECTOR_ROTATION_TTL,
    )

    elapsed = time.time() - start
    logger.info(
        "[SectorRotation] Done in %.1fs | bias=%s | off=%d def=%d | top=%s | missing=%d",
        elapsed,
        rotation_bias,
        offensive_score,
        defensive_score,
        top_3,
        len(missing),
    )

    return intel
