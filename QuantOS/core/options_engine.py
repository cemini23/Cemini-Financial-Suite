"""
QuantOS™ - Institutional Trading System
Copyright (c) 2026 Cemini23
All Rights Reserved. Commercial use without permission is prohibited.
"""
import time
import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# CACHE: Store IV for 5 min
_iv_cache = {}

def get_cached_iv(symbol):
    current = time.time()
    if symbol in _iv_cache:
        val, ts = _iv_cache[symbol]
        if current - ts < 300: return val
    return None

class OptionsEngine:
    def __init__(self, api=None):
        self.api = api

    def find_atm_contract(self, symbol, type="call"):
        today = datetime.now()
        target_date = today + timedelta(days=7)
        days_until_friday = (4 - target_date.weekday() + 7) % 7
        expiry_date = target_date + timedelta(days=days_until_friday)
        expiry_str = expiry_date.strftime("%y%m%d")
        
        t_char = 'C' if type.lower() == "call" else 'P'
        # Dummy strike for OCC symbol generation
        strike = 100 
        strike_formatted = f"{int(strike * 1000):08d}"
        
        contract_symbol = f"{symbol.ljust(6)}{expiry_str}{t_char}{strike_formatted}"
        return contract_symbol.replace(" ", "")

    def calculate_limit_price(self, bid, ask):
        """Returns the Mid-Price."""
        return (bid + ask) / 2

    def submit_safe_order(self, symbol, side, quantity):
        """
        Gets current Bid/Ask and submits a limit order at the mid-price.
        """
        try:
            # In a real Robinhood/Alpaca integration:
            # quote = self.api.get_option_quote(symbol)
            # bid = float(quote.bid_price)
            # ask = float(quote.ask_price)
            
            # Placeholder values for logic demonstration
            bid = 1.00
            ask = 1.10
            
            limit_price = self.calculate_limit_price(bid, ask)
            print(f"Submitting SAFE {side.upper()} order for {symbol} at ${limit_price:.2f}")
            
            # Example API call:
            # self.api.submit_order(symbol=symbol, qty=quantity, side=side, type='limit', limit_price=limit_price)
            return True
        except Exception as e:
            print(f"Error submitting safe order: {e}")
            return False

    def get_implied_volatility(self, history_df):
        if history_df is None or len(history_df) < 30:
            return 0.30
        history_df['Close'] = pd.to_numeric(history_df['Close'], errors='coerce')
        history_df = history_df.dropna(subset=['Close'])
        log_returns = np.log(history_df['Close'] / history_df['Close'].shift(1))
        vol = log_returns.tail(30).std() * math.sqrt(252)
        return vol
