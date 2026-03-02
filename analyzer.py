import pandas as pd
import psycopg2
import redis
import time
import os
import json
import requests
from core.intel_bus import IntelPublisher

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_discord_report(win_rate, mode, total_trades):
    if not DISCORD_WEBHOOK_URL: return
    color = 3066993 if mode == "aggressive" else 15158332
    payload = {"username": "Cemini Analyzer", "embeds": [{"title": "📊 Performance Report", "description": "The Coach has finished the hourly review.", "color": color, "fields": [{"name": "Current Mode", "value": mode.capitalize(), "inline": True}, {"name": "Win Rate", "value": f"{win_rate:.1%}", "inline": True}, {"name": "Total Trades", "value": str(total_trades), "inline": True}], "footer": {"text": "Cemini Financial Suite | Evolution v1.0"}}]}
    try: requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except: pass

def send_heatseeker_alert(symbol, spike_ratio):
    if not DISCORD_WEBHOOK_URL: return
    payload = {"username": "Cemini Heatseeker", "content": f"🔥 **HEATSEEKER ALERT**: ${symbol} mention density spiked **{spike_ratio:.1f}x** in the last 15m!\n🧠 Brain Status: Watching for SMA crossover to confirm entry."}
    try: requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except: pass

def send_decoupling_alert(pair, old_corr, new_corr):
    if not DISCORD_WEBHOOK_URL: return
    payload = {"username": "Cemini Matrix", "content": f"⚠️ **DECOUPLING ALERT**: {pair} correlation dropped from **{old_corr:.2f}** to **{new_corr:.2f}**!\n📉 Logic: Market regime shift detected. Risk parameters adjusted."}
    try: requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except: pass

def check_heatseeker_spikes(conn):
    print("🔥 Analyzer: Checking for Heatseeker spikes...")
    try:
        query = """
            WITH recent AS (SELECT symbol, COUNT(*) as recent_count FROM sentiment_logs WHERE timestamp > NOW() - INTERVAL '15 minutes' GROUP BY symbol),
            baseline AS (SELECT symbol, COUNT(*) / 16.0 as baseline_count FROM sentiment_logs WHERE timestamp > NOW() - INTERVAL '4 hours' AND timestamp <= NOW() - INTERVAL '15 minutes' GROUP BY symbol)
            SELECT r.symbol, r.recent_count, b.baseline_count FROM recent r JOIN baseline b ON r.symbol = b.symbol WHERE r.recent_count > (b.baseline_count * 3) AND r.recent_count > 10;
        """
        df = pd.read_sql(query, conn)
        conn.commit()
        for _, row in df.iterrows():
            ratio = row['recent_count'] / row['baseline_count'] if row['baseline_count'] > 0 else 10.0
            send_heatseeker_alert(row['symbol'], ratio)
    except Exception as e:
        print(f"⚠️ Heatseeker Query Error: {e}")
        conn.rollback()

