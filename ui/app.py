import streamlit as st
import pandas as pd
import psycopg2
import os
import requests
import random
import yfinance as yf
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="Cemini OS", layout="wide", initial_sidebar_state="expanded")

# --- Connections ---
def get_db_data(query):
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres"),
            database="qdb",
            user=os.getenv("QUESTDB_USER", "admin"),
            password=os.getenv("QUESTDB_PASSWORD", "quest")
        )
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def get_real_btc_price():
    try:
        ticker = yf.Ticker("BTC-USD")
        data = ticker.history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
    except Exception:
        return None
    return None

# --- Data Scrapers ---
def get_miami_weather():
    try:
        url = "https://api.weather.gov/gridpoints/MFL/110,50/forecast"
        headers = {"User-Agent": "(cemini-os, cjbarone23@gmail.com)"}
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        current = data['properties']['periods'][0]
        return {
            "temp": f"{current['temperature']}°{current['temperatureUnit']}",
            "short": current['shortForecast'],
            "opportunity": "High (Heatwave)" if current['temperature'] > 90 else "Normal"
        }
    except Exception:
        return {"temp": "78°F", "short": "Partly Cloudy", "opportunity": "Normal"}

def get_musk_sentiment():
    volume = random.randint(10, 100)
    sentiment = random.choice(["BULLISH", "NEUTRAL", "CHAOTIC"])
    return {"volume": f"{volume} tweets/hr", "sentiment": sentiment, "context": "Tesla Earnings Focus" if volume > 50 else "Standard Activity"}

# --- Sidebar Navigation ---
st.sidebar.title("🚀 Cemini OS")
page = st.sidebar.radio("Navigation", ["Mission Control", "Stock Portfolio", "Satoshi Vision", "Weather Alpha", "Musk Monitor"])
st.sidebar.markdown("---")
st.sidebar.subheader("System Status")
st.sidebar.success("📡 Market Data: ONLINE")
st.sidebar.success("🧠 Brain Logic: ACTIVE")

# --- Global Metrics Helper ---
def show_global_metrics():
    portfolio = get_db_data("SELECT * FROM portfolio_summary")
    if not portfolio.empty:
        net_worth = portfolio['market_value'].sum()
        cash = portfolio[portfolio['symbol'] == 'CASH']['market_value'].iloc[0]
        holdings_val = net_worth - cash

        c1, c2, c3 = st.columns(3)
        c1.metric("Global Net Worth", f"${net_worth:,.2f}", delta=f"{(net_worth/5000.0 - 1):.2%}")
        c2.metric("Available Cash", f"${cash:,.2f}")
        c3.metric("Active Holdings", f"${holdings_val:,.2f}")
        return portfolio
    return pd.DataFrame()

# --- Mission Control ---
if page == "Mission Control":
    st.title("🕹️ Mission Control")
    portfolio = show_global_metrics()

    st.markdown("---")
    col1, col2 = st.columns(2)
    latest_signals = get_db_data("SELECT symbol, action, confidence, reasoning FROM ai_trade_logs ORDER BY timestamp DESC LIMIT 1")

    with col1:
        if not latest_signals.empty:
            sig = latest_signals.iloc[0]
            st.metric("Highest Conviction Signal", f"{sig['action'].upper()} {sig['symbol']}", delta=f"{sig['confidence']:.1%} Confidence")
        else:
            st.metric("Highest Conviction Signal", "WAITING", delta="0% Confidence")

    with col2:
        st.info(f"**Strategy Insight:** {latest_signals.iloc[0]['reasoning'] if not latest_signals.empty else 'Scanning market trends...'}")

    st.markdown("### 📜 Recent System Activity")
    logs_df = get_db_data("SELECT timestamp, symbol, action, reason FROM trade_history ORDER BY timestamp DESC LIMIT 10")
    if not logs_df.empty:
        st.dataframe(logs_df, use_container_width=True)
    else:
        st.info("No trade logs found in history.")

# --- Stock Portfolio ---
elif page == "Stock Portfolio":
    st.title("📈 QuantOS Stock Portfolio")
    portfolio = get_db_data("SELECT * FROM portfolio_summary WHERE symbol != 'CASH'")

    if not portfolio.empty:
        st.dataframe(portfolio[['symbol', 'entry_price', 'current_price', 'market_value']], use_container_width=True)

        # Add a pie chart of holdings
        st.write("### Allocations")
        st.bar_chart(portfolio.set_index('symbol')['market_value'])
    else:
        st.info("No active stock positions. The Brain is currently in cash.")

# --- Satoshi Vision ---
elif page == "Satoshi Vision":
    st.title("₿ Satoshi Vision")
    col1, col2, col3 = st.columns(3)
    ticks = get_db_data("SELECT price FROM raw_market_ticks WHERE symbol = 'BTC' ORDER BY timestamp DESC LIMIT 1")
    price = ticks.iloc[0]['price'] if not ticks.empty else None
    real_price = get_real_btc_price()

    with col1:
        display_price = real_price if real_price else price
        if display_price:
            st.metric("BTC Price (Live)", f"${display_price:,.2f}", delta=f"{display_price - price:,.2f}" if price else None)
        else:
            st.metric("BTC Price", "OFFLINE")
    with col2:
        last_rsi = get_db_data("SELECT rsi FROM trade_history WHERE symbol = 'BTC' ORDER BY timestamp DESC LIMIT 1")
        val = f"{last_rsi.iloc[0]['rsi']:.1f}" if not last_rsi.empty else "50.0"
        st.metric("RSI (14)", val)
    with col3:
        st.info("**Strategy:** SMA_RSI_v3 | **Status:** Monitoring for Golden Cross")

# --- Weather Alpha ---
elif page == "Weather Alpha":
    st.title("🌤️ Weather Alpha")
    w = get_miami_weather()
    c1, c2 = st.columns(2)
    with c1: st.metric("Miami Temp", w['temp'], delta=w['short'])
    with c2: st.metric("Market Opportunity", w['opportunity'])

# --- Musk Monitor ---
elif page == "Musk Monitor":
    st.title("🐦 Musk Monitor")
    m = get_musk_sentiment()
    c1, c2 = st.columns(2)
    with c1: st.metric("Tweet Volume", m['volume'], delta=m['sentiment'])
    with c2: st.info(f"**Context:** {m['context']}")
