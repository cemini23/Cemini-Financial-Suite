"""
Cemini Financial Suite — Playbook Replay Viewer (Step 37)

Streamlit tab: time-travel through historical playbook snapshots.

Features:
  - Date picker → available dates with playbook data
  - Snapshot timeline (selectbox) — one entry per 5-min cycle
  - Regime banner (color-coded GREEN/YELLOW/RED)
  - Signal detector grid (which of 6 detectors fired, on which symbols)
  - Risk metrics (CVaR, Kelly, drawdown)
  - Sector rotation panel (graceful fallback for pre-Step 25 snapshots)
  - Raw JSON expander for debugging
  - Auto-play mode (session_state cycle through timeline)

Data source: PostgreSQL playbook_logs table (read-only).
No /mnt/archive/playbook/ volume needed — Postgres is available.
"""

from __future__ import annotations

import json
import os
import time
from datetime import date, datetime, timezone
from typing import Optional

import pandas as pd
import psycopg2
import streamlit as st

from replay_helpers import (
    REGIME_COLORS,
    SIGNAL_DETECTORS,
    available_dates_sql,
    build_detector_grid,
    extract_regime_detail,
    extract_risk_metrics,
    extract_sector_rotation,
    extract_signal_summary,
    format_full_datetime,
    format_snapshot_label,
    get_regime_color,
    parse_payload,
    regime_snapshots_for_date_sql,
    risk_in_window_sql,
    signals_in_window_sql,
)

_DB_PARAMS = dict(
    host=os.getenv("DB_HOST", "postgres"),
    database="qdb",
    user="admin",
    password=os.getenv("POSTGRES_PASSWORD", "quest"),
)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


def _query(sql: str, params=None) -> pd.DataFrame:
    try:
        conn = psycopg2.connect(**_DB_PARAMS)
        cur = conn.cursor()
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        conn.close()
        return pd.DataFrame(rows, columns=cols)
    except Exception:
        return pd.DataFrame()


def _fetch_single(sql: str, params=None) -> Optional[dict]:
    """Fetch one row as dict, or None if no rows."""
    df = _query(sql, params)
    if df.empty:
        return None
    return df.iloc[0].to_dict()


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------


def load_available_dates() -> list[date]:
    df = _query(available_dates_sql())
    if df.empty or "log_date" not in df.columns:
        return []
    return [d for d in df["log_date"].tolist() if d is not None]


def load_regime_snapshots(selected_date: date) -> pd.DataFrame:
    return _query(regime_snapshots_for_date_sql(), (selected_date,))


def load_signals_for_cycle(cycle_ts: datetime) -> pd.DataFrame:
    return _query(signals_in_window_sql(), (cycle_ts, cycle_ts))


def load_risk_for_cycle(cycle_ts: datetime) -> Optional[dict]:
    row = _fetch_single(risk_in_window_sql(), (cycle_ts, cycle_ts))
    if row is None:
        return None
    raw_payload = row.get("payload", {})
    return parse_payload(raw_payload)


# ---------------------------------------------------------------------------
# Sub-panels
# ---------------------------------------------------------------------------


