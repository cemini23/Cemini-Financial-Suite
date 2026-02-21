"""
QuantOS™ v11.5.0 - SoFi Adapter
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import os
import robin_stocks.sofi as sofi
from core.brokers.sofi_client import SoFiBroker
from core.broker_interface import BrokerInterface
from core.logger_config import get_logger
import yfinance as yf

logger = get_logger("sofi_adapter")

class SofiAdapter(BrokerInterface):
    def __init__(self):
        self.name = "sofi"
        self.username = os.getenv("SOFI_USERNAME")
        self.password = os.getenv("SOFI_PASSWORD")
        self.client = SoFiBroker(self.username, self.password)

    def authenticate(self):
        logger.info("🔐 Connecting to SoFi...")
        self.client.login()
        if self.client.is_logged_in:
            logger.info("✅ SoFi Authenticated.")
            return True
        return False

    def get_buying_power(self) -> float:
        return self.client.get_balance()

    def get_positions(self) -> list:
        """
        SoFi position retrieval is limited in robin_stocks.
        Returning empty list for now.
        """
        if not self.client.is_logged_in: return []
        return []

    def get_latest_price(self, symbol: str) -> float:
        """Fetches latest price using yfinance as fallback."""
        try:
            ticker = yf.Ticker(symbol)
            return float(ticker.fast_info['last_price'])
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return 0.0

    def submit_order(self, symbol: str, amount: float, side: str, order_type: str = "market", limit_price: float = None) -> dict:
        """
        SoFi execution via SofiAdapter.
        Converts dollar amount to quantity based on current price.
        """
        if not self.client.is_logged_in:
            return {"error": "Not authenticated"}

        try:
            price = limit_price if limit_price else self.get_latest_price(symbol)
            if price <= 0:
                return {"error": f"Invalid price for {symbol}"}

            qty = int(amount / price)
            if qty <= 0:
                return {"error": "Quantity 0"}

            order = self.client.execute_trade(symbol, qty, side)
            return {"status": "submitted", "order": order}
        except Exception as e:
            logger.error(f"❌ SoFi order failed: {e}")
            return {"error": str(e)}

    def submit_order_by_quantity(self, symbol: str, qty: float, side: str, order_type: str = "market", limit_price: float = None) -> dict:
        return {"error": "Quantity orders not implemented for SoFi."}

    def cancel_all_orders(self):
        logger.warning("⚠️ Cancel all orders not implemented for SoFi adapter.")
        pass
