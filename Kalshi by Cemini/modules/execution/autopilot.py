import asyncio
import json
import os
import time
import base64
import httpx
import redis.asyncio as aioredis
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

from modules.execution.allocator import CapitalAllocator
from modules.satoshi_vision.analyzer import SatoshiAnalyzer
from modules.powell_protocol.analyzer import PowellAnalyzer
from modules.social_alpha.analyzer import SocialAnalyzer
from modules.weather_alpha.analyzer import WeatherAnalyzer
from modules.musk_monitor.predictor import MuskPredictor
from app.core.settings_manager import settings_manager
from app.core.config import add_ui_log, settings
import sys as _sys
import os as _os
_repo_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..', '..'))
if _repo_root not in _sys.path:
    _sys.path.append(_repo_root)
from core.intel_bus import IntelReader

class CeminiAutopilot:
    """
    The Active Trading Daemon.
    Scans all Alpha streams and executes trades via Kelly Allocation.
    """
    def __init__(self):
        self.allocator = CapitalAllocator()
        self.btc_engine = SatoshiAnalyzer()
        self.fed_engine = PowellAnalyzer()
        self.social_engine = SocialAnalyzer()
        self.weather_engine = WeatherAnalyzer()
        self.musk_engine = MuskPredictor()
        self.is_running = False
        self.executed_trades = {} # Maps trade_id to timestamp
        self.blacklist = {} # Maps ticker to cooldown expiry timestamp
        _redis_host = os.getenv('REDIS_HOST', 'redis')
        _redis_pass = os.getenv('REDIS_PASSWORD', 'cemini_redis_2026')
        self._redis_url = f"redis://:{_redis_pass}@{_redis_host}:6379"

    async def _load_state(self):
        """Restore executed_trades and blacklist from Redis on startup."""
        try:
            r = aioredis.from_url(self._redis_url, decode_responses=True)
            try:
                saved_trades = await r.get('kalshi:executed_trades')
                saved_blacklist = await r.get('kalshi:blacklist')
                if saved_trades:
                    self.executed_trades = json.loads(saved_trades)
                    print(f"📦 Restored {len(self.executed_trades)} executed trades from Redis.")
                if saved_blacklist:
                    self.blacklist = json.loads(saved_blacklist)
                    print(f"📦 Restored {len(self.blacklist)} blacklisted tickers from Redis.")
            finally:
                await r.aclose()
        except Exception as e:
            print(f"⚠️ State restore failed: {e}")

    async def _save_state(self):
        """Persist executed_trades and blacklist to Redis."""
        try:
            r = aioredis.from_url(self._redis_url, decode_responses=True)
            try:
                await r.set('kalshi:executed_trades', json.dumps(self.executed_trades))
                await r.set('kalshi:blacklist', json.dumps(self.blacklist))
            finally:
                await r.aclose()
        except Exception as e:
            print(f"⚠️ State save failed: {e}")

    async def execute_kalshi_order(self, trade_data, amount):
        """
        Executes a real order on Kalshi using direct RSA signing and HTTPX.
        Bypasses SDK bugs.
        """
        try:
            key_id = settings.KALSHI_API_KEY
            private_key_path = settings.KALSHI_PRIVATE_KEY_PATH

            if not key_id:
                raise ValueError("KALSHI_API_KEY not found in .env file.")

            with open(private_key_path, 'rb') as f:
                private_key = serialization.load_pem_private_key(f.read(), password=None)

            ticker = None
            if trade_data['module'] == "WEATHER":
                city = trade_data.get('city', 'MIA')
                series_id = f"KXHIGH{city}"
                async with httpx.AsyncClient() as client:
                    m_res = await client.get(f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series_id}&status=open")
                    markets = m_res.json().get('markets', [])
                    if markets:
                        ticker = markets[0]['ticker']
                    else:
                        raise ValueError(f"No active weather markets for {series_id}")

            elif trade_data['module'] == "MUSK":
                async with httpx.AsyncClient() as client:
                    m_res = await client.get(f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXELONATTEND&status=open")
                    markets = m_res.json().get('markets', [])
                    if markets:
                        ticker = markets[0]['ticker']
                    else:
                        raise ValueError("No active Musk Attend markets found.")

            if not ticker: return

            if f"TICKER_{ticker}" in self.executed_trades:
                print(f"⚠️ Blocked: Already traded ticker {ticker} today.")
                return

            count = int(amount / 0.5) or 1
            method = "POST"
            path = "/trade-api/v2/portfolio/orders"
            url = f"https://api.elections.kalshi.com{path}"

            payload = {
                "ticker": str(ticker),
                "action": "buy",
                "type": "market",
                "count": int(count),
                "side": "yes",
                "yes_price": 99
            }

            timestamp = str(int(time.time() * 1000))
            msg = timestamp + method + path
            signature = private_key.sign(msg.encode('utf-8'), padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
            sig_b64 = base64.b64encode(signature).decode('utf-8')

            headers = {"KALSHI-ACCESS-KEY": key_id, "KALSHI-ACCESS-SIGNATURE": sig_b64, "KALSHI-ACCESS-TIMESTAMP": timestamp, "Content-Type": "application/json"}

            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code in [200, 201]:
                    print(f"💰 [LIVE] Direct API Success: {ticker}")
                    add_ui_log(f"LIVE Order SUCCESS: {ticker} ({count} contracts)", level="SUCCESS")
                    self.executed_trades[f"TICKER_{ticker}"] = time.time()
                    await self._save_state()
                    return True
                else:
                    raise Exception(f"HTTP {resp.status_code}: {resp.text}")

        except Exception as e:
            print(f"❌ [LIVE] Direct Kalshi Order Failed: {e}")
            add_ui_log(f"LIVE Order FAILED: {str(e)}", level="ERROR")
            return False

    async def get_active_positions(self):
        """
        Fetches current open positions from Kalshi to prevent duplicate trades.
        """
        try:
            key_id = settings.KALSHI_API_KEY
            private_key_path = settings.KALSHI_PRIVATE_KEY_PATH
            with open(private_key_path, 'rb') as f:
                private_key = serialization.load_pem_private_key(f.read(), password=None)

            path = "/trade-api/v2/portfolio/positions"
            url = f"https://api.elections.kalshi.com{path}"
            timestamp = str(int(time.time() * 1000))
            msg = timestamp + "GET" + path
            signature = private_key.sign(msg.encode('utf-8'), padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
            sig_b64 = base64.b64encode(signature).decode('utf-8')
            headers = {"KALSHI-ACCESS-KEY": key_id, "KALSHI-ACCESS-SIGNATURE": sig_b64, "KALSHI-ACCESS-TIMESTAMP": timestamp, "Content-Type": "application/json"}

            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    positions = data.get('market_positions', [])
                    found = [p['ticker'] for p in positions if p.get('position', 0) != 0]
                    return found
                return []
        except: return []

    async def manage_active_exits(self):
        """
        The Mathematical Exit Engine.
        Decides whether to 'Let it Ride' or 'Sell Early' to optimize expected value.
        """
        try:
            key_id = settings.KALSHI_API_KEY
            private_key_path = settings.KALSHI_PRIVATE_KEY_PATH
            with open(private_key_path, 'rb') as f:
                private_key = serialization.load_pem_private_key(f.read(), password=None)

            path = "/trade-api/v2/portfolio/positions"
            url = f"https://api.elections.kalshi.com{path}"
            timestamp = str(int(time.time() * 1000))
            msg = timestamp + "GET" + path
            signature = private_key.sign(msg.encode('utf-8'), padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
            sig_b64 = base64.b64encode(signature).decode('utf-8')
            headers = {"KALSHI-ACCESS-KEY": key_id, "KALSHI-ACCESS-SIGNATURE": sig_b64, "KALSHI-ACCESS-TIMESTAMP": timestamp, "Content-Type": "application/json"}

            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200: return
                positions = resp.json().get('market_positions', [])

                for pos in positions:
                    ticker = pos['ticker']
                    shares = pos['position']
                    if shares == 0: continue

                    # MINIMUM HOLDING TIME: 5 minutes (300 seconds)
                    # This prevents 'instant' reversals without significant news.
                    trade_time = self.executed_trades.get(f"TICKER_{ticker}", 0)
                    time_held = time.time() - trade_time

                    if time_held < 300:
                        continue

                    m_path = f"/trade-api/v2/markets/{ticker}"
                    m_url = f"https://api.elections.kalshi.com{m_path}"
                    m_msg = str(int(time.time() * 1000)) + "GET" + m_path
                    m_sig = private_key.sign(m_msg.encode('utf-8'), padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
                    m_headers = {"KALSHI-ACCESS-KEY": key_id, "KALSHI-ACCESS-SIGNATURE": base64.b64encode(m_sig).decode('utf-8'), "KALSHI-ACCESS-TIMESTAMP": m_msg[:13]}

                    m_resp = await client.get(m_url, headers=m_headers)
                    if m_resp.status_code != 200: continue
                    market_data = m_resp.json().get('market', {})
                    current_yes_bid = market_data.get('yes_bid', 0)

                    if current_yes_bid >= 90:
                        print(f"💰 Take Profit: {ticker} reached 90c. Selling.")
                        await self.execute_kalshi_exit(ticker, shares, "Take Profit")
                    elif current_yes_bid <= 10 and current_yes_bid > 0:
                        print(f"📉 Stop Loss: {ticker} dropped to 10c (Resilient). Cutting losses.")
                        await self.execute_kalshi_exit(ticker, shares, "Stop Loss")

        except Exception as e:
            print(f"⚠️ Exit Engine Error: {e}")

    async def execute_kalshi_exit(self, ticker, shares, reason):
        """
        Executes a real SELL order on Kalshi to close a position.
        """
        try:
            key_id = settings.KALSHI_API_KEY
            private_key_path = settings.KALSHI_PRIVATE_KEY_PATH
            with open(private_key_path, 'rb') as f:
                private_key = serialization.load_pem_private_key(f.read(), password=None)

            self.blacklist[ticker] = time.time() + (4 * 3600)
            print(f"🚫 Blacklisting {ticker} for 4 hours due to exit.")

            method = "POST"
            path = "/trade-api/v2/portfolio/orders"
            url = f"https://api.elections.kalshi.com{path}"
            payload = {"ticker": str(ticker), "action": "sell", "type": "market", "count": int(shares), "side": "yes", "no_price": 99}
            timestamp = str(int(time.time() * 1000))
            msg = timestamp + method + path
            signature = private_key.sign(msg.encode('utf-8'), padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
            sig_b64 = base64.b64encode(signature).decode('utf-8')
            headers = {"KALSHI-ACCESS-KEY": key_id, "KALSHI-ACCESS-SIGNATURE": sig_b64, "KALSHI-ACCESS-TIMESTAMP": timestamp, "Content-Type": "application/json"}

            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code in [200, 201]:
                    print(f"📉 [EXIT] Successfully sold {ticker}")
                    add_ui_log(f"EXIT EXECUTED: {ticker} ({shares} shares) - {reason}", level="SUCCESS")
                    await self._save_state()
                    return True
                else: raise Exception(f"HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            add_ui_log(f"EXIT FAILED: {ticker} - {str(e)}", level="ERROR")
            return False

    async def scan_and_execute(self):
        print("[*] AUTOPILOT: Engaged. Scanning markets...")
        await self._load_state()
        live_positions = await self.get_active_positions()
        for ticker in live_positions:
            self.executed_trades[f"TICKER_{ticker}"] = time.time()
            print(f"📊 Tracking existing position: {ticker}")

        while True:
            print(f"💓 AUTOPILOT Heartbeat: {time.strftime('%H:%M:%S')}")
            settings = settings_manager.get_settings()
            if not settings.trading_enabled:
                await asyncio.sleep(60)
                continue

            # Intel Bus: read cross-system signals before scoring new opportunities
            _heat_signal = await IntelReader.read_async("intel:portfolio_heat")
            _btc_bus = await IntelReader.read_async("intel:btc_sentiment")
            _spy_bus = await IntelReader.read_async("intel:spy_trend")

            # Hard stop: if total portfolio heat across both systems exceeds 80%, skip new trades
            if _heat_signal and _heat_signal.get("value", 0) > 0.8:
                print(f"🔥 AUTOPILOT: Portfolio heat at {_heat_signal['value']:.0%} — skipping new trades.")
                await asyncio.sleep(30)
                continue

            _bus_btc_sentiment = _btc_bus.get("value", None) if _btc_bus else None
            _bus_spy_trend = _spy_bus.get("value", "neutral").lower() if _spy_bus else "neutral"

            await self.manage_active_exits()

            btc_task = self.btc_engine.analyze_multiframe(asset="BTC", horizon="SCALP")
            fed_task = self.fed_engine.analyze_fed_market()
            social_task = self.social_engine.get_target_sentiment()
            weather_task = self.weather_engine.scan_full_us()
            musk_task = self.musk_engine.predict_today()

            btc, fed, social, weather, musk = await asyncio.gather(btc_task, fed_task, social_task, weather_task, musk_task)

            opportunities = []
            btc_score = int(btc['score'].split('/')[0])

            # Intel Bus: apply SPY macro filter — bearish macro reduces BTC confidence
            if _bus_spy_trend == "bearish" and _bus_btc_sentiment is not None and _bus_btc_sentiment < 0:
                btc_score = int(btc_score * 0.85)  # 15% penalty when both signals are bearish

            if btc_score >= settings.btc_threshold:
                opportunities.append({"module": "BTC", "signal": f"BTC {btc['sentiment']}", "score": btc_score, "odds": 1.95})
            if fed['macro_indicators']['yield_curve'] == "INVERTED":
                opportunities.append({"module": "POWELL", "signal": "Recession Hedge", "score": 85, "odds": 3.50})
            if social['score'] >= settings.social_threshold:
                opportunities.append({"module": "SOCIAL", "signal": "Social Alpha", "score": int(social['score'] * 100), "odds": 2.10})
            if weather.get("best_opportunity"):
                best_w = weather["best_opportunity"]
                w_score = int(best_w['edge'] * 100)
                social_weather_boost = 0
                for sig in social.get('signals', []):
                    if sig.get('category') == "Weather" and sig['verdict'] == "BULLISH":
                        social_weather_boost += 5
                final_w_score = w_score + social_weather_boost
                if final_w_score >= settings.global_min_score:
                    opportunities.append({"module": "WEATHER", "signal": f"{best_w['city']} {best_w['signal']}", "score": final_w_score, "odds": 3.0, "city": best_w['city']})
            if "HYPER-ACTIVE" in musk['prediction']['current_status']:
                opportunities.append({"module": "MUSK", "signal": "Elon Matrix", "score": 90, "odds": 4.50})

            if opportunities:
                self.allocator = CapitalAllocator()
                best_trade = sorted(opportunities, key=lambda x: x['score'], reverse=True)[0]

                # 1. MASTER GUARD: LIVE PORTFOLIO & BLACKLIST
                current_portfolio = await self.get_active_positions()

                # Check Blacklist
                if any(time.time() < expiry for t, expiry in self.blacklist.items()):
                    city = best_trade.get('city', '')
                    if any(city in t and time.time() < exp for t, exp in self.blacklist.items()):
                        print(f"🚫 {city} is on cooldown. Skipping.")
                        await asyncio.sleep(30)
                        continue

                already_held = False
                if best_trade['module'] == "WEATHER":
                    already_held = any(f"KXHIGH{best_trade['city']}" in p for p in current_portfolio)
                else:
                    already_held = any(best_trade['signal'] in p for p in current_portfolio)

                if already_held:
                    print(f"⚠️ Already holding {best_trade['signal']}. Skipping.")
                    await asyncio.sleep(30)
                    continue

                trade_id = f"{best_trade['signal']}_{time.strftime('%Y-%m-%d')}"
                if trade_id in self.executed_trades:
                    await asyncio.sleep(30)
                    continue

                if best_trade['score'] < settings.global_min_score:
                    await asyncio.sleep(30)
                    continue

                size = self.allocator.calculate_position_size(best_trade['score'], best_trade['odds'])
                if size > 0:
                    mode_str = "[PAPER]" if settings.paper_mode else "[LIVE]"
                    print(f"[*] AUTOPILOT {mode_str} Executing {best_trade['signal']} (${size})")
                    add_ui_log(f"{mode_str} Executing {best_trade['signal']} (${size})", level="TRADE")
                    if not settings.paper_mode:
                        success = await self.execute_kalshi_order(best_trade, size)
                        if success: self.executed_trades[trade_id] = time.time()
                    else: self.executed_trades[trade_id] = time.time()

            await asyncio.sleep(30)

    async def run(self):
        self.is_running = True
        await self.scan_and_execute()
