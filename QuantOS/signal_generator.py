# CEMINI FINANCIAL SUITE™
# Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
# All Rights Reserved.
import psycopg2
import redis
import json
import time
import os
import pandas as pd
import requests
from datetime import datetime

# 1. Environment Connections
DB_HOST = os.getenv("DB_HOST", "localhost")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# --- State Management ---
active_positions = {} 
CASH_BALANCE = 5000.0 
DAILY_LOSS_LIMIT = 50.0
cumulative_daily_loss = 0.0
last_reset_day = datetime.now().day
MANUAL_MODE = False # --- RE-ENABLE AUTOMATIC BRAIN ---

def connect_db():
    try:
        conn = psycopg2.connect(host=DB_HOST, port=5432, database="qdb", user="admin", password="quest")
        return conn
    except Exception as e:
        print(f"❌ Brain DB Connection Failed: {e}"); return None

def connect_redis():
    try:
        r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True); r.ping()
        return r
    except Exception as e:
        print(f"❌ Brain Redis Connection Failed: {e}"); return None

def update_portfolio_db(conn):
    global active_positions, CASH_BALANCE
    try:
        cursor = conn.cursor(); conn.autocommit = True
        cursor.execute("CREATE TABLE IF NOT EXISTS portfolio_summary (symbol VARCHAR(50), entry_price DOUBLE PRECISION, current_price DOUBLE PRECISION, market_value DOUBLE PRECISION, is_cash BOOLEAN, timestamp TIMESTAMP WITH TIME ZONE);")
        cursor.execute("DELETE FROM portfolio_summary;")
        cursor.execute("INSERT INTO portfolio_summary (symbol, entry_price, current_price, market_value, is_cash, timestamp) VALUES (%s, %s, %s, %s, %s, %s)", ("CASH", 1.0, 1.0, CASH_BALANCE, True, datetime.now()))
        for symbol, pos in active_positions.items():
            cursor.execute("INSERT INTO portfolio_summary (symbol, entry_price, current_price, market_value, is_cash, timestamp) VALUES (%s, %s, %s, %s, %s, %s)", (symbol, pos['entry_price'], pos['max_price'], pos['max_price'], False, datetime.now()))
    except Exception as e: print(f"⚠️ Portfolio Sync Error: {e}")

def send_discord_alert(action, symbol, price, reason=None, rsi=None):
    if not DISCORD_WEBHOOK_URL: return
    color = 3066993 if action.upper() == "BUY" else 15158332
    fields = [{"name": "Symbol", "value": symbol, "inline": True}, {"name": "Price", "value": f"${price:.2f}", "inline": True}]
    if rsi: fields.append({"name": "RSI", "value": f"{rsi:.2f}", "inline": True})
    if reason: fields.append({"name": "Reason", "value": reason, "inline": False})
    payload = {"username": "Cemini Brain", "embeds": [{"title": f"🚨 TRADE SIGNAL: {action.upper()}", "color": color, "fields": fields, "footer": {"text": "Cemini Financial Suite | Intelligence Layer v1.1"}}]}
    try: requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except Exception as e: print(f"⚠️ Discord Alert Failed: {e}")

def get_recent_ticks(conn, symbol, limit=30):
    query = "SELECT timestamp, price FROM raw_market_ticks WHERE symbol = %s ORDER BY timestamp DESC LIMIT %s;"
    try:
        df = pd.read_sql_query(query, conn, params=(symbol, limit))
        if df.empty: return df
        return df.sort_values('timestamp').reset_index(drop=True)
    except Exception as e: print(f"⚠️ DB Read Error: {e}"); return pd.DataFrame()

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1: return None
    delta = prices.diff(); gain = (delta.where(delta > 0, 0)).rolling(window=period).mean(); loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    loss = loss.replace(0, 0.00001); rs = gain / loss; rsi = 100 - (100 / (1 + rs)); return rsi.iloc[-1]

