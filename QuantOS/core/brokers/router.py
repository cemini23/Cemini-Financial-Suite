"""
QuantOS™ v12.0.0 - Intelligent Order Router
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import os
from datetime import datetime
import pytz
from core.broker_interface import BrokerInterface
from core.brokers.factory import get_broker_by_name
from core.logger_config import get_logger
from config.settings_manager import settings_manager

logger = get_logger("broker_router")

class GlobalRouter(BrokerInterface):
    def __init__(self):
        self.brokers = {}
        # Load from settings manager
        self.enabled = settings_manager.get("global_router_enabled")
        self.primary_broker_name = settings_manager.get("primary_broker") or os.getenv("ACTIVE_BROKER", "ibkr").lower()
        
        logger.info(f"🚦 Global Router Initialized. Enabled: {self.enabled} | Primary: {self.primary_broker_name}")

    def _get_best_broker_name(self, symbol=None, side=None):
        """
        Logic to pick the best broker:
        1. If disabled, always use primary.
        2. Pre-Market (4:00 AM - 9:30 AM EST): Webull
        3. Regular Hours (9:30 AM - 4:00 PM EST): Alpaca or IBKR
        4. After-Hours (4:00 PM - 8:00 PM EST): Webull
        5. Crypto / Weekend: SoFi or Alpaca
        """
        if not self.enabled:
            return self.primary_broker_name

        tz = pytz.timezone('US/Eastern')
        now = datetime.now(tz)
        is_weekend = now.weekday() >= 5
        
        # Current time in HHMM format
        time_int = int(now.strftime("%H%M"))

        # Crypto Logic
        if "BTC" in (symbol or "") or "ETH" in (symbol or ""):
            return "sofi"

        if is_weekend:
            return self.primary_broker_name

        # Extended Hours Check
        if 400 <= time_int < 930:
            return "webull" # Pre-market
        elif 1600 <= time_int < 2000:
            return "webull" # After-hours
        elif 930 <= time_int < 1600:
            # Regular hours: Favor Alpaca if it's primary, otherwise IBKR
            return "alpaca" if self.primary_broker_name == "alpaca" else "ibkr"
        
        return self.primary_broker_name

    def _get_broker(self, name):
        if name not in self.brokers:
            logger.info(f"🔌 Router: Initializing {name} adapter...")
            try:
                self.brokers[name] = get_broker_by_name(name)
                # Only authenticate once during initialization
                self.brokers[name].authenticate()
            except Exception as e:
                logger.error(f"❌ Router failed to init {name}: {e}")
                # Fallback to primary if initialization fails and we are not already trying to init primary
                if name != self.primary_broker_name:
                    return self._get_broker(self.primary_broker_name)
                raise e
        return self.brokers[name]

    def authenticate(self):
        # We authenticate the primary broker upfront
        return self._get_broker(self.primary_broker_name).authenticate()

    def get_buying_power(self) -> float:
        # Buying power depends on which broker we are looking at. 
        # For router, we return the primary broker's buying power.
        return self._get_broker(self.primary_broker_name).get_buying_power()

    def get_positions(self) -> list:
        # Aggregates positions from all initialized brokers
        all_positions = []
        # If disabled, only show primary positions
        if not self.enabled:
            return self._get_broker(self.primary_broker_name).get_positions()

        # If enabled, show from all brokers we've talked to
        for name in list(self.brokers.keys()):
            try:
                all_positions.extend(self.brokers[name].get_positions())
            except Exception as e:
                logger.error(f"Router error fetching positions from {name}: {e}")
        return all_positions

    def get_latest_price(self, symbol: str) -> float:
        name = self._get_best_broker_name(symbol)
        return self._get_broker(name).get_latest_price(symbol)

    def submit_order(self, symbol: str, amount: float, side: str, order_type: str = "market", limit_price: float = None) -> dict:
        name = self._get_best_broker_name(symbol, side)
        logger.info(f"🎯 Router: Routing {side.upper()} {symbol} order to {name.upper()}")
        return self._get_broker(name).submit_order(symbol, amount, side, order_type, limit_price)

    def cancel_all_orders(self):
        for name in self.brokers:
            self.brokers[name].cancel_all_orders()

    def check_health(self):
        """Pings all active brokers to verify connectivity."""
        status = {}
        
        # 1. Check Alpaca
        if 'alpaca' in self.brokers or self.primary_broker_name == 'alpaca':
            try:
                b = self._get_broker('alpaca')
                # Try to fetch buying power or similar lightweight call
                b.get_buying_power()
                status['alpaca'] = True
            except Exception:
                status['alpaca'] = False

        # 2. Check Robinhood
        if 'robinhood' in self.brokers or self.primary_broker_name == 'robinhood':
            try:
                b = self._get_broker('robinhood')
                b.get_buying_power()
                status['robinhood'] = True
            except Exception:
                status['robinhood'] = False

        # 3. Check IBKR
        if 'ibkr' in self.brokers or self.primary_broker_name == 'ibkr':
            try:
                b = self._get_broker('ibkr')
                # For IBKR, we check if the underlying connection is still alive
                status['ibkr'] = b.ib.isConnected() if hasattr(b, 'ib') else False
            except:
                status['ibkr'] = False
                
        return status
