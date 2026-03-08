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
        """
        Wilder's Smoothed Moving Average RSI (industry standard, Wilder 1978).

        Seeds with SMA on first `period` deltas, then applies exponential
        smoothing: avg = (prev_avg * (period - 1) + current) / period.
        This matches pandas-ta, TradingView, and most professional platforms.
        """
        prices = self.price_history.get(symbol)
        if prices is None or len(prices) < period + 1:
            return None  # Use fallback in analysis

        # D8: Wilder's SMMA RSI — replaces former SMA-based calculation.
        deltas = np.diff(prices)
        gains = np.maximum(deltas, 0)
        losses = -np.minimum(deltas, 0)

        # Seed: SMA of the first `period` bars
        avg_gain = float(np.mean(gains[:period]))
        avg_loss = float(np.mean(losses[:period]))

        # Smooth remaining bars with Wilder's formula
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

# Singleton instance for real-time updates
realtime_brain = QuantBrain()
