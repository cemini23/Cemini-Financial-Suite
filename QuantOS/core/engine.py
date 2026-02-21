"""
QuantOS™ v13.0.8 - Trading Engine Core
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import asyncio
import os
import threading
import pandas as pd
import redis.asyncio as aioredis
from datetime import datetime
from dotenv import load_dotenv

# Core Imports
from core import brain
from core import ledger
from core import tickers
from core.execution import ExecutionEngine
from core.logger_config import get_logger
from core.risk_manager import RiskManager
from core.brokers.factory import get_broker
from core.data.streamer import MarketStream
from core.collector import DataCollector
from core.harvester import harvester
from core.bq_signals import cloud_signals
from core.sentiment.x_oracle import x_oracle
from core.strategy_matrix import MasterStrategyMatrix
from core.async_scanner import AsyncScanner
from core.money_manager import money_manager
from strategies.analysis import calculate_confidence_score
from config.settings_manager import settings_manager

logger = get_logger("engine")

class TradingEngine:
    def __init__(self):
        self.version = "13.1.0"
        self.collector = None
        self.broker = None
        self.is_running = False
        self.history_cache = {}
        self.last_history_sync = 0
        self.report_sent_today = False
        # fresh_start is triggered via Redis key 'quantos:fresh_start_requested'
        # Run: python QuantOS/scripts/trigger_fresh_start.py to request a liquidation

        # Adaptive Risk Matrix: (min_volume_multiplier, min_drop_percentage)
        self.thresholds = {
            "indices": (2.5, -0.75),       # SPY dropping 0.75% is a flash crash
            "mega_cap": (3.0, -1.5),       # AAPL dropping 1.5%
            "high_beta": (3.0, -2.5),      # TSLA dropping 2.5%
            "crypto_proxies": (3.5, -3.0), # COIN/MSTR are wild
            "crypto_native": (3.0, -2.0)   # BTC dropping 2%
        }
        self.default_threshold = (3.0, -2.0)
        self.symbol_category_map = self._load_category_map()

    def _load_category_map(self):
        """Creates a lookup dictionary mapping symbols to categories from tickers.json."""
        from core.tickers import get_categories
        cats = get_categories()
        mapping = {}
        for category, symbols in cats.items():
            for sym in symbols:
                mapping[sym] = category
        return mapping

    def liquidate_all_positions(self):
        """Emergency/Fresh Start: Sells all current holdings."""
        logger.info("🚨 FRESH START: Liquidating all active positions...")
        try:
            # Check if broker is authenticated/available
            try:
                positions = self.broker.get_positions()
            except Exception as e:
                logger.error(f"⚠️ Could not fetch positions for liquidation: {e}")
                return

            if not positions:
                logger.info("✅ No positions found to liquidate.")
                return

            print(f"🚨 FRESH START: Identified {len(positions)} positions to close.")
            import time
            for p in positions:
                symbol = p['symbol']
                qty = p['quantity']
                if qty > 0:
                    try:
                        print(f"📉 LIQUIDATING: {symbol} ({qty} shares)")
                        self.broker.submit_order_by_quantity(symbol, qty, "sell", order_type="market")
                        time.sleep(5.0) # Increased to 5s for the final stubborn few
                    except Exception as e:
                        logger.error(f"❌ Failed to liquidate {symbol}: {e}")

            logger.info("✅ Liquidation cycle completed.")
        except Exception as e:
            logger.error(f"❌ Liquidation failed: {e}")

    def initialize(self):
        """Pre-flight checks and initialization."""
        self.collector = DataCollector()
        load_dotenv()
        self.broker = get_broker()
        try:
            # Single auth attempt at startup
            success = self.broker.authenticate()
            if not success:
                logger.warning(f"⚠️ Initial authentication failed. Entering monitoring mode.")
            else:
                logger.info("✅ Broker session established.")
        except Exception as e:
            logger.error(f"❌ Broker init error: {e}")

        ledger.init_ledger()
        self.execution_engine = ExecutionEngine(self.broker)
        self.strategy_matrix = MasterStrategyMatrix(self, cloud_signals, x_oracle)
        logger.info(f"🚀 Trading Engine v{self.version} Initialized")

    def is_market_open(self):
        """Checks if the US market is currently open."""
        import pytz
        tz = pytz.timezone('US/Eastern')
        now = datetime.now(tz)

        # Weekday check (0=Monday, 6=Sunday)
        if now.weekday() > 4:
            return False

        # Time check (9:30 AM - 4:00 PM)
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

        return market_open <= now <= market_close

    async def _sync_historical_data(self, watchlist):
        """Fetches daily historicals for the entire watchlist in optimized chunks."""
        import time
        import robin_stocks.robinhood as rh

        if time.time() - self.last_history_sync < 1800 and self.history_cache:
            return

        logger.info(f"📊 SYNC: Refreshing historical daily data for {len(watchlist)} assets...")
        try:
            new_cache = {}
            # Chunking into batches of 50 to avoid 400 Bad Request (URL too long)
            chunk_size = 50
            for i in range(0, len(watchlist), chunk_size):
                chunk = watchlist[i:i + chunk_size]
                batch_history = rh.stocks.get_stock_historicals(chunk, interval='day', span='year')

                if batch_history:
                    for entry in batch_history:
                        if entry and 'symbol' in entry:
                            ticker = entry['symbol']
                            if ticker not in new_cache: new_cache[ticker] = []
                            new_cache[ticker].append(entry)

                # Small sleep between chunks to be polite to the API
                await asyncio.sleep(0.5)

            if new_cache:
                self.history_cache = new_cache
                self.last_history_sync = time.time()
                logger.info(f"✅ SYNC Complete. Cached {len(new_cache)} assets.")
            else:
                logger.warning("⚠️ SYNC: No data returned from Robinhood.")

        except Exception as e:
            logger.warning(f"⚠️ History Sync Failed: {e}")

    async def trade_loop(self):
        """The optimized trading loop using Batch Sync + Async Scanning."""
        risk_manager = RiskManager(self.broker)
        execution_engine = ExecutionEngine(self.broker)

        while self.is_running:
            settings_manager.settings = settings_manager.load_settings()
            if settings_manager.get("bot_paused"):
                await asyncio.sleep(5)
                continue

            watchlist = settings_manager.get("active_tickers") or tickers.WATCHLIST
            is_open = self.is_market_open()

            # --- FRESH START PROTOCOL ---
            # Triggered only when 'quantos:fresh_start_requested' Redis key is 'true'.
            # Use QuantOS/scripts/trigger_fresh_start.py to request a liquidation.
            if is_open:
                try:
                    redis_host = os.getenv('REDIS_HOST', 'redis')
                    _r = aioredis.from_url(f"redis://{redis_host}:6379", decode_responses=True)
                    try:
                        fresh_requested = await _r.get('quantos:fresh_start_requested')
                        if fresh_requested and fresh_requested.lower() == 'true':
                            self.liquidate_all_positions()
                            await _r.set('quantos:fresh_start_requested', 'false')
                            logger.info("✨ Clean Slate Achieved. Resuming normal operations.")
                    finally:
                        await _r.aclose()
                except Exception as _e:
                    logger.warning(f"⚠️ Fresh start Redis check failed: {_e}")

            # 1. Batch Sync Daily Data (Only if open, every 30m)
            if is_open:
                await self._sync_historical_data(watchlist)

            # 2. THE SPEED BOOST: Run the async scanner for real-time prices
            scanner = AsyncScanner(watchlist)
            market_data = await scanner.scan_market()

            # 3. Process results using cached history
            valid_tickers = 0
            for ticker, price in market_data.items():
                try:
                    if price <= 0: continue
                    valid_tickers += 1

                    # Update brain/harvester (Always record if we have a price from scanner)
                    brain.realtime_brain.update_price(ticker, price)
                    harvester.record_tick(ticker, price, 0)

                    if not is_open: continue

                    # Get cached history
                    history = self.history_cache.get(ticker)
                    if not history: continue

                    df = pd.DataFrame(history)
                    df['Close'] = pd.to_numeric(df['close_price'], errors='coerce')
                    rsi_rt = brain.realtime_brain.calculate_rsi(ticker)

                    # Core Analysis
                    score, indicators = calculate_confidence_score(ticker, df, rsi_rt, is_simulation=False)

                    # Execution
                    if not ledger.has_position(ticker):
                        await execution_engine.execute_buy(ticker, score, indicators, settings_manager.settings)
                        await asyncio.sleep(1.0) # Rate limit safety

                except Exception as e:
                    logger.error(f"❌ Error processing {ticker}: {e}")

            # --- 4. CLOUD SIGNAL PROCESSING (CONFLUENCE) ---
            if is_open:
                # The MasterStrategyMatrix looks for confluence between BigQuery anomalies and FinBERT sentiment
                await self.strategy_matrix.evaluate_market()

            # Sunset Report Check
            await self._check_sunset_report(is_open)

            await asyncio.sleep(10) # 10s delay with real-time stream active

    async def _check_sunset_report(self, is_open):
        """Triggers the sunset report once daily at 16:15 EST."""
        import pytz
        tz = pytz.timezone('US/Eastern')
        now = datetime.now(tz)
        today_str = now.strftime("%Y-%m-%d")

        # Reset flag on new day
        if hasattr(self, '_last_report_day') and self._last_report_day != today_str:
            self.report_sent_today = False

        self._last_report_day = today_str

        # Check if it is 16:15 or later and report hasn't been sent
        if now.hour == 16 and now.minute >= 15 and not self.report_sent_today:
            logger.info("🌅 16:15 EST: Preparing Sunset Report...")
            try:
                from strategies import analytics
                from core.reporting import SunsetReporter

                stats = analytics.get_performance_stats()
                # Check for any trade activity today (Buys or Sells)
                if stats.get("today_activity", 0) == 0:
                    logger.info("ℹ️ No trade activity today. Skipping report.")
                    self.report_sent_today = True
                    return

                broker_pnl = stats.get("broker_daily_pnl", {}).get(today_str, {"Total": 0.0})
                recipients = settings_manager.get("report_recipients")
                reporter = SunsetReporter(recipients)
                reporter.send_report(broker_pnl)
                self.report_sent_today = True
            except Exception as e:
                logger.error(f"❌ Failed to send Sunset Report: {e}")

    async def start_async(self):
        self.is_running = True
        self.initialize()

        # Start trade loop
        tasks = [self.trade_loop()]

        # Check for Alpaca or IBKR connectivity
        alpaca_key = os.getenv("ALPACA_API_KEY")
        alpaca_active = alpaca_key and "your_" not in alpaca_key.lower()
        ibkr_active = self.broker and hasattr(self.broker, 'ib') and self.broker.ib.isConnected()

        print(f"📡 Connectivity Check: Alpaca={alpaca_active}, IBKR={ibkr_active}")

        if alpaca_active or ibkr_active:
            print("📡 Initializing MarketStream...")
            market_stream = MarketStream(tickers.WATCHLIST[:100], self.on_market_update, broker=self.broker)
            tasks.append(market_stream.start())
            logger.info(f"📡 MarketStream added to tasks (Alpaca: {alpaca_active}, IBKR: {ibkr_active})")
        else:
            logger.info("📡 MarketStream skipped (No active credentials). Using Scanner for data.")

        print(f"📡 Starting {len(tasks)} background tasks...")
        await asyncio.gather(*tasks)

    def run(self):
        """Synchronous wrapper for threading."""
        asyncio.run(self.start_async())

    def execute_cross_broker_trade(self, symbol, qty=None, side="buy"):
        """
        Specialized execution for external signals (TradingView, Kalshi).
        This bypasses the scanner and executes immediately on the active broker.
        """
        async def _execute():
            try:
                if not self.broker:
                    self.initialize()

                execution_engine = ExecutionEngine(self.broker)

                # If qty is provided, we use it directly.
                # Otherwise, we ask money_manager for a recommended size.
                if qty:
                    price = self.broker.get_latest_price(symbol)
                    amount = float(qty) * price
                else:
                    buying_power = self.broker.get_buying_power()
                    amount = money_manager.calculate_position_size(buying_power, 100) # Use max score for signals

                if amount <= 0:
                    logger.warning(f"⚠️ Signal execution failed: Calculated amount is $0 for {symbol}")
                    return

                logger.info(f"📡 SIGNAL RECEIVED: {side.upper()} {symbol} (Signal Strength: 100)")
                await execution_engine.execute_smart_order(symbol, side, amount, settings_manager.settings)

            except Exception as e:
                logger.error(f"❌ Cross-broker trade failed: {e}")

        # Run the async execution in a new thread/loop if called from sync context
        thread = threading.Thread(target=lambda: asyncio.run(_execute()), daemon=True)
        thread.start()

    async def execute_dip_buy(self, symbol, current_price, category, execution_engine):
        """Executes a bracket order for automated risk management."""
        logger.info(f"🚀 ENGINE: Firing Mean-Reversion BRACKET BUY for {symbol} at ${current_price}...")

        # 1. Define category-specific exit rules (Take Profit %, Stop Loss %)
        # Formatting these for the adaptive risk strategy
        exit_rules = {
            "indices": (1.0, -0.5),
            "mega_cap": (2.0, -1.0),
            "high_beta": (4.0, -2.0),
            "crypto_native": (3.0, -1.5)
        }

        tp_pct, sl_pct = exit_rules.get(category, (2.0, -1.0))

        # 2. Calculate absolute price targets
        take_profit_price = round(current_price * (1 + (tp_pct / 100.0)), 2)
        stop_loss_price = round(current_price * (1 + (sl_pct / 100.0)), 2)

        logger.info(f"🎯 MATRIX ARMED [{category.upper()}]: Target ${take_profit_price} | Stop ${stop_loss_price}")

        # 3. Calculate Position Size
        buying_power = self.broker.get_buying_power()
        # High confidence for these tactical setups
        buy_amount = money_manager.calculate_position_size(buying_power, 90)

        if buy_amount <= 0:
            logger.info(f"💰 Money Manager suggested $0 for {symbol}. Skipping.")
            return

        # 4. Submit Bracket Order
        await execution_engine.submit_bracket_order(
            symbol,
            buy_amount,
            "buy",
            take_profit_price,
            stop_loss_price,
            settings_manager.settings
        )

    async def on_market_update(self, symbol, data_type, data):
        if data_type == "trade":
            price = data.get("price")
            volume = data.get("volume", 0)
            if price:
                brain.realtime_brain.update_price(symbol, price)
                harvester.record_tick(symbol, price, volume)

                # TRIGGER ANALYSIS ON REAL-TIME DATA
                try:
                    # Get cached history
                    history = self.history_cache.get(symbol)
                    if history and self.is_market_open():
                        df = pd.DataFrame(history)
                        df['Close'] = pd.to_numeric(df['close_price'], errors='coerce')
                        rsi_rt = brain.realtime_brain.calculate_rsi(symbol)

                        # Core Analysis
                        from strategies.analysis import calculate_confidence_score
                        score, indicators = calculate_confidence_score(symbol, df, rsi_rt, is_simulation=False)

                        # Execution
                        from core.execution import ExecutionEngine
                        execution_engine = ExecutionEngine(self.broker)
                        if not ledger.has_position(symbol):
                            await execution_engine.execute_buy(symbol, score, indicators, settings_manager.settings)
                except Exception as e:
                    logger.error(f"Error in on_market_update analysis for {symbol}: {e}")

        elif data_type == "quote":
            # For now, we log quotes or use them for spread monitoring
            bid = data.get("bid")
            ask = data.get("ask")
            if bid and ask:
                # Potential: Update spread metrics or order book models here
                pass
