from webull import webull
import os

class WebullBroker:
    def __init__(self):
        self.wb = webull()
        self.email = os.getenv("WEBULL_EMAIL")
        self.password = os.getenv("WEBULL_PASSWORD")
        self.trade_pin = os.getenv("WEBULL_PIN")

    def login(self):
        """Authenticates with Webull. Requires MFA on first run."""
        try:
            # You will need to provide the MFA code in the terminal
            self.wb.login(self.email, self.password)
            self.wb.get_trade_token(self.trade_pin)
            print("✅ Webull: Logged in and Trade Token secured.")
        except Exception as e:
            print(f"❌ Webull Login Failed: {e}")

    def execute_trade(self, symbol, qty, side="buy"):
        """Executes a market order on Webull."""
        try:
            order = self.wb.place_order(stock=symbol, action=side.upper(), orderType='MKT', enforce='GTC', quantity=qty)
            print(f"🚀 Webull ORDER: {side.upper()} {qty} {symbol}")
            return order
        except Exception as e:
            print(f"⚠️ Webull Trade Error: {e}")
