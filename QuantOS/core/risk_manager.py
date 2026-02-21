"""
QuantOS™ - Institutional Trading System
Copyright (c) 2026 Cemini23
All Rights Reserved. Commercial use without permission is prohibited.
"""
from config.settings_manager import settings_manager

class RiskManager:
    def __init__(self, api=None):
        self.api = api
        self.max_options_allocation = 0.05  # 5% of portfolio
        self.max_daily_loss = 0.03          # 3% daily stop
        self.starting_equity = None

    def get_exit_levels(self, entry_price, side='buy'):
        """Calculates stop-loss and profit target levels"""
        stop_loss_pct = settings_manager.get("stop_loss_pct")
        profit_target_pct = settings_manager.get("take_profit_pct")
        
        if side == 'buy':
            stop = entry_price * (1 - stop_loss_pct)
            target = entry_price * (1 + profit_target_pct)
        else: # sell/short
            stop = entry_price * (1 + stop_loss_pct)
            target = entry_price * (1 - profit_target_pct)
        return {"stop": round(stop, 2), "target": round(target, 2)}

    def check_exposure(self, portfolio):
        total_value = float(portfolio.equity)
        
        # Initialize starting equity for daily loss tracking
        if self.starting_equity is None:
            self.starting_equity = total_value
            
        # Daily Loss Check
        daily_loss = (self.starting_equity - total_value) / self.starting_equity
        if daily_loss >= self.max_daily_loss:
            return "BLOCKED_DAILY_LOSS"

        # Options Allocation Check
        # Assuming portfolio object or api can provide options market value
        options_value = getattr(portfolio, 'options_market_value', 0)
        if (options_value / total_value) > self.max_options_allocation:
            return "BLOCKED_ALLOCATION_LIMIT"

        for position in portfolio.positions:
            position_value = float(position.market_value)
            if position_value > 0.20 * total_value:
                return "OVEREXPOSED"
        return "HEALTHY"

    def can_trade_options(self, ticker, spread, volume):
        """
        Safety Check for Options Liquidity
        IF spread > 0.15 (Wide spread trap) -> Return False.
        IF volume < 50 (Illiquid trap) -> Return False.
        """
        if spread > 0.15:
            return False
        if volume < 50:
            return False
        return True

    def suggest_hedge(self, symbol, quantity, market_trend):
        if market_trend == "BEARISH" and quantity > 100:
            hedge_quantity = quantity // 100
            return f"BUY {hedge_quantity} PUTS on {symbol} (Hedge)"
        return "No hedge suggested"
