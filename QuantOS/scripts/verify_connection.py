import os
import sys
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.brokers.factory import get_broker
from core.logger_config import get_logger

logger = get_logger("verify_connection")

async def verify_connection():
    load_dotenv()
    
    logger.info("🔍 Initializing Connection Test...")
    
    try:
        broker = get_broker()
        broker_name = os.getenv("ACTIVE_BROKER", "unknown").upper()
        logger.info(f"📡 Target Broker: {broker_name}")
        
        if not broker.authenticate():
            logger.error(f"❌ Failed to authenticate with {broker_name}. Check your credentials in .env")
            return

        logger.info(f"✅ Authenticated with {broker_name}")
        
        # Ghost Trade: Limit Buy SPY at $1.00
        symbol = "SPY"
        limit_price = 1.00
        amount = 1.00 # 1 share approx at $1.00
        
        logger.info(f"👻 Placing Ghost Trade: Limit BUY {symbol} at ${limit_price}...")
        
        # Most brokers require amount or quantity. For this test, we'll try to buy 1 share or $1 worth.
        # Based on AlpacaAdapter, it calculates qty = int(amount / limit_price)
        res = broker.submit_order(symbol, amount, "buy", order_type="limit", limit_price=limit_price)
        
        if "error" in res:
            logger.error(f"❌ Ghost Trade FAILED: {res['error']}")
        else:
            order_id = res.get('id') or res.get('order_id') or res.get('id')
            status = res.get('status') or 'Submitted'
            logger.info(f"🎉 Order Placed (ID: {order_id})")
            
            # Immediately Cancel
            logger.info("🛑 Cancelling test order...")
            if hasattr(broker, 'cancel_order') and order_id:
                broker.cancel_order(order_id)
            elif hasattr(broker, 'cancel_all_orders'):
                broker.cancel_all_orders()
            else:
                import robin_stocks.robinhood as rh
                rh.orders.cancel_all_stock_orders()
                
            logger.info("✅ CONNECTION VERIFIED: Read/Write access confirmed.")
            logger.info("---------------------------------------------------------")

    except Exception as e:
        logger.error(f"💥 Connection verification crashed: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(verify_connection())
