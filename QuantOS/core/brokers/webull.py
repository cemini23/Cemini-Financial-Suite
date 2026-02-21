"""
QuantOS™ v11.6.0 - Webull Adapter
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import os
from core.brokers.webull_client import WebullBroker
from core.broker_interface import BrokerInterface
from core.logger_config import get_logger
import yfinance as yf

logger = get_logger("webull_adapter")

class WebullAdapter(BrokerInterface):
    def __init__(self):
        self.name = "webull"
        self.client = WebullBroker()

    def authenticate(self):
        logger.info("🔐 Connecting to Webull...")
        self.client.login()
        # Note: webull library doesn't have a simple is_logged_in check after login
        # We assume success if no exception was raised in login()
        logger.info("✅ Webull Authentication attempt completed.")
        return True

    def get_buying_power(self) -> float:
        try:
            account = self.client.wb.get_account_id()
            # This is a simplification; webull-python response structures vary
            return 0.0 
        except Exception as e:
            logger.error(f"Error fetching Webull buying power: {e}")
            return 0.0

    def get_positions(self) -> list:
        if not self.client: return []
        try:
            positions_data = self.client.wb.get_positions()
            positions = []
            for p in positions_data:
                positions.append({
                    "symbol": p.get('ticker', {}).get('symbol'),
                    "quantity": float(p.get('position', 0)),
                    "market_value": float(p.get('marketValue', 0)),
                    "average_buy_price": float(p.get('cost', 0))
                })
            return positions
        except Exception as e:
            logger.error(f"Error fetching Webull positions: {e}")
            return []

    def get_latest_price(self, symbol: str) -> float:
        try:
            ticker = yf.Ticker(symbol)
            return float(ticker.fast_info['last_price'])
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return 0.0

    def submit_order(self, symbol: str, amount: float, side: str, order_type: str = "market", limit_price: float = None) -> dict:
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
            logger.error(f"❌ Webull order failed: {e}")
            return {"error": str(e)}

    def submit_order_by_quantity(self, symbol: str, qty: float, side: str, order_type: str = "market", limit_price: float = None) -> dict:
        return {"error": "Quantity orders not implemented for Webull."}

    def cancel_all_orders(self):
        logger.warning("⚠️ Cancel all orders not implemented for Webull adapter.")
        pass
