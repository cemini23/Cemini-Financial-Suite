"""
Cemini Financial Suite — Volatility Surface Monitor (Step 23)

Runs every 6th playbook cycle (~30 min cadence), queries raw_market_ticks,
computes realized vol / Parkinson vol / beta for each tracked equity, and
publishes a vol surface snapshot to intel:vol_surface (TTL=3600).

Architecture
------------
- Pure math in realized_vol.py (fully testable without DB)
- This module handles only DB I/O + Intel Bus publish
- Called non-blocking from runner.py (same pattern as sector_rotation)

Published key: intel:vol_surface (TTL=3600 seconds, ~1 hour)
"""
from __future__ import annotations

import logging
import math
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("options_greeks.vol_monitor")

# Minimum trading days required for a reliable vol estimate
_MIN_BARS = 21
# Lookback for beta and regime calculation
_BETA_LOOKBACK = 63
_REGIME_LOOKBACK = 63

# Symbols for which we compute vol (equities only, not sector ETFs for beta)
EQUITY_SYMBOLS = [
    "SPY", "QQQ", "IWM",
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA",
    "AMD", "SMCI", "PLTR", "AVGO",
    "COIN", "MSTR", "MARA",
    "JPM", "BAC", "GS",
    # Sector ETFs (no beta vs themselves, but include for vol)
    "XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY",
]


def _fetch_ohlcv(conn, symbol: str, lookback: int) -> dict[str, list]:
    """Fetch OHLCV from raw_market_ticks for the given symbol."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT timestamp, open, high, low, close
        FROM raw_market_ticks
        WHERE symbol = %s
          AND timestamp >= NOW() - INTERVAL '%s days'
        ORDER BY timestamp ASC
        """,
        (symbol, lookback + 10),  # +10 buffer for weekends/holidays
    )
    rows = cursor.fetchall()
    closes = [float(r[4]) for r in rows if r[4] is not None]
    highs = [float(r[2]) for r in rows if r[2] is not None]
    lows = [float(r[3]) for r in rows if r[3] is not None]
    return {"closes": closes, "highs": highs, "lows": lows}


def run_vol_monitor(conn, today: Optional[datetime] = None) -> Optional[dict]:
    """Compute volatility surface for all tracked equity symbols.

    Args:
        conn: Active psycopg2 connection (autocommit mode).
        today: Override for testing; defaults to UTC now.

    Returns:
        The published vol_surface dict, or None on failure.
    """
    from options_greeks.realized_vol import (
        realized_vol,
        parkinson_vol,
        rolling_beta,
        vol_regime,
        approx_iv,
    )
    from core.intel_bus import IntelPublisher, IntelReader

    if today is None:
        today = datetime.now(timezone.utc)

    # Read VIX from Intel Bus (published hourly by analyzer.py)
    vix_val: Optional[float] = None
    try:
        raw = IntelReader.read("intel:vix_level")
        if raw:
            vix_val = float(raw.get("value", 0.0)) or None
    except Exception:
        pass

    # Fetch SPY data for beta calculation
    try:
        spy_data = _fetch_ohlcv(conn, "SPY", _BETA_LOOKBACK)
        spy_closes = spy_data["closes"][-_BETA_LOOKBACK:]
    except Exception as exc:
        logger.warning("[VolMonitor] Failed to fetch SPY data: %s", exc)
        spy_closes = []

    symbols_out: dict[str, dict] = {}
    high_vol: list[str] = []
    low_vol: list[str] = []
    all_regimes: list[str] = []

    for symbol in EQUITY_SYMBOLS:
        try:
            data = _fetch_ohlcv(conn, symbol, _REGIME_LOOKBACK + _MIN_BARS)
            closes = data["closes"]
            highs = data["highs"]
            lows = data["lows"]

            if len(closes) < _MIN_BARS:
                logger.debug("[VolMonitor] %s: only %d bars — skipping", symbol, len(closes))
                continue

            # 21-day close-to-close vol
            rv_21 = realized_vol(closes[-21:])

            # 21-day Parkinson vol (if H/L available)
            pv_21: Optional[float] = None
            if len(highs) >= 21 and len(lows) >= 21:
                pv = parkinson_vol(highs[-21:], lows[-21:])
                pv_21 = pv if not math.isnan(pv) else None

            # Vol regime: compare current 21d vol to rolling 63d window of 21d vols
            regime_vols: list[float] = []
            if len(closes) >= _REGIME_LOOKBACK:
                # Compute 21-day rolling vols across the 63-bar lookback
                for i in range(_REGIME_LOOKBACK - _MIN_BARS + 1):
                    start = i
                    end = i + _MIN_BARS
                    if end <= len(closes):
                        rv = realized_vol(closes[start:end])
                        if not math.isnan(rv):
                            regime_vols.append(rv)

            regime = vol_regime(rv_21 if not math.isnan(rv_21) else 0.0, regime_vols)

            # Beta vs SPY
            beta: Optional[float] = None
            if symbol != "SPY" and len(spy_closes) >= 5:
                stock_slice = closes[-len(spy_closes):]
                spy_slice = spy_closes[-len(stock_slice):]
                b = rolling_beta(stock_slice, spy_slice)
                beta = b if not math.isnan(b) else None

            # Approximate IV from VIX
            iv_approx: Optional[float] = None
            if vix_val is not None and beta is not None:
                iv = approx_iv(vix_val, beta)
                iv_approx = iv if not math.isnan(iv) else None

            symbols_out[symbol] = {
                "symbol": symbol,
                "realized_vol_21d": round(rv_21, 6) if not math.isnan(rv_21) else None,
                "parkinson_vol_21d": round(pv_21, 6) if pv_21 is not None else None,
                "vol_regime": regime,
                "approx_iv": round(iv_approx, 6) if iv_approx is not None else None,
                "beta_to_spy": round(beta, 4) if beta is not None else None,
            }

            all_regimes.append(regime)
            if regime == "HIGH":
                high_vol.append(symbol)
            elif regime == "LOW":
                low_vol.append(symbol)

        except Exception as exc:
            logger.debug("[VolMonitor] %s: computation error: %s", symbol, exc)
            continue

    if not symbols_out:
        logger.warning("[VolMonitor] No symbols computed — skipping publish")
        return None

    # Market-level regime: majority vote
    high_n = all_regimes.count("HIGH")
    low_n = all_regimes.count("LOW")
    n = len(all_regimes)
    if high_n > n / 2:
        market_regime = "HIGH"
    elif low_n > n / 2:
        market_regime = "LOW"
    else:
        market_regime = "NORMAL"

    payload: dict = {
        "timestamp": today.isoformat(),
        "vix": vix_val,
        "symbols": symbols_out,
        "market_vol_regime": market_regime,
        "high_vol_symbols": high_vol,
        "low_vol_symbols": low_vol,
        "total_tracked": len(symbols_out),
    }

    IntelPublisher.publish(
        key="intel:vol_surface",
        value=payload,
        source_system="vol_monitor",
        confidence=0.9,
        ttl=3600,
    )
    logger.info(
        "[VolMonitor] Published vol_surface: %d symbols | market=%s | vix=%s",
        len(symbols_out),
        market_regime,
        vix_val,
    )
    return payload
