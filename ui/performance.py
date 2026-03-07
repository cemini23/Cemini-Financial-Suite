"""Step 3: Paper Trade Performance Dashboard.

READ-ONLY — all queries are SELECT-only.
All P&L figures are hypothetical simulation results, clearly labeled as such.
No trading behavior is modified by this module.
"""

import os
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
import streamlit as st

REGIME_COLORS = {
    "GREEN": "#27ae60",
    "YELLOW": "#f39c12",
    "RED": "#c0392b",
    "UNKNOWN": "#7f8c8d",
}
REGIME_BG_OPACITY = 0.12

_DB_PARAMS = dict(
    host=os.getenv("DB_HOST", "postgres"),
    database="qdb",
    user="admin",
    password=os.getenv("POSTGRES_PASSWORD", "quest"),
)


# ── DB helpers ────────────────────────────────────────────────────────────────

def _query(sql: str, params=None) -> pd.DataFrame:
    try:
        conn = psycopg2.connect(**_DB_PARAMS)
        cur = conn.cursor()
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return pd.DataFrame(rows, columns=cols)
    except Exception as exc:
        st.warning(f"DB query error: {exc}")
        return pd.DataFrame()


# ── Redis helper ──────────────────────────────────────────────────────────────

def _get_redis():
    try:
        import redis  # optional dep
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=6379,
            password=os.getenv("REDIS_PASSWORD", "cemini_redis_2026"),
            decode_responses=True,
            socket_connect_timeout=2,
        )
        r.ping()
        return r
    except Exception:
        return None


# ── Cached data loaders ───────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_regime(start, end):
    return _query(
        """
        SELECT timestamp,
               regime,
               (payload->>'spy_price')::float   AS spy_price,
               (payload->>'ema21')::float        AS ema21,
               (payload->>'sma50')::float        AS sma50,
               (payload->>'confidence')::float   AS confidence,
               payload->>'reason'                AS reason
        FROM playbook_logs
        WHERE log_type = 'regime'
          AND timestamp BETWEEN %s AND %s
        ORDER BY timestamp
        """,
        (start, end),
    )


@st.cache_data(ttl=300)
def load_signals(start, end):
    return _query(
        """
        SELECT timestamp,
               payload->>'symbol'                    AS symbol,
               payload->>'pattern_name'               AS pattern_name,
               (payload->>'entry_price')::float       AS entry_price,
               (payload->>'stop_price')::float        AS stop_price,
               (payload->>'confidence')::float        AS confidence,
               payload->>'regime_at_detection'        AS regime
        FROM playbook_logs
        WHERE log_type = 'signal'
          AND timestamp BETWEEN %s AND %s
        ORDER BY timestamp
        """,
        (start, end),
    )


@st.cache_data(ttl=300)
def load_risk(start, end):
    return _query(
        """
        SELECT timestamp,
               (payload->>'kelly_size')::float                               AS kelly_size,
               (payload->>'cvar_99')::float                                  AS cvar_99,
               (payload->>'nav')::float                                      AS nav,
               (payload->'drawdown_snapshot'->'portfolio'->>'peak_equity')::float AS peak_equity,
               (payload->'drawdown_snapshot'->'portfolio'->>'halted')::boolean    AS halted
        FROM playbook_logs
        WHERE log_type = 'risk'
          AND timestamp BETWEEN %s AND %s
        ORDER BY timestamp
        """,
        (start, end),
    )


@st.cache_data(ttl=300)
def load_ticks(symbols_tuple, start, end):
    if not symbols_tuple:
        return pd.DataFrame()
    placeholders = ",".join(["%s"] * len(symbols_tuple))
    return _query(
        f"""
        SELECT symbol, price, created_at
        FROM raw_market_ticks
        WHERE symbol IN ({placeholders})
          AND created_at BETWEEN %s AND %s
        ORDER BY symbol, created_at
        """,
        list(symbols_tuple) + [start, end],
    )


@st.cache_data(ttl=300)
def load_db_health():
    return _query(
        """
        SELECT
            (SELECT MAX(created_at) FROM raw_market_ticks WHERE symbol='BTC-USD')  AS last_crypto,
            (SELECT MAX(created_at) FROM raw_market_ticks WHERE symbol='SPY')       AS last_equity,
            (SELECT COUNT(*) FROM playbook_logs WHERE timestamp > NOW() - INTERVAL '1 hour') AS playbook_last_hour,
            (SELECT COUNT(*) FROM raw_market_ticks WHERE created_at > NOW() - INTERVAL '1 hour') AS ticks_last_hour,
            (SELECT MAX(timestamp) FROM trade_history) AS last_trade,
            (SELECT COUNT(*) FROM trade_history) AS total_trades,
            (SELECT COUNT(DISTINCT symbol) FROM raw_market_ticks) AS tracked_symbols
        """
    )


# ── P&L simulation ────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def simulate_pnl(signals_df_json, ticks_df_json, tp_pct, position_pct, portfolio_start):
    """Run hypothetical P&L simulation from signal detections.

    Inputs are JSON-serialized DataFrames so st.cache_data can hash them.
    """
    signals_df = pd.read_json(signals_df_json)
    ticks_df = pd.read_json(ticks_df_json)

    if signals_df.empty or ticks_df.empty:
        return "[]", "{}"

    # Ensure timestamps are comparable
    signals_df["timestamp"] = pd.to_datetime(signals_df["timestamp"], utc=True)
    ticks_df["created_at"] = pd.to_datetime(ticks_df["created_at"], utc=True)

    # Pre-group ticks by symbol
    ticks_by_sym = {}
    for sym, grp in ticks_df.groupby("symbol"):
        arr = grp.sort_values("created_at")[["created_at", "price"]].reset_index(drop=True)
        ticks_by_sym[sym] = arr

    trades = []
    portfolio = float(portfolio_start)

    for _, sig in signals_df.iterrows():
        sym = sig["symbol"]
        entry = sig["entry_price"]
        stop = sig["stop_price"]
        conf = sig.get("confidence") or 0.5

        # Validity guards
        if not entry or entry <= 0:
            continue
        if not stop or stop <= 0 or stop >= entry:
            continue

        tp_price = entry * (1.0 + tp_pct)
        position_size = portfolio * position_pct * min(float(conf), 1.0)
        n_shares = position_size / entry if entry > 0 else 0

        sym_ticks = ticks_by_sym.get(sym)
        if sym_ticks is None or sym_ticks.empty:
            continue

        sig_ts = pd.Timestamp(sig["timestamp"]).tz_localize("UTC") if pd.Timestamp(sig["timestamp"]).tzinfo is None else pd.Timestamp(sig["timestamp"])
        future = sym_ticks[sym_ticks["created_at"] > sig_ts].head(300)

        if future.empty:
            continue

        # Walk forward to find outcome
        outcome = "expired"
        exit_price = float(future["price"].iloc[-1])

        future_prices = future["price"].values
        for p in future_prices:
            if p >= tp_price:
                outcome = "win"
                exit_price = tp_price
                break
            elif p <= stop:
                outcome = "loss"
                exit_price = float(stop)
                break
        else:
            # Time expiry — mark win/loss based on final price
            outcome = "win" if exit_price >= entry else "loss"

        pnl = (exit_price - entry) * n_shares
        pnl_pct = (exit_price - entry) / entry
        portfolio += pnl

        trades.append(
            dict(
                timestamp=str(sig["timestamp"]),
                symbol=sym,
                pattern=sig.get("pattern_name", ""),
                regime=sig.get("regime", ""),
                entry=entry,
                stop=stop,
                tp=tp_price,
                exit=exit_price,
                outcome=outcome,
                pnl=pnl,
                pnl_pct=pnl_pct,
                portfolio=portfolio,
                confidence=conf,
            )
        )

    stats = {}
    if trades:
        df = pd.DataFrame(trades)
        wins = df[df["outcome"] == "win"]
        losses = df[df["outcome"] == "loss"]
        win_rate = len(wins) / len(df) if len(df) > 0 else 0
        total_wins = wins["pnl"].sum() if not wins.empty else 0
        total_losses = abs(losses["pnl"].sum()) if not losses.empty else 1e-9
        profit_factor = total_wins / total_losses

        roll_max = df["portfolio"].cummax()
        max_dd = ((df["portfolio"] - roll_max) / roll_max).min()

        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        daily = df.set_index("timestamp")["pnl_pct"].resample("D").sum()
        sharpe = (daily.mean() / daily.std() * (252 ** 0.5)) if daily.std() > 0 else 0.0

        stats = dict(
            total_trades=len(df),
            win_rate=win_rate,
            avg_win_pct=float(wins["pnl_pct"].mean()) if not wins.empty else 0.0,
            avg_loss_pct=float(losses["pnl_pct"].mean()) if not losses.empty else 0.0,
            profit_factor=profit_factor,
            max_drawdown=float(max_dd),
            sharpe=sharpe,
            total_return_pct=float((portfolio - portfolio_start) / portfolio_start),
            final_portfolio=portfolio,
        )

    import json
    return pd.DataFrame(trades).to_json() if trades else "[]", json.dumps(stats)


# ── Regime band helper ────────────────────────────────────────────────────────

def _add_regime_bands(fig, regime_df, opacity=REGIME_BG_OPACITY):
    if regime_df.empty:
        return
    prev = None
    for _, row in regime_df.iterrows():
        if prev is not None:
            fig.add_vrect(
                x0=prev["timestamp"],
                x1=row["timestamp"],
                fillcolor=REGIME_COLORS.get(str(prev["regime"]), "#7f8c8d"),
                opacity=opacity,
                layer="below",
                line_width=0,
            )
        prev = row
    if prev is not None:
        fig.add_vrect(
            x0=prev["timestamp"],
            x1=pd.Timestamp(regime_df["timestamp"].max()) + pd.Timedelta(minutes=5),
            fillcolor=REGIME_COLORS.get(str(prev["regime"]), "#7f8c8d"),
            opacity=opacity,
            layer="below",
            line_width=0,
        )


# ── Panel 1: Regime Timeline ──────────────────────────────────────────────────

def _panel_regime(regime_df, spy_ticks):
    st.subheader("Regime Timeline")
    st.caption(
        "SPY price with GREEN / YELLOW / RED macro regime bands. "
        "Regime is classified by SPY vs EMA21 + SMA50 with JNK/TLT cross-validation. "
        "Updated every 5 minutes by playbook_runner."
    )

    if regime_df.empty or len(regime_df) < 5:
        st.info("Accumulating regime data…")
        return

    fig = go.Figure()
    _add_regime_bands(fig, regime_df, opacity=0.18)

    price_series = spy_ticks if spy_ticks is not None and not spy_ticks.empty else None
    if price_series is not None:
        fig.add_trace(
            go.Scatter(
                x=price_series["created_at"],
                y=price_series["price"],
                name="SPY (ticks)",
                line=dict(color="#2c3e50", width=1.5),
                hovertemplate="%{x|%b %d %H:%M}<br>SPY: $%{y:.2f}<extra></extra>",
            )
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=regime_df["timestamp"],
                y=regime_df["spy_price"],
                name="SPY (playbook reading)",
                line=dict(color="#2c3e50", width=1.5),
                hovertemplate="%{x|%b %d %H:%M}<br>SPY: $%{y:.2f}<extra></extra>",
            )
        )

    fig.add_trace(
        go.Scatter(
            x=regime_df["timestamp"],
            y=regime_df["ema21"],
            name="EMA21",
            line=dict(color="#3498db", width=1, dash="dot"),
            hovertemplate="EMA21: $%{y:.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=regime_df["timestamp"],
            y=regime_df["sma50"],
            name="SMA50",
            line=dict(color="#e74c3c", width=1, dash="dot"),
            hovertemplate="SMA50: $%{y:.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis_title="Date",
        yaxis_title="Price ($)",
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Regime distribution pills
    dist = regime_df["regime"].value_counts()
    total = dist.sum()
    icons = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}
    cols = st.columns(len(dist))
    for i, (regime, cnt) in enumerate(dist.items()):
        pct = cnt / total * 100
        cols[i].metric(
            f"{icons.get(regime, '⚪')} {regime}",
            f"{pct:.1f}%",
            f"{cnt:,} scans",
        )

    # Most recent regime reason
    latest = regime_df.iloc[-1]
    st.info(
        f"**Current regime:** {latest['regime']} — {latest['reason']}  "
        f"(confidence: {latest['confidence']:.0%})"
    )


# ── Panel 2: Signal Detection Log ─────────────────────────────────────────────

def _panel_signals(signals_df):
    st.subheader("Signal Detection Log")
    st.caption(
        "Every signal detected by the 6-pattern catalog (EpisodicPivot, MomentumBurst, "
        "ElephantBar, VCP, HighTightFlag, InsideBar212). "
        "Current data shows real detections — zero means a detector found no qualifying setups."
    )

    if signals_df.empty:
        st.info("No signals detected in this period.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Detections", f"{len(signals_df):,}")
    c2.metric("Unique Tickers", f"{signals_df['symbol'].nunique()}")
    c3.metric("Patterns Active", f"{signals_df['pattern_name'].nunique()}")
    c4.metric("Avg Confidence", f"{signals_df['confidence'].mean():.1%}")

    col1, col2 = st.columns(2)

    with col1:
        pat_counts = signals_df["pattern_name"].value_counts().reset_index()
        pat_counts.columns = ["Pattern", "Count"]
        fig_pat = px.bar(
            pat_counts,
            x="Count",
            y="Pattern",
            orientation="h",
            color="Pattern",
            height=220,
            title="Detections by Pattern",
        )
        fig_pat.update_layout(margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
        st.plotly_chart(fig_pat, use_container_width=True)

    with col2:
        regime_counts = signals_df["regime"].value_counts().reset_index()
        regime_counts.columns = ["Regime", "Count"]
        fig_reg = px.bar(
            regime_counts,
            x="Regime",
            y="Count",
            color="Regime",
            color_discrete_map=REGIME_COLORS,
            height=220,
            title="Detections by Regime at Detection",
        )
        fig_reg.update_layout(margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
        st.plotly_chart(fig_reg, use_container_width=True)

    # Daily detection bar chart
    daily = (
        signals_df.copy()
        .assign(day=pd.to_datetime(signals_df["timestamp"]).dt.date)
        .groupby("day")
        .size()
        .reset_index(name="count")
    )
    fig_daily = px.bar(daily, x="day", y="count", height=200, title="Signal Detections Per Day")
    fig_daily.update_layout(margin=dict(l=0, r=0, t=30, b=0), xaxis_title="", yaxis_title="Detections")
    st.plotly_chart(fig_daily, use_container_width=True)

    # Tables
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("**Top Tickers**")
        top = (
            signals_df.groupby("symbol")
            .size()
            .sort_values(ascending=False)
            .head(10)
            .reset_index(name="Detections")
            .rename(columns={"symbol": "Ticker"})
        )
        st.dataframe(top, use_container_width=True, hide_index=True)

    with col_b:
        st.write("**Recent Detections**")
        recent = (
            signals_df.sort_values("timestamp", ascending=False)
            [["timestamp", "symbol", "pattern_name", "regime", "confidence", "entry_price"]]
            .head(20)
            .rename(columns={
                "timestamp": "Time",
                "symbol": "Ticker",
                "pattern_name": "Pattern",
                "regime": "Regime",
                "confidence": "Conf",
                "entry_price": "Entry ($)",
            })
        )
        if "Conf" in recent.columns:
            recent["Conf"] = recent["Conf"].map(lambda x: f"{x:.0%}" if pd.notna(x) else "")
        if "Entry ($)" in recent.columns:
            recent["Entry ($)"] = recent["Entry ($)"].map(lambda x: f"${x:.2f}" if pd.notna(x) else "")
        st.dataframe(recent, use_container_width=True, hide_index=True)


# ── Panel 3: Hypothetical P&L ─────────────────────────────────────────────────

def _panel_pnl(signals_df, ticks_df, regime_df, tp_pct, portfolio_start):
    st.subheader("Hypothetical P&L — Simulated Paper Trading")

    st.warning(
        "⚠️ **SIMULATION ONLY** — Calculates what would have happened if every signal "
        "detection triggered a paper-mode trade with fixed position sizing. "
        "This is NOT real trading history. Past simulated performance does not indicate "
        "future results."
    )

    if signals_df.empty:
        st.info("No signals to simulate.")
        return

    valid = signals_df.dropna(subset=["entry_price", "stop_price"])
    valid = valid[
        (valid["entry_price"] > 0)
        & (valid["stop_price"] > 0)
        & (valid["stop_price"] < valid["entry_price"])
    ].reset_index(drop=True)

    if valid.empty or ticks_df.empty:
        st.info("Insufficient data for simulation (need valid entry/stop prices and future tick data).")
        return

    trades_json, stats_json = simulate_pnl(
        valid.to_json(),
        ticks_df.to_json(),
        tp_pct=tp_pct,
        position_pct=0.02,
        portfolio_start=float(portfolio_start),
    )

    import json
    stats = json.loads(stats_json)
    if not stats:
        st.info("No completed simulated trades found (ticks needed after each signal timestamp).")
        return

    trades_df = pd.read_json(trades_json)
    if trades_df.empty:
        st.info("No trades in simulation.")
        return

    trades_df["timestamp"] = pd.to_datetime(trades_df["timestamp"], utc=True)

    # Stats row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric(
        "Total Return",
        f"{stats['total_return_pct']:+.1%}",
        f"${stats['final_portfolio']:,.0f} final",
    )
    c2.metric("Win Rate", f"{stats['win_rate']:.1%}", f"{stats['total_trades']} trades")
    c3.metric("Profit Factor", f"{stats['profit_factor']:.2f}")
    c4.metric("Sharpe Ratio", f"{stats['sharpe']:.2f}")
    c5.metric("Max Drawdown", f"{stats['max_drawdown']:.1%}")
    c6.metric(
        "Avg Win / Loss",
        f"{stats['avg_win_pct']:+.1%}",
        f"Loss: {stats['avg_loss_pct']:+.1%}",
    )

    # Equity curve
    fig = go.Figure()
    _add_regime_bands(fig, regime_df, opacity=0.07)

    fig.add_trace(
        go.Scatter(
            x=trades_df["timestamp"],
            y=trades_df["portfolio"],
            name="Portfolio Value",
            fill="tozeroy",
            fillcolor="rgba(52,152,219,0.08)",
            line=dict(color="#3498db", width=2),
            hovertemplate="%{x|%b %d}<br>Portfolio: $%{y:,.2f}<extra></extra>",
        )
    )
    fig.add_hline(
        y=float(portfolio_start),
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Start: ${portfolio_start:,.0f}",
    )

    fig.update_layout(
        height=350,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    # P&L by regime
    st.write("**P&L by Regime at Detection** (measures whether regime gate adds value)")
    if "regime" in trades_df.columns and not trades_df["regime"].isna().all():
        regime_pnl = (
            trades_df.groupby("regime")
            .agg(
                Trades=("pnl", "count"),
                Win_Rate=("outcome", lambda x: (x == "win").mean()),
                Total_PnL=("pnl", "sum"),
                Avg_Return=("pnl_pct", "mean"),
            )
            .reset_index()
        )
        regime_pnl.columns = ["Regime", "Trades", "Win Rate", "Total P&L ($)", "Avg Return"]
        regime_pnl["Win Rate"] = regime_pnl["Win Rate"].map("{:.1%}".format)
        regime_pnl["Total P&L ($)"] = regime_pnl["Total P&L ($)"].map("${:,.2f}".format)
        regime_pnl["Avg Return"] = regime_pnl["Avg Return"].map("{:+.2%}".format)
        st.dataframe(regime_pnl, use_container_width=True, hide_index=True)

    # Config reminder
    st.caption(
        f"Simulation parameters: TP={tp_pct:.0%} above entry · SL=stop_price from signal · "
        f"Position size=2% of portfolio × confidence · Starting portfolio=${portfolio_start:,.0f}"
    )

    with st.expander("Trade Log — last 30 simulated trades"):
        view = trades_df.tail(30)[
            ["timestamp", "symbol", "pattern", "regime", "entry", "exit", "outcome", "pnl_pct", "portfolio"]
        ].copy()
        view["pnl_pct"] = view["pnl_pct"].map("{:+.2%}".format)
        view["entry"] = view["entry"].map("${:.2f}".format)
        view["exit"] = view["exit"].map("${:.2f}".format)
        view["portfolio"] = view["portfolio"].map("${:,.2f}".format)
        st.dataframe(view, use_container_width=True, hide_index=True)


# ── Panel 4: Risk Metrics ──────────────────────────────────────────────────────

def _panel_risk(risk_df, regime_df):
    st.subheader("Risk Metrics Over Time")
    st.caption(
        "Fractional Kelly position size, CVaR 99th percentile, and NAV from the "
        "playbook risk engine. Logged every 5 minutes by playbook_runner."
    )

    if risk_df.empty:
        st.info("Accumulating risk data…")
        return

    # Kelly and CVaR
    fig = go.Figure()
    _add_regime_bands(fig, regime_df, opacity=0.08)

    kelly_data = risk_df[risk_df["kelly_size"].notna() & (risk_df["kelly_size"] > 0)]
    cvar_data = risk_df[risk_df["cvar_99"].notna() & (risk_df["cvar_99"] != 0)]

    if not kelly_data.empty:
        fig.add_trace(
            go.Scatter(
                x=kelly_data["timestamp"],
                y=kelly_data["kelly_size"],
                name="Kelly Fraction",
                line=dict(color="#27ae60", width=1.5),
                hovertemplate="Kelly: %{y:.4f}<extra></extra>",
            )
        )

    if not cvar_data.empty:
        fig.add_trace(
            go.Scatter(
                x=cvar_data["timestamp"],
                y=cvar_data["cvar_99"].abs(),
                name="CVaR 99%",
                line=dict(color="#e74c3c", width=1.5),
                yaxis="y2",
                hovertemplate="CVaR 99%: %{y:.4f}<extra></extra>",
            )
        )

    if kelly_data.empty and cvar_data.empty:
        st.info(
            "Kelly and CVaR are near zero across this window. "
            "The risk engine needs active positions (live equity ticks + trade history) "
            "to compute meaningful values. This reflects the paper-mode state."
        )
    else:
        fig.update_layout(
            height=280,
            margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(title="Kelly Fraction"),
            yaxis2=dict(title="CVaR 99%", overlaying="y", side="right"),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Peak NAV (SPY benchmark tracked by risk engine)
    peak_data = risk_df[risk_df["peak_equity"].notna() & (risk_df["peak_equity"] > 0)]
    if not peak_data.empty:
        fig2 = go.Figure()
        fig2.add_trace(
            go.Scatter(
                x=peak_data["timestamp"],
                y=peak_data["peak_equity"],
                name="Peak NAV (SPY benchmark)",
                line=dict(color="#3498db", width=1.5, dash="dot"),
                fill="tozeroy",
                fillcolor="rgba(52,152,219,0.05)",
                hovertemplate="Peak NAV: $%{y:.2f}<extra></extra>",
            )
        )
        fig2.update_layout(
            height=220,
            margin=dict(l=10, r=10, t=10, b=10),
            yaxis_title="$ (SPY as NAV proxy)",
            title="SPY Peak NAV Tracked by Risk Engine",
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.caption("Peak NAV not yet tracked — requires active portfolio positions.")


# ── Panel 5: Pipeline Health ───────────────────────────────────────────────────

def _panel_health(regime_df, signals_df, risk_df):
    st.subheader("Pipeline Health / Data Quality")
    st.caption("Data freshness and continuity per source. Use this to diagnose stale or missing data.")

    now = pd.Timestamp.now("UTC")

    def _badge(age_min, warn=10, err=60):
        if age_min < warn:
            return "🟢 OK"
        elif age_min < err:
            return "🟡 STALE"
        return "🔴 OFFLINE"

    rows = []

    # Playbook runner (from in-memory data)
    if not regime_df.empty:
        last_ts = pd.to_datetime(regime_df["timestamp"].max(), utc=True)
        age = (now - last_ts).total_seconds() / 60
        rows.append({
            "Service": "playbook_runner",
            "Status": _badge(age, warn=10, err=30),
            "Last Event": str(last_ts)[:19] + " UTC",
            "Detail": f"{len(regime_df):,} regime logs in window",
        })

    # DB health
    db_h = load_db_health()
    if not db_h.empty:
        r = db_h.iloc[0]

        for col_key, svc, warn_min, err_min, note in [
            ("last_crypto", "polygon_ingestor (crypto)", 20, 90, "24/7 — should always be fresh"),
            ("last_equity", "polygon_ingestor (equities)", 480, 1440, "Market hours only (9:30–16:00 ET)"),
        ]:
            val = r[col_key]
            if val and str(val) not in ("None", "NaT", ""):
                ts = pd.Timestamp(val)
                if ts.tzinfo is None:
                    ts = ts.tz_localize("UTC")
                age = (now - ts).total_seconds() / 60
                rows.append({
                    "Service": svc,
                    "Status": _badge(age, warn_min, err_min),
                    "Last Event": str(ts)[:19] + " UTC",
                    "Detail": note,
                })

        if r["last_trade"] and str(r["last_trade"]) not in ("None", "NaT", ""):
            rows.append({
                "Service": "trade_history",
                "Status": "🟢 OK",
                "Last Event": str(r["last_trade"])[:19] + " UTC",
                "Detail": f"{r['total_trades']:,} total trade records",
            })

    # Redis intel bus
    redis_client = _get_redis()
    intel_keys = [
        ("intel:playbook_snapshot", 10, 20),
        ("intel:spy_trend", 10, 20),
        ("intel:vix_level", 10, 20),
        ("intel:btc_sentiment", 15, 30),
        ("intel:geopolitical_risk", 120, 300),
        ("intel:kalshi_orderbook_summary", 15, 30),
        ("strategy_mode", 360, 1440),
    ]
    if redis_client:
        for key, warn, err in intel_keys:
            ttl = redis_client.ttl(key)
            size = redis_client.strlen(key)
            if size == 0 or ttl == -2:
                status = "🔴 MISSING"
                detail = "Key not found in Redis"
            elif ttl == -1:
                status = "🟢 OK (persistent)"
                detail = f"{size} bytes, no expiry"
            else:
                status = "🟢 ACTIVE"
                detail = f"{size} bytes, TTL={ttl}s"
            rows.append({"Service": f"Redis: {key}", "Status": status, "Last Event": "—", "Detail": detail})
    else:
        rows.append({
            "Service": "Redis intel bus",
            "Status": "🟡 UNREACHABLE from dashboard",
            "Last Event": "—",
            "Detail": "Add REDIS_HOST=redis to cemini_os env if needed",
        })

    health_df = pd.DataFrame(rows)
    if not health_df.empty:
        st.dataframe(health_df, use_container_width=True, hide_index=True)

    # Data volume summary
    st.write("**Data Volume Summary (selected window)**")
    v1, v2, v3, v4 = st.columns(4)
    v1.metric("Regime Logs", f"{len(regime_df):,}")
    v2.metric("Signal Detections", f"{len(signals_df):,}")
    v3.metric("Risk Snapshots", f"{len(risk_df):,}")
    if not db_h.empty:
        v4.metric("Ticks (last hour)", str(db_h.iloc[0].get("ticks_last_hour", 0)))

    # Daily cadence chart
    if not regime_df.empty:
        daily_r = (
            regime_df.copy()
            .assign(day=pd.to_datetime(regime_df["timestamp"]).dt.date)
            .groupby("day")
            .size()
            .reset_index(name="scans")
        )
        fig = px.bar(
            daily_r,
            x="day",
            y="scans",
            title="Playbook Runner Scans Per Day (target ≈ 288 at 5-min interval)",
            height=220,
        )
        fig.add_hline(y=288, line_dash="dash", line_color="green", annotation_text="5-min target")
        fig.update_layout(margin=dict(l=0, r=0, t=35, b=0), xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)


# ── Main entry point ──────────────────────────────────────────────────────────

def render():
    st.title("📊 Step 3: Performance Dashboard")
    st.caption(
        "Paper trading visualization — READ-ONLY. All charts draw from live Postgres data. "
        "Hypothetical P&L is clearly labeled as simulation. No trading behavior is modified."
    )

    # ── Controls ────────────────────────────────────────────────────────────
    ctrl_l, ctrl_r = st.columns([3, 1])
    with ctrl_l:
        min_d = datetime(2026, 2, 25)
        max_d = datetime.now()
        date_range = st.date_input(
            "Date Range",
            value=(min_d.date(), max_d.date()),
            min_value=min_d.date(),
            max_value=max_d.date(),
        )
    with ctrl_r:
        tp_pct = st.number_input(
            "Take Profit %",
            min_value=0.5,
            max_value=10.0,
            value=2.0,
            step=0.5,
            help="Target profit threshold for hypothetical P&L simulation",
        ) / 100.0
        portfolio_start = st.number_input(
            "Starting Portfolio ($)",
            min_value=1000,
            max_value=100000,
            value=10000,
            step=1000,
        )

    if not isinstance(date_range, (list, tuple)) or len(date_range) != 2:
        st.warning("Select a start and end date.")
        return

    start_dt = datetime.combine(date_range[0], datetime.min.time())
    end_dt = datetime.combine(date_range[1], datetime.max.time())

    # ── Load data ────────────────────────────────────────────────────────────
    with st.spinner("Loading performance data…"):
        regime_df = load_regime(start_dt, end_dt)
        signals_df = load_signals(start_dt, end_dt)
        risk_df = load_risk(start_dt, end_dt)

        signal_syms = tuple(sorted(signals_df["symbol"].unique())) if not signals_df.empty else ()
        all_syms = tuple(sorted(set(signal_syms) | {"SPY"}))
        ticks_df = load_ticks(all_syms, start_dt, end_dt)

        spy_ticks = ticks_df[ticks_df["symbol"] == "SPY"].copy() if not ticks_df.empty else pd.DataFrame()
        sim_ticks = (
            ticks_df[ticks_df["symbol"].isin(signal_syms)].copy()
            if not ticks_df.empty and signal_syms
            else pd.DataFrame()
        )

    # Minimum data gate
    if len(regime_df) < 10:
        st.warning(
            f"Only {len(regime_df)} regime logs found. "
            "The playbook_runner logs data every 5 minutes — check that the container is healthy."
        )
        return

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Regime Timeline",
        "🎯 Signal Detections",
        "💰 Hypothetical P&L",
        "⚖️ Risk Metrics",
        "🔬 Pipeline Health",
    ])

    with tab1:
        _panel_regime(regime_df, spy_ticks)

    with tab2:
        _panel_signals(signals_df)

    with tab3:
        _panel_pnl(signals_df, sim_ticks, regime_df, tp_pct, portfolio_start)

    with tab4:
        _panel_risk(risk_df, regime_df)

    with tab5:
        _panel_health(regime_df, signals_df, risk_df)
