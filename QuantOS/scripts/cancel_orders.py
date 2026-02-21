import robin_stocks.robinhood as rh
import os
from dotenv import load_dotenv

load_dotenv()

def cancel_everything():
    print("🔌 Connecting to Robinhood to CANCEL ALL ORDERS...")
    try:
        rh.login(Username=os.getenv("RH_UserNAME"), password=os.getenv("RH_PASSWORD"))
        print("✅ Logged in.")
        
        print("🛑 Canceling all open orders...")
        try:
            rh.orders.cancel_all_stock_orders()
        except:
            pass
        try:
            rh.orders.cancel_all_option_orders()
        except:
            pass
        print("✅ All open orders have been cancelled.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    cancel_everything()