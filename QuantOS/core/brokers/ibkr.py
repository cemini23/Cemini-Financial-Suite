"""
QuantOS™ v8.7.0 - Interactive Brokers Adapter
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
from ib_insync import IB, Stock, MarketOrder, LimitOrder, AccountValue
import os
import nest_asyncio
from core.broker_interface import BrokerInterface
from core.logger_config import get_logger

# Allow nested event loops for ib_insync in some environments
nest_asyncio.apply()

logger = get_logger("ibkr_adapter")

class IBKRAdapter(BrokerInterface):
    def __init__(self):
        self.name = "ibkr"
        self.ib = IB()
        self.host = os.getenv("IBKR_HOST", "127.0.0.1")
        self.port = int(os.getenv("IBKR_PORT", 7497))
        self.client_id = int(os.getenv("IBKR_CLIENT_ID", 1))

    def authenticate(self):
        logger.info(f"📡 Attempting to connect to IBKR at {self.host}:{self.port} (ClientID: {self.client_id})...")
        try:
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            logger.info("✅ Connected to IBKR!")
            return True
        except Exception as e:
            logger.error(f"❌ ERROR: Could not find IBKR TWS or Gateway.")
            logger.info("💡 FIX: Ensure Trader Workstation is open and 'ActiveX/Socket Clients' is enabled in Settings.")
            logger.error(f"Technical Error: {e}")
            return False

    def get_buying_power(self) -> float:
        try:
            values = self.ib.accountSummary()
            for v in values:
                if v.tag == 'NetLiquidation':
                    return float(v.value)
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching buying power: {e}")
            return 0.0

    def get_positions(self) -> list:
        try:
            ib_positions = self.ib.portfolio()
            positions = []
            for p in ib_positions:
                positions.append({
                    "symbol": p.contract.symbol,
                    "quantity": float(p.position),
                    "market_value": float(p.marketValue),
                    "average_buy_price": float(p.averageCost)
                })
            return positions
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []

    def get_latest_price(self, symbol: str) -> float:
        try:
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            ticker = self.ib.reqMktData(contract, '', False, False)
            self.ib.sleep(1) # Wait for data to arrive
            price = ticker.last if ticker.last == ticker.last else ticker.close # Handle NaN
            return float(price) if price else 0.0
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return 0.0

    def submit_order(self, symbol: str, amount: float, side: str, order_type: str = "market", limit_price: float = None) -> dict:
        """
        Submits an order. For IBKR, we convert the dollar 'amount' to quantity if possible, 
        or use specific IBKR order types.
        """
        try:
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # Determine quantity based on price if 'amount' is in USD
            price = self.get_latest_price(symbol)
            if price <= 0:
                raise ValueError(f"Invalid price for {symbol}")
            
            # Use float for quantity to support fractional trading (if account allows)
            qty = round(amount / price, 4)
            if qty <= 0:
                logger.warning(f"Quantity for {symbol} is too low. Amount ${amount} is insufficient.")
                return {"error": "Amount too low"}

            if order_type.lower() == "market":
                order = MarketOrder(side.upper(), qty)
            else:
                # Use provided limit_price or fallback to current price
                l_price = limit_price if limit_price else price
                order = LimitOrder(side.upper(), qty, l_price)
            
            trade = self.ib.placeOrder(contract, order)
            logger.info(f"📝 IBKR {side.upper()} {order_type.upper()} order for {symbol} ({qty} shares) submitted.")
            return {"order_id": trade.order.orderId, "status": trade.orderStatus.status}
        except Exception as e:
            logger.error(f"❌ IBKR order failed: {e}")
            return {"error": str(e)}

    def submit_order_by_quantity(self, symbol: str, qty: float, side: str, order_type: str = "market", limit_price: float = None) -> dict:
        try:
            from ib_insync import Stock, MarketOrder, LimitOrder
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            if order_type.lower() == "market":
                order = MarketOrder(side.upper(), qty)
            else:
                l_price = limit_price if limit_price else self.get_latest_price(symbol)
                order = LimitOrder(side.upper(), qty, l_price)
            
            trade = self.ib.placeOrder(contract, order)
            return {"order_id": trade.order.orderId, "status": trade.orderStatus.status}
        except Exception as e:
            return {"error": str(e)}

    def cancel_all_orders(self):
        try:
            self.ib.reqGlobalCancel()
            logger.info("✅ All IBKR orders cancelled.")
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")

    def __del__(self):
        if self.ib.isConnected():
            self.ib.disconnect()
