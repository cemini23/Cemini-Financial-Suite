"""
QuantOS™ v7.1.0 - Alpaca Adapter
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, TakeProfitRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
import os
from core.broker_interface import BrokerInterface
from core.logger_config import get_logger
from config.settings_manager import settings_manager

logger = get_logger("alpaca_adapter")

class AlpacaAdapter(BrokerInterface):
    def __init__(self):
        self.name = "alpaca"
        # Prioritize settings_manager (UI), then ENV
        self.api_key = settings_manager.get("alpaca_api_key") or os.getenv("APCA_API_KEY_ID") or os.getenv("ALPACA_API_KEY")
        self.secret_key = settings_manager.get("alpaca_secret_key") or os.getenv("APCA_API_SECRET_KEY") or os.getenv("ALPACA_SECRET_KEY")
        self.base_url = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
        
        # Determine paper mode from settings_manager or ENV
        env_setting = settings_manager.get("environment")
        if env_setting:
            self.paper = env_setting.upper() == "PAPER"
        else:
            self.paper = os.getenv("ENVIRONMENT", "PAPER").upper() == "PAPER"
            
        self.client = None
        self.data_client = None

    def authenticate(self):
        logger.info(f"🔐 Connecting to Alpaca (Key: {self.api_key[:4]}...{self.api_key[-4:] if self.api_key else ''})...")
        try:
            if not self.api_key or not self.secret_key:
                raise ValueError("Alpaca API Key or Secret Key is missing.")
                
            self.client = TradingClient(self.api_key, self.secret_key, paper=self.paper)
            self.data_client = StockHistoricalDataClient(self.api_key, self.secret_key)
            logger.info(f"✅ Alpaca Authenticated (Paper: {self.paper}).")
            return True
        except Exception as e:
            logger.error(f"❌ Alpaca Connection Failed: {e}")
            return False

    def get_buying_power(self) -> float:
        try:
            account = self.client.get_account()
            return float(account.buying_power)
        except Exception as e:
            logger.error(f"Error fetching buying power: {e}")
            return 0.0

    def get_positions(self) -> list:
        try:
            alpaca_positions = self.client.get_all_positions()
            positions = []
            for p in alpaca_positions:
                positions.append({
                    "symbol": p.symbol,
                    "quantity": float(p.qty),
                    "market_value": float(p.market_value),
                    "average_buy_price": float(p.avg_entry_price)
                })
            return positions
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []

    def get_latest_price(self, symbol: str) -> float:
        try:
            request_params = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            latest_quote = self.data_client.get_stock_latest_quote(request_params)
            return float(latest_quote[symbol].ask_price)
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return 0.0

    def submit_order(self, symbol: str, amount: float, side: str, order_type: str = "market", limit_price: float = None) -> dict:
        try:
            order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
            
            if order_type.lower() == "limit" and limit_price:
                # For limit orders, Alpaca requires quantity, not notional
                qty = float(amount / limit_price) if limit_price > 0 else 0
                if qty <= 0:
                    return {"error": "Quantity 0"}
                
                order_data = LimitOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    limit_price=limit_price,
                    side=order_side,
                    time_in_force=TimeInForce.GTC
                )
            else:
                # Alpaca supports notional (dollar amount) for market orders
                order_data = MarketOrderRequest(
                    symbol=symbol,
                    notional=amount,
                    side=order_side,
                    time_in_force=TimeInForce.GTC
                )
            
            order = self.client.submit_order(order_data=order_data)
            logger.info(f"📝 Alpaca {side.upper()} {order_type.upper()} order for {symbol} (${amount}) submitted.")
            return {"id": str(order.id), "status": str(order.status)}
        except Exception as e:
            logger.error(f"❌ Alpaca order failed: {e}")
            return {"error": str(e)}

    def submit_order_by_quantity(self, symbol: str, qty: float, side: str, order_type: str = "market", limit_price: float = None) -> dict:
        """Alpaca quantity-based implementation."""
        try:
            order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
            if order_type.lower() == "limit" and limit_price:
                req = LimitOrderRequest(symbol=symbol, qty=qty, side=order_side, time_in_force=TimeInForce.GTC, limit_price=limit_price)
            else:
                req = MarketOrderRequest(symbol=symbol, qty=qty, side=order_side, time_in_force=TimeInForce.GTC)
            
            res = self.client.submit_order(req)
            return {"id": str(res.id), "status": str(res.status)}
        except Exception as e:
            logger.error(f"❌ Alpaca order by quantity failed: {e}")
            return {"error": str(e)}

    def submit_bracket_order(self, symbol: str, amount: float, side: str, tp_price: float, sl_price: float) -> dict:
        """Alpaca bracket order implementation."""
        try:
            order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
            
            # Alpaca bracket orders require take_profit and stop_loss requests
            order_data = MarketOrderRequest(
                symbol=symbol,
                notional=amount,
                side=order_side,
                time_in_force=TimeInForce.GTC,
                order_class=OrderClass.BRACKET,
                take_profit=TakeProfitRequest(limit_price=tp_price),
                stop_loss=StopLossRequest(stop_price=sl_price)
            )
            
            order = self.client.submit_order(order_data=order_data)
            logger.info(f"🎯 Alpaca BRACKET {side.upper()} order for {symbol} (${amount}) submitted. TP: ${tp_price}, SL: ${sl_price}")
            return {"id": str(order.id), "status": str(order.status)}
        except Exception as e:
            logger.error(f"❌ Alpaca bracket order failed: {e}")
            return {"error": str(e)}

    def cancel_all_orders(self):
        try:
            self.client.cancel_orders()
            logger.info("✅ All Alpaca orders cancelled.")
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
