"""
# Role: Integration Engineer
# Project: QuantOS v13.6 (Robinhood Session Auth)
# Objective: Remove TOTP logic and use session caching for headless Robinhood authentication.
"""
import os
import time
import robin_stocks.robinhood as r
from core.broker_interface import BrokerInterface
from core.logger_config import get_logger

logger = get_logger("robinhood_adapter")

class RobinhoodAdapter(BrokerInterface):
    def __init__(self):
        self.name = "robinhood"
        self.username = os.getenv("RH_USERNAME") or os.getenv("ROBINHOOD_USERNAME")
        self.password = os.getenv("RH_PASSWORD") or os.getenv("ROBINHOOD_PASSWORD")
        self.is_logged_in = False
        self.consecutive_errors = 0
        self.MAX_ERRORS = 3

    def authenticate(self):
        """Logs in using the cached session token OR direct credentials if session is missing."""
        logger.info("🔐 Connecting to Robinhood...")
        try:
            # We explicitly try to log in with credentials and store the session
            # If a valid session exists in memory/pickle, robin_stocks will use it
            # Otherwise it will use the credentials provided
            r.login(
                self.username, 
                self.password, 
                store_session=True
            )
            self.is_logged_in = True
            self.consecutive_errors = 0
            logger.info("✅ Robinhood: Authenticated successfully.")
            return True
        except Exception as e:
            logger.error(f"❌ Robinhood Login Failed: {e}. Ensure you have authorized your session via 'scripts/manual_login.py'.")
            self.is_logged_in = False
            return False

    def get_buying_power(self) -> float:
        if not self.is_logged_in:
            return 0.0
        try:
            profile = r.profiles.load_account_profile()
            return float(profile.get('portfolio_cash', 0)) if profile else 0.0
        except Exception as e:
            logger.error(f"Error fetching buying power: {e}")
            return 0.0

    def get_positions(self) -> list:
        if not self.is_logged_in:
            return []
        try:
            holdings = r.build_holdings()
            positions = []
            for ticker, data in (holdings or {}).items():
                positions.append({
                    "symbol": ticker,
                    "quantity": float(data.get('quantity', 0)),
                    "market_value": float(data.get('equity', 0)),
                    "average_buy_price": float(data.get('average_buy_price', 0))
                })
            return positions
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []

    def get_latest_price(self, symbol: str) -> float:
        """Fetches data but trips the circuit breaker if it fails too many times."""
        if not self.is_logged_in or self.consecutive_errors >= self.MAX_ERRORS:
            return 0.0

        try:
            time.sleep(0.5) 
            data = r.get_latest_price(symbol)
            self.consecutive_errors = 0 
            return float(data[0]) if data and data[0] else 0.0
            
        except Exception as e:
            self.consecutive_errors += 1
            logger.warning(f"⚠️ Robinhood Scan Error ({self.consecutive_errors}/{self.MAX_ERRORS}): {symbol}")
            
            if self.consecutive_errors >= self.MAX_ERRORS:
                logger.error("🚨 CIRCUIT BREAKER TRIPPED: Robinhood API unresponsive.")
            return 0.0

    def submit_order(self, symbol: str, amount: float, side: str, order_type: str = "market", limit_price: float = None) -> dict:
        if not self.is_logged_in:
            return {"error": "Not logged in"}
        try:
            if side.lower() == "buy":
                res = r.orders.order_buy_fractional_by_price(symbol, amount)
            else:
                res = r.orders.order_sell_fractional_by_price(symbol, amount)
            logger.info(f"📝 Robinhood {side.upper()} order for {symbol} (${amount}) submitted.")
            return res
        except Exception as e:
            logger.error(f"❌ Robinhood order failed: {e}")
            return {"error": str(e)}

    def submit_order_by_quantity(self, symbol: str, qty: float, side: str, order_type: str = "market", limit_price: float = None) -> dict:
        if not self.is_logged_in:
            return {"error": "Not logged in"}
        try:
            if side.lower() == "buy":
                res = r.orders.order_buy_market(symbol, qty)
            else:
                res = r.orders.order_sell_market(symbol, qty)
            logger.info(f"📝 Robinhood {side.upper()} order for {symbol} ({qty} shares) submitted.")
            return res
        except Exception as e:
            logger.error(f"❌ Robinhood order by quantity failed: {e}")
            return {"error": str(e)}

    def cancel_all_orders(self):
        if not self.is_logged_in:
            return
        try:
            r.orders.cancel_all_stock_orders()
            logger.info("✅ All Robinhood stock orders cancelled.")
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
