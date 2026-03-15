"""
Cemini Financial Suite — Playbook Replay Helpers (Step 37)

Pure data-processing functions for the Playbook Replay Viewer.
No Streamlit imports — fully unit-testable.

These helpers translate raw playbook_logs rows into structured, display-ready dicts.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REGIME_COLORS: dict[str, str] = {
    "GREEN": "#27ae60",
    "YELLOW": "#f39c12",
    "RED": "#c0392b",
    "UNKNOWN": "#7f8c8d",
}

REGIME_EMOJI: dict[str, str] = {
    "GREEN": "🟢",
    "YELLOW": "🟡",
    "RED": "🔴",
    "UNKNOWN": "⚫",
}

SIGNAL_DETECTORS = [
    "EpisodicPivot",
    "MomentumBurst",
    "ElephantBar",
    "VCP",
    "HighTightFlag",
    "InsideBar212",
]


# ---------------------------------------------------------------------------
# Payload parsing
# ---------------------------------------------------------------------------


def parse_payload(raw: Any) -> dict:
    """Parse a JSONB payload (dict, JSON string, or bytes) into a plain dict.

    Returns an empty dict on any parse failure — never raises.
    """
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, (str, bytes)):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}


# ---------------------------------------------------------------------------
# Regime helpers
# ---------------------------------------------------------------------------


def get_regime_color(regime: Optional[str]) -> str:
    """Return hex color for regime label. Defaults to UNKNOWN gray."""
    if regime is None:
        return REGIME_COLORS["UNKNOWN"]
    return REGIME_COLORS.get(str(regime).upper(), REGIME_COLORS["UNKNOWN"])


def get_regime_emoji(regime: Optional[str]) -> str:
    """Return emoji for regime label."""
    if regime is None:
        return REGIME_EMOJI["UNKNOWN"]
    return REGIME_EMOJI.get(str(regime).upper(), REGIME_EMOJI["UNKNOWN"])


def extract_regime_detail(payload: dict) -> dict:
    """Extract structured regime metrics from a regime-type log payload.

    Returns a dict with: regime, spy_price, ema21, sma50, confidence, reason, jnk_tlt_flag.
    Missing keys default to sensible zero/unknown values.
    """
    return {
        "regime": payload.get("regime", "UNKNOWN"),
        "spy_price": float(payload.get("spy_price", 0.0)),
        "ema21": float(payload.get("ema21", 0.0)),
        "sma50": float(payload.get("sma50", 0.0)),
        "confidence": float(payload.get("confidence", 0.0)),
        "reason": str(payload.get("reason", "")),
        "jnk_tlt_flag": bool(payload.get("jnk_tlt_flag", False)),
    }


# ---------------------------------------------------------------------------
# Signal helpers
# ---------------------------------------------------------------------------


def extract_signal_summary(payload: dict) -> list[dict]:
    """Extract a list of signal dicts from a signal-type log payload.

    Signal rows have: pattern_name, symbol, confidence, entry_price, stop_price.
    Returns a list (usually length 1 per DB row, but handles list payloads too).
    """
    if "pattern_name" in payload:
        return [{
            "pattern_name": payload.get("pattern_name", ""),
            "symbol": payload.get("symbol", ""),
            "confidence": float(payload.get("confidence", 0.0)),
            "entry_price": float(payload.get("entry_price", 0.0)),
            "stop_price": float(payload.get("stop_price", 0.0)),
        }]
    if isinstance(payload.get("signals"), list):
        return payload["signals"]
    return []


def build_detector_grid(signal_rows: list[dict]) -> dict[str, list[str]]:
    """Build a detector_name → [symbols_triggered] mapping from a list of signal rows.

    Used to show which detectors fired in a cycle and which symbols triggered them.
    Detectors not present in signal_rows appear in the grid with an empty list.
    """
    grid: dict[str, list[str]] = {d: [] for d in SIGNAL_DETECTORS}
    for row in signal_rows:
        payload = row if "pattern_name" in row else parse_payload(row.get("payload", {}))
        name = payload.get("pattern_name", "")
        sym = payload.get("symbol", "")
        if name in grid and sym:
            grid[name].append(sym)
    return grid


# ---------------------------------------------------------------------------
# Risk helpers
# ---------------------------------------------------------------------------


def extract_risk_metrics(payload: dict) -> dict:
    """Extract risk metrics from a risk-type log payload.

    Returns: cvar_99, kelly_size, nav, drawdown_snapshot (or empty dict).
    """
    return {
        "cvar_99": float(payload.get("cvar_99", 0.0)),
        "kelly_size": float(payload.get("kelly_size", 0.0)),
        "nav": float(payload.get("nav", 0.0)),
        "drawdown_snapshot": payload.get("drawdown_snapshot", {}),
    }


# ---------------------------------------------------------------------------
# Sector rotation helpers
# ---------------------------------------------------------------------------


def extract_sector_rotation(intel_value: Any) -> Optional[dict]:
    """Extract sector rotation summary from an intel:sector_rotation payload.

    Returns structured dict or None if sector data is not present/parseable.
    This is read from the Intel Bus payload value dict, not from playbook_logs.
    """
    payload = parse_payload(intel_value) if not isinstance(intel_value, dict) else intel_value
    if not payload:
        return None
    # Must have rotation_bias to be valid sector rotation data
    if "rotation_bias" not in payload:
        return None
    return {
        "rotation_bias": payload.get("rotation_bias", "NEUTRAL"),
        "offensive_score": int(payload.get("offensive_score", 0)),
        "defensive_score": int(payload.get("defensive_score", 0)),
        "top_3": list(payload.get("top_3", [])),
        "bottom_3": list(payload.get("bottom_3", [])),
    }


# ---------------------------------------------------------------------------
# Timestamp formatting
# ---------------------------------------------------------------------------


def format_snapshot_label(ts: Any, regime: Optional[str] = None) -> str:
    """Build a human-readable timeline label: HH:MM | REGIME.

    ts can be a datetime, ISO string, or float epoch.
    """
    time_str = _format_ts(ts)
    if regime:
        emoji = get_regime_emoji(regime)
        return f"{time_str} {emoji} {regime}"
    return time_str


def _format_ts(ts: Any) -> str:
    """Format timestamp as HH:MM:SS. Accepts datetime, string, or epoch float."""
    if isinstance(ts, datetime):
        return ts.strftime("%H:%M:%S")
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.strftime("%H:%M:%S")
        except ValueError:
            return ts
    if isinstance(ts, (int, float)):
        try:
            dt = datetime.fromtimestamp(float(ts), tz=timezone.utc)
            return dt.strftime("%H:%M:%S")
        except (OSError, OverflowError, ValueError):
            return str(ts)
    return str(ts)


def format_full_datetime(ts: Any) -> str:
    """Format timestamp as full datetime string for detail display."""
    if isinstance(ts, datetime):
        return ts.strftime("%Y-%m-%d %H:%M:%S UTC")
    return str(ts)


# ---------------------------------------------------------------------------
# SQL helpers (return SQL strings — DB connection is caller's responsibility)
# ---------------------------------------------------------------------------


def available_dates_sql() -> str:
    """SQL to fetch distinct dates with playbook data (newest first, up to 90 days)."""
    return (
        "SELECT DISTINCT timestamp::date AS log_date "
        "FROM playbook_logs "
        "ORDER BY log_date DESC "
        "LIMIT 90"
    )


def regime_snapshots_for_date_sql() -> str:
    """SQL to fetch all regime snapshots for a given date (ascending time)."""
    return (
        "SELECT id, timestamp, log_type, regime, payload "
        "FROM playbook_logs "
        "WHERE log_type = 'regime' AND timestamp::date = %s "
        "ORDER BY timestamp ASC"
    )


def signals_in_window_sql() -> str:
    """SQL to fetch signal logs within ±3 min of a given timestamp."""
    return (
        "SELECT id, timestamp, log_type, regime, payload "
        "FROM playbook_logs "
        "WHERE log_type = 'signal' "
        "  AND timestamp >= %s - interval '3 minutes' "
        "  AND timestamp <= %s + interval '3 minutes' "
        "ORDER BY timestamp ASC"
    )


def risk_in_window_sql() -> str:
    """SQL to fetch risk snapshot within ±3 min of a given timestamp."""
    return (
        "SELECT payload "
        "FROM playbook_logs "
        "WHERE log_type = 'risk' "
        "  AND timestamp >= %s - interval '3 minutes' "
        "  AND timestamp <= %s + interval '3 minutes' "
        "ORDER BY timestamp DESC "
        "LIMIT 1"
    )