def _render_regime_banner(regime_detail: dict, cycle_ts: Any) -> None:
    regime = regime_detail.get("regime", "UNKNOWN")
    color = get_regime_color(regime)
    st.markdown(
        f"""
        <div style="
            background-color: {color}22;
            border-left: 6px solid {color};
            padding: 12px 20px;
            border-radius: 6px;
            margin-bottom: 12px;
        ">
            <h2 style="margin:0; color:{color};">{regime} REGIME</h2>
            <span style="color:#666; font-size:0.9em;">{format_full_datetime(cycle_ts)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    cols[0].metric("SPY Price", f"${regime_detail['spy_price']:.2f}" if regime_detail["spy_price"] else "—")
    cols[1].metric("EMA 21", f"{regime_detail['ema21']:.2f}" if regime_detail["ema21"] else "—")
    cols[2].metric("SMA 50", f"{regime_detail['sma50']:.2f}" if regime_detail["sma50"] else "—")
    cols[3].metric("Confidence", f"{regime_detail['confidence']:.0%}")
    if regime_detail.get("reason"):
        st.caption(f"💬 {regime_detail['reason']}")
    if regime_detail.get("jnk_tlt_flag"):
        st.warning("⚠️ JNK/TLT flag: credit markets NOT confirming equity breakout")


def _render_signal_grid(signals_df: pd.DataFrame) -> None:
    st.subheader("🎯 Signal Detectors")

    signal_rows: list[dict] = []
    for _, row in signals_df.iterrows():
        payload = parse_payload(row.get("payload", {}))
        signal_rows.extend(extract_signal_summary(payload))

    grid = build_detector_grid(signal_rows)

    cols = st.columns(3)
    for idx, detector in enumerate(SIGNAL_DETECTORS):
        col = cols[idx % 3]
        triggered_syms = grid.get(detector, [])
        fired = bool(triggered_syms)
        with col:
            status = "✅ FIRED" if fired else "❌ —"
            color = "#27ae60" if fired else "#bdc3c7"
            syms_str = ", ".join(triggered_syms) if fired else "—"
            st.markdown(
                f"""
                <div style="border:1px solid {color}; border-radius:6px;
                            padding:10px; margin-bottom:8px; min-height:70px;">
                    <b style="color:{color};">{status}</b>
                    <div style="font-size:0.9em; font-weight:600;">{detector}</div>
                    <div style="font-size:0.8em; color:#666;">{syms_str}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if signal_rows:
        with st.expander(f"Signal details ({len(signal_rows)} events)", expanded=False):
            for sig in signal_rows:
                st.markdown(
                    f"**{sig.get('pattern_name', '?')}** on **{sig.get('symbol', '?')}** "
                    f"— conf={sig.get('confidence', 0):.2f} "
                    f"entry={sig.get('entry_price', 0):.4f} "
                    f"stop={sig.get('stop_price', 0):.4f}"
                )


def _render_risk_metrics(risk_payload: Optional[dict]) -> None:
    st.subheader("⚖️ Risk Metrics")
    if risk_payload is None:
        st.info("No risk snapshot found within ±3 minutes of this cycle.")
        return
    metrics = extract_risk_metrics(risk_payload)
    cols = st.columns(3)
    cols[0].metric("CVaR 99%", f"{metrics['cvar_99']:.4f}")
    cols[1].metric("Kelly Size", f"{metrics['kelly_size']:.4f}")
    cols[2].metric("NAV", f"${metrics['nav']:.2f}" if metrics["nav"] else "—")
    dd = metrics.get("drawdown_snapshot", {})
    if dd:
        with st.expander("Drawdown snapshot"):
            st.json(dd)


def _render_sector_rotation_panel(intel_value: Any) -> None:
    st.subheader("🔄 Sector Rotation")
    rotation = extract_sector_rotation(intel_value)
    if rotation is None:
        st.info("Sector rotation data not available for this snapshot "
                "(Step 25 started logging on Mar 15 — older snapshots will show this message).")
        return

    bias = rotation["rotation_bias"]
    bias_color = {"RISK_ON": "#27ae60", "RISK_OFF": "#c0392b", "NEUTRAL": "#f39c12"}.get(bias, "#7f8c8d")
    st.markdown(
        f"**Rotation Bias:** "
        f"<span style='color:{bias_color}; font-weight:700;'>{bias}</span> &nbsp;"
        f"(Off: {rotation['offensive_score']} / Def: {rotation['defensive_score']})",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Top 3 sectors:**")
        for sym in rotation.get("top_3", []):
            st.markdown(f"• {sym}")
    with c2:
        st.markdown("**Bottom 3 sectors:**")
        for sym in rotation.get("bottom_3", []):
            st.markdown(f"• {sym}")


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

from typing import Any  # noqa: E402 (already imported above, kept for clarity)


def render() -> None:
    """Entry point called from app.py."""
    st.title("⏮️ Playbook Replay Viewer")
    st.caption(
        "Time-travel through historical playbook snapshots. "
        "Read-only — no trades are placed. "
        "Data source: PostgreSQL `playbook_logs` table."
    )

    # ── Available dates ──────────────────────────────────────────────────────
    available_dates = load_available_dates()
    if not available_dates:
        st.warning(
            "No playbook snapshots found in the database. "
            "The playbook_runner logs data every 5 minutes — "
            "check that the container is healthy and has been running."
        )
        return

    # ── Date picker ──────────────────────────────────────────────────────────
    ctrl_l, ctrl_r = st.columns([2, 1])
    with ctrl_l:
        selected_date = st.date_input(
            "Select date",
            value=available_dates[0],
            min_value=available_dates[-1],
            max_value=available_dates[0],
        )
    with ctrl_r:
        autoplay = st.toggle("▶ Auto-play", value=False, help="Cycle through snapshots at 1s intervals")

    # ── Load regime snapshots for selected date ──────────────────────────────
    snapshots_df = load_regime_snapshots(selected_date)

    if snapshots_df.empty:
        st.info(f"No regime snapshots found for {selected_date}.")
        return

    total = len(snapshots_df)
    st.caption(f"{total} regime snapshots on {selected_date}")

    # Build timeline labels
    labels = []
    for _, row in snapshots_df.iterrows():
        labels.append(format_snapshot_label(row["timestamp"], row.get("regime")))

    # ── Session state for auto-play ──────────────────────────────────────────
    if "replay_idx" not in st.session_state:
        st.session_state.replay_idx = 0

    # ── Snapshot selector ────────────────────────────────────────────────────
    selected_idx = st.select_slider(
        "Snapshot timeline",
        options=list(range(total)),
        value=st.session_state.replay_idx,
        format_func=lambda i: labels[i],
    )
    st.session_state.replay_idx = selected_idx

    # ── Snapshot detail ──────────────────────────────────────────────────────
    row = snapshots_df.iloc[selected_idx]
    cycle_ts = row["timestamp"]
    raw_payload = row.get("payload", {})
    regime_payload = parse_payload(raw_payload)
    regime_detail = extract_regime_detail(regime_payload)

    st.markdown("---")
    _render_regime_banner(regime_detail, cycle_ts)

    st.markdown("---")
    signals_df = load_signals_for_cycle(cycle_ts)
    _render_signal_grid(signals_df)

    st.markdown("---")
    risk_payload = load_risk_for_cycle(cycle_ts)
    _render_risk_metrics(risk_payload)

    # Sector rotation: check if payload has rotation_bias (Step 25 adds it to intel, not playbook_logs)
    # Try reading from Intel Bus payload embedded in regime_payload metadata, else show graceful fallback
    st.markdown("---")
    sector_intel = regime_payload.get("sector_rotation")  # may not exist in older snapshots
    _render_sector_rotation_panel(sector_intel)

    st.markdown("---")
    with st.expander("🔬 Raw JSON payload", expanded=False):
        st.json(regime_payload)

    # ── Auto-play ────────────────────────────────────────────────────────────
    if autoplay and selected_idx < total - 1:
        time.sleep(1.0)
        st.session_state.replay_idx = selected_idx + 1
        st.rerun()
