import robin_stocks.sofi as sofi
import logging

class SoFiBroker:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.is_logged_in = False

    def login(self):
        """Authenticates with SoFi. May require 2FA code in terminal."""
        try:
            # This will prompt for 2FA in the terminal on the first run
            login = sofi.login(self.username, self.password)
            self.is_logged_in = True
            print("✅ SoFi: Logged in successfully.")
        except Exception as e:
            print(f"❌ SoFi Login Failed: {e}")

    def get_balance(self):
        """Retrieves buying power."""
        if not self.is_logged_in: return 0
        profile = sofi.load_account_profile()
        return float(profile.get('buying_power', 0))

    def execute_trade(self, symbol, qty, side="buy"):
        """Executes a market order on SoFi."""
        if not self.is_logged_in: return
        
        try:
            if side.lower() == "buy":
                order = sofi.order_buy_market(symbol, qty)
            else:
                order = sofi.order_sell_market(symbol, qty)
            print(f"🚀 SoFi ORDER: {side.upper()} {qty} {symbol}")
            return order
        except Exception as e:
            print(f"⚠️ SoFi Trade Error: {e}")
