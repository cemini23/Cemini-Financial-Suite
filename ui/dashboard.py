from deephaven import ui
from deephaven.plot import express as dx
import psycopg2
import pandas as pd
import os

# --- 1. LIVE DATA STREAMING ENGINE ---

def fetch_db_stream(table_name: str, limit: int = 500):
    """
    Queries Postgres for the absolute latest ticking data.
    """
    host = os.getenv("DB_HOST", "postgres")
    try:
        conn = psycopg2.connect(
            host=host, 
            port=5432, 
            user="admin", 
            password="quest", 
            database="qdb"
        )
        query = f"SELECT * FROM {table_name} ORDER BY timestamp DESC LIMIT {limit}"
        return pd.read_sql(query, conn)
    except Exception as e:
        print(f"❌ UI: Error fetching {table_name}: {e}")
        return pd.DataFrame()

# --- 2. DASHBOARD COMPONENTS ---

@ui.component
def quant_os_dashboard():
    """
    Real-time Operations Center.
    Visualizes raw ticks, aggregated OHLCV, and AI decisions.
    """
    # Load ticking datasets
    raw_ticks = fetch_db_stream("raw_market_ticks")
    ai_logs = fetch_db_stream("ai_trade_logs", limit=100)

    # Price Velocity Chart
    tick_chart = dx.line(
        raw_ticks, 
        x="timestamp", 
        y="price", 
        by="symbol",
        title="Live Tick Firehose (Postgres Feed)"
    )

    return ui.flex(
        ui.heading("💎 Cemini Quantitative Dashboard", level=1),
        
        # Row 1: The Firehose
        ui.flex(
            ui.view(tick_chart, flex_grow=1),
            direction="row",
            height="45vh"
        ),
        
        ui.divider(size="M"),
        
        # Row 2: Hard Numbers & AI Reasoning
        ui.flex(
            ui.flex(
                ui.heading("Raw Ticks", level=3),
                ui.table(raw_ticks),
                direction="column",
                flex_grow=1
            ),
            ui.flex(
                ui.heading("CIO Decision Audit", level=3),
                ui.table(ai_logs),
                direction="column",
                flex_grow=1
            ),
            direction="row",
            gap="size-200",
            height="45vh"
        ),
        
        direction="column",
        gap="size-300",
        padding="size-400",
        height="100vh"
    )

# Render Dashboard
cemini_ui = quant_os_dashboard()
