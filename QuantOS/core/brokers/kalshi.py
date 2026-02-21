"""
QuantOS™ v1.0.0 - Kalshi Suite Adapter
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import os
from core.broker_interface import BrokerInterface
from core.logger_config import get_logger

# We try to import kalshi_python but don't fail if not present
try:
    import kalshi_python
    from kalshi_python.api import portfolio_api
    from kalshi_python.configuration import Configuration
    from kalshi_python.api_client import ApiClient
except ImportError:
    kalshi_python = None

logger = get_logger("kalshi_adapter")

class KalshiAdapter(BrokerInterface):
    def __init__(self):
        self.name = "kalshi"
        # Since QuantOS and Kalshi projects are side-by-side on Desktop
        self.base_path = "/Users/claudiobarone/Desktop/Kalshi by Cemini"
        
        # Load from Kalshi's .env specifically
        from dotenv import dotenv_values
        kalshi_env = dotenv_values(os.path.join(self.base_path, ".env"))
        
        self.key_id = kalshi_env.get("KALSHI_API_KEY")
        self.private_key_path = os.path.join(self.base_path, "private_key.pem")
        self.api_client = None

    def authenticate(self):
        if not kalshi_python:
            logger.error("❌ kalshi-python SDK not installed.")
            return False
        
        if not self.key_id:
            return False
            
        if not os.path.exists(self.private_key_path):
            logger.error(f"❌ Kalshi credentials or private_key.pem missing at {self.private_key_path}.")
            return False

        try:
            config = Configuration()
            config.host = 'https://api.elections.kalshi.com/trade-api/v2'
            self.api_client = ApiClient(config)
            self.api_client.set_kalshi_auth(self.key_id, self.private_key_path)
            # Try a simple call to verify
            p_api = portfolio_api.PortfolioApi(self.api_client)
            p_api.get_balance()
            logger.info("✅ Kalshi Authenticated via Suite Bridge.")
            return True
        except Exception as e:
            logger.error(f"❌ Kalshi Auth Failed: {e}")
            return False

    def get_buying_power(self) -> float:
        if not self.api_client:
            return 0.0
        try:
            p_api = portfolio_api.PortfolioApi(self.api_client)
            res = p_api.get_balance()
            return float(res.balance / 100.0)
        except Exception as e:
            logger.error(f"Error fetching Kalshi balance: {e}")
            return 0.0

    def get_positions(self) -> list:
        if not self.api_client:
            return []
        try:
            p_api = portfolio_api.PortfolioApi(self.api_client)
            res = p_api.get_positions()
            positions = []
            for p in res.positions:
                positions.append({
                    "symbol": p.ticker,
                    "quantity": float(p.position),
                    "market_value": 0.0, # Kalshi doesn't provide easy market value in this call
                    "average_buy_price": 0.0
                })
            return positions
        except Exception as e:
            logger.error(f"Error fetching Kalshi positions: {e}")
            return []

    def get_latest_price(self, symbol: str) -> float:
        # Not implemented for Kalshi in this adapter yet
        return 0.0

    def submit_order(self, symbol: str, amount: float, side: str, order_type: str = "market", limit_price: float = None) -> dict:
        return {"error": "Order submission via Suite Bridge not yet implemented."}

    def submit_order_by_quantity(self, symbol: str, qty: float, side: str, order_type: str = "market", limit_price: float = None) -> dict:
        return {"error": "Quantity orders not implemented for Kalshi."}

    def cancel_all_orders(self):
        pass