def evaluate_market(df, symbol, redis_client, db_conn):
    global active_positions, CASH_BALANCE, cumulative_daily_loss, last_reset_day
    
    if datetime.now().day != last_reset_day:
        cumulative_daily_loss = 0.0
        last_reset_day = datetime.now().day

    if cumulative_daily_loss >= DAILY_LOSS_LIMIT:
        return

    if len(df) < 15: return
    df['SMA_Short'] = df['price'].rolling(window=3).mean(); df['SMA_Long'] = df['price'].rolling(window=10).mean(); current_rsi = calculate_rsi(df['price'])
    latest = df.iloc[-1]; previous = df.iloc[-2]; current_price = latest['price']; trailing_percent = 0.02
    fear_greed = float(redis_client.get("macro:fear_greed") or 50.0)
    if fear_greed > 80: trailing_percent = 0.01

    if symbol in active_positions:
        pos = active_positions[symbol]
        if current_price > pos['max_price']:
            pos['max_price'] = current_price
            pos['trailing_stop'] = current_price * (1 - trailing_percent)
        death_cross = previous['SMA_Short'] >= previous['SMA_Long'] and latest['SMA_Short'] < latest['SMA_Long']
        if current_price <= pos['trailing_stop'] or death_cross:
            reason = "Trailing Stop" if current_price <= pos['trailing_stop'] else "Death Cross"
            profit_loss = current_price - pos['entry_price']
            if profit_loss < 0:
                cumulative_daily_loss += abs(profit_loss)
                if cumulative_daily_loss >= DAILY_LOSS_LIMIT:
                    redis_client.publish("emergency_stop", f"Daily Loss Limit Hit: ${cumulative_daily_loss:.2f}")
            
            CASH_BALANCE += current_price
            exit_payload = {"pydantic_signal": {"target_system": "QuantOS", "target_brokerage": "Robinhood", "asset_class": "equity", "ticker_or_event": symbol, "action": "sell", "confidence_score": 1.0, "proposed_allocation_pct": 0.0, "agent_reasoning": f"Exit: {reason}"}, "timestamp": str(latest['timestamp']), "reason": reason, "price": current_price}
            redis_client.publish("trade_signals", json.dumps(exit_payload))
            send_discord_alert("SELL", symbol, current_price, reason=f"{reason} | Daily Loss: ${cumulative_daily_loss:.2f}")
            del active_positions[symbol]
        return

    sma_crossover = previous['SMA_Short'] <= previous['SMA_Long'] and latest['SMA_Short'] > latest['SMA_Long']
    strategy_mode = redis_client.get("strategy_mode") or "standard"
    rsi_threshold = 50 if strategy_mode == "conservative" else 70
    not_overbought = current_rsi < rsi_threshold if current_rsi else False

    if sma_crossover and not_overbought:
        CASH_BALANCE -= current_price
        active_positions[symbol] = {"entry_price": current_price, "max_price": current_price, "trailing_stop": current_price * (1 - trailing_percent)}
        entry_payload = {"pydantic_signal": {"target_system": "QuantOS", "target_brokerage": "Robinhood", "asset_class": "equity", "ticker_or_event": symbol, "action": "buy", "confidence_score": 0.90, "proposed_allocation_pct": 0.02, "agent_reasoning": f"Entry: SMA Cross RSI < {rsi_threshold}"}, "timestamp": str(latest['timestamp']), "strategy": "Intelligence_v1", "price": current_price, "rsi": current_rsi}
        redis_client.publish("trade_signals", json.dumps(entry_payload))
        send_discord_alert("BUY", symbol, current_price, reason=f"FGI: {fear_greed:.1f}", rsi=current_rsi)

def main():
    print("🧠 QuantOS Brain v3.3 Booting Up...")
    conn = connect_db(); r = connect_redis()
    if not conn or not r: return
    symbols_to_track = ["SPY", "QQQ", "BTC"]
    while True:
        for symbol in symbols_to_track:
            df = get_recent_ticks(conn, symbol, limit=30)
            if not df.empty: evaluate_market(df, symbol, r, conn)
        update_portfolio_db(conn)
        time.sleep(5)

if __name__ == "__main__":
    main()
