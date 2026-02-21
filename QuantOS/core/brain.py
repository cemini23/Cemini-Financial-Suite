"""
QuantOS™ v7.0.0 - Real-time Brain
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import numpy as np
from core.logger_config import get_logger

logger = get_logger("brain")

class QuantBrain:
    def __init__(self):
        self.price_history = {} # Dictionary of numpy arrays

    def update_price(self, symbol, price):
        if symbol not in self.price_history:
            self.price_history[symbol] = np.array([], dtype=float)
        
        # Append new price efficiently
        self.price_history[symbol] = np.append(self.price_history[symbol], price)
        
        # Keep only last 1000 data points to save RAM
        if len(self.price_history[symbol]) > 1000:
            self.price_history[symbol] = self.price_history[symbol][-1000:]

    def calculate_rsi(self, symbol, period=14):
        prices = self.price_history.get(symbol)
        if prices is None or len(prices) < period + 1:
            return None # Use fallback in analysis

        # Vectorized RSI Calculation (Fast)
        deltas = np.diff(prices)
        gains = np.maximum(deltas, 0)
        losses = -np.minimum(deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

# Singleton instance for real-time updates
realtime_brain = QuantBrain()
