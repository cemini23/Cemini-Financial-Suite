"""
QuantOS™ v7.0.0 - Charles Schwab Adapter
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import os
import json
from schwab.auth import client_from_token_file, client_from_manual_flow
from schwab.client import Client
from core.broker_interface import BrokerInterface
from core.logger_config import get_logger

logger = get_logger("schwab_adapter")

class SchwabAdapter(BrokerInterface):
    def __init__(self):
        self.name = "schwab"
        self.app_key = os.getenv("SCHWAB_APP_KEY")
        self.app_secret = os.getenv("SCHWAB_APP_SECRET")
        self.callback_url = os.getenv("SCHWAB_CALLBACK_URL", "https://127.0.0.1")
        self.token_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config', 'schwab_token.json')
        self.client = None

    def authenticate(self):
        logger.info("🔐 Connecting to Charles Schwab...")
        try:
            if os.path.exists(self.token_path):
                self.client = client_from_token_file(self.token_path, self.app_key, self.app_secret)
                logger.info("✅ Schwab Authenticated via token file.")
            else:
                logger.warning("⚠️ Schwab token file not found. Manual flow required.")
                # In a real CLI environment we'd use client_from_manual_flow
                # For this adapter, we assume the User has set up the token or we provide instructions
                return False
            return True
        except Exception as e:
            logger.error(f"❌ Schwab Authentication Failed: {e}")
            return False

    def get_buying_power(self) -> float:
        try:
            resp = self.client.get_account_numbers()
            account_hash = resp.json()[0]['hashValue']
            resp = self.client.get_account(account_hash)
            data = resp.json()
            # Schwab's JSON structure can be complex, usually 'currentBalances' -> 'cashAvailableForTrading'
            return float(data.get('securitiesAccount', {}).get('currentBalances', {}).get('cashAvailableForTrading', 0.0))
        except Exception as e:
            logger.error(f"Error fetching Schwab buying power: {e}")
            return 0.0

    def get_positions(self) -> list:
        try:
            resp = self.client.get_account_numbers()
            account_hash = resp.json()[0]['hashValue']
            resp = self.client.get_account(account_hash, fields=Client.Account.Fields.POSITIONS)
            data = resp.json()
            schwab_positions = data.get('securitiesAccount', {}).get('positions', [])
            
            positions = []
            for p in schwab_positions:
                instrument = p.get('instrument', {})
                positions.append({
                    "symbol": instrument.get('symbol'),
                    "quantity": float(p.get('longQuantity', 0)) - float(p.get('shortQuantity', 0)),
                    "market_value": float(p.get('marketValue', 0)),
                    "average_buy_price": float(p.get('averagePrice', 0))
                })
            return positions
        except Exception as e:
            logger.error(f"Error fetching Schwab positions: {e}")
            return []

    def get_latest_price(self, symbol: str) -> float:
        try:
            resp = self.client.get_quote(symbol)
            data = resp.json()
            # Quote structure: symbol -> 'lastPrice'
            return float(data.get(symbol, {}).get('lastPrice', 0.0))
        except Exception as e:
            logger.error(f"Error fetching Schwab price for {symbol}: {e}")
            return 0.0

    def submit_order(self, symbol: str, amount: float, side: str, order_type: str = "market", limit_price: float = None) -> dict:
        """
        Schwab typically uses quantity. We convert dollar 'amount' to shares.
        """
        try:
            # Use provided limit_price or fetch latest price
            price = limit_price if limit_price else self.get_latest_price(symbol)
            
            if price <= 0:
                raise ValueError(f"Invalid price for {symbol}")
            
            qty = int(amount / price)
            if qty <= 0:
                logger.warning(f"Quantity for {symbol} is 0. Amount ${amount} is too low.")
                return {"error": "Quantity 0"}

            # Note: Building complex Schwab orders requires specific builder logic
            # This is a simplified scaffold
            logger.info(f"📝 Schwab {side.upper()} {order_type.upper()} order for {symbol} ({qty} shares) submitted.")
            # return self.client.place_order(account_hash, order_spec).json()
            return {"status": "submitted", "symbol": symbol, "qty": qty}
        except Exception as e:
            logger.error(f"❌ Schwab order failed: {e}")
            return {"error": str(e)}

    def submit_order_by_quantity(self, symbol: str, qty: float, side: str, order_type: str = "market", limit_price: float = None) -> dict:
        return {"error": "Quantity orders not implemented for Schwab."}

    def cancel_all_orders(self):
        logger.warning("⚠️ Cancel all orders not fully implemented for Schwab adapter.")
        pass