def improve_logic():
    print("🧠 The Coach (Analyzer) Initialized...")
    while True:
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'postgres'),
                database=os.getenv('POSTGRES_DB', 'qdb'),
                user=os.getenv('POSTGRES_USER', 'admin'),
                password=os.getenv('POSTGRES_PASSWORD', 'quest'),
                options="-c idle_in_transaction_session_timeout=600000",
            )
            r = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=6379, password=os.getenv('REDIS_PASSWORD', 'cemini_redis_2026'), decode_responses=True)
            break
        except: time.sleep(5)

    last_hourly_review = 0
    last_heat_check = 0
    last_corr_check = 0
    last_intel_publish = 0   # Intel Bus refresh: every 4 min (< 5 min TTL)
    prev_btc_spy_corr = None

    while True:
        now = time.time()

        # 1. Heatseeker Check (Every 15 mins)
        if now - last_heat_check > 900:
            check_heatseeker_spikes(conn)
            last_heat_check = now

        # 2. Correlation Check (Every 30 mins)
        if now - last_corr_check > 1800:
            print("🔗 Analyzer: Checking correlation matrix...")
            try:
                df_corr = pd.read_sql("SELECT * FROM v_correlation_metrics", conn)
                conn.commit()
                if not df_corr.empty:
                    matches = df_corr[df_corr['pair'] == 'BTC/SPY']
                    if not matches.empty:
                        btc_spy = matches['coefficient'].iloc[0]
                        if prev_btc_spy_corr is not None:
                            if (prev_btc_spy_corr - btc_spy) > 0.5:
                                send_decoupling_alert("BTC/SPY", prev_btc_spy_corr, btc_spy)
                        prev_btc_spy_corr = btc_spy
                        r.set("intel:btc_spy_corr", float(btc_spy or 0))
                last_corr_check = now
            except Exception as e:
                print(f"⚠️ Correlation Error: {e}")
                conn.rollback()

        # 3. Intel Bus refresh (Every 4 mins — keeps VIX/SPY signals alive within 5 min TTL)
        if now - last_intel_publish > 240:
            try:
                fgi_val = r.get("macro:fear_greed")
                if fgi_val:
                    # VIX proxy: maps FGI (0=fear, 100=greed) → VIX-like float.
                    # FGI=10 → proxy=45, FGI=50 → proxy=25, FGI=80 → proxy=10.
                    vix_proxy = max(10.0, 50.0 - (float(fgi_val) / 2.0))
                    IntelPublisher.publish("intel:vix_level", round(vix_proxy, 1), "analyzer")

                # SPY trend from strategy_mode in Redis.
                # "sniper" (extreme fear) maps to "neutral" — extreme fear is a contrarian
                # buy signal, not a bearish penalty on top of the regime gate's own RED filter.
                _mode = r.get("strategy_mode") or "neutral"
                _spy_map = {"aggressive": "bullish", "sniper": "neutral", "conservative": "neutral"}
                IntelPublisher.publish("intel:spy_trend", _spy_map.get(_mode, "neutral"), "analyzer", confidence=0.7)

                # Portfolio heat: fraction of active positions across both systems
                _positions_raw = r.get("quantos:active_positions")
                _kalshi_raw = r.get("kalshi:executed_trades")
                _active = len(json.loads(_positions_raw)) if _positions_raw else 0
                _kalshi = len(json.loads(_kalshi_raw)) if _kalshi_raw else 0
                _heat = min(1.0, (_active + _kalshi) / 30.0)
                IntelPublisher.publish("intel:portfolio_heat", round(_heat, 3), "analyzer", confidence=0.9)

                last_intel_publish = now
            except Exception as _be:
                print(f"⚠️ Intel Bus publish failed: {_be}")

        # 4. Performance Review (Every Hour)
        if now - last_hourly_review > 3600:
            try:
                fgi = r.get("macro:fear_greed")
                if fgi and float(fgi) < 25:
                    r.set("strategy_mode", "sniper")
                    if DISCORD_WEBHOOK_URL:
                        requests.post(DISCORD_WEBHOOK_URL, json={"username": "Cemini Coach", "content": f"🎯 **SNIPER_MODE ACTIVE**: Market panic detected (FGI: {float(fgi):.1f})."})

                mode = "neutral"
                df = pd.read_sql("SELECT * FROM trade_history", conn)
                conn.commit()
                if len(df) > 5:
                    sells = df[df['action'] == 'SELL']
                    wins = len(sells[sells['reason'] != 'SL'])
                    win_rate = wins / len(sells) if len(sells) > 0 else 0.5
                    mode = "conservative" if win_rate < 0.45 else "aggressive"
                    r.set("strategy_mode", mode)
                    send_discord_report(win_rate, mode, len(sells))

                last_hourly_review = now
            except Exception as e:
                print(f"⚠️ Coach Error: {e}")
                conn.rollback()

        time.sleep(60)

if __name__ == "__main__":
    improve_logic()
