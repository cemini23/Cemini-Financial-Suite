import robin_stocks.robinhood as rh
import os
from dotenv import load_dotenv

load_dotenv()
def sell_all_positions():
    """Non-interactive sell all for server use"""
    # Assuming already logged in via main bot or server
    holdings = rh.build_holdings()
    for symbol in holdings:
        try:
            rh.orders.order_sell_fractional_by_quantity(symbol, float(holdings[symbol]['quantity']))
        except Exception as e:
            print(f"❌ Failed to sell {symbol}: {e}")

def emergency_sell():
    rh.login(Username=os.getenv("RH_UserNAME"), password=os.getenv("RH_PASSWORD"))

    print("🔥 EMERGNCY SELL PROTOCOL INITIATED 🔥")
    confirm = input("Type 'SELL EVERYTHING' to confirm: ")

    if confirm == "SELL EVERYTHING":
        holdings = rh.build_holdings()
        for symbol in holdings:
            print(f"🔻 Selling all {symbol}...")
            try:
                rh.orders.order_sell_fractional_by_price(symbol, float(holdings[symbol]['equity']))
            except Exception as e:
                print(f"❌ Failed to sell {symbol}: {e}")
        print("DONE.")
    else:
        print("Aborted.")

if __name__ == '__main__':
    emergency_sell()