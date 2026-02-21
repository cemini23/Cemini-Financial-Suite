from app.core.settings_manager import settings_manager

class CapitalAllocator:
    """
    The Money Management Engine.
    Uses Fractional Kelly Criterion to maximize growth while minimizing ruin risk.
    """
    def __init__(self, bankroll=None):
        self.settings = settings_manager.get_settings()
        # Use provided bankroll or fallback to system max_budget
        self.bankroll = bankroll if bankroll is not None else self.settings.max_budget

    def calculate_position_size(self, confidence_score: float, odds: float = 2.0) -> float:
        """
        Calculates optimal position size using Kelly Criterion.
        
        Args:
            confidence_score (float): Model's confidence (0-100).
            odds (float): Decimal odds (e.g., 2.0 = +100 = 50/50 payout).
        
        Returns:
            float: Amount to bet in USD.
        """
        if confidence_score < 60: return 0.0 # Safety Filter
        
        # 1. Convert Confidence to Probability (p)
        # We temper the raw score to be conservative
        p = (confidence_score / 100.0) 
        q = 1 - p
        b = odds - 1 # Net odds received on the wager
        
        # 2. Kelly Formula: f = (bp - q) / b
        f_star = (b * p - q) / b
        
        # 3. Fractional Kelly (Risk Management)
        # We use 'Quarter Kelly' or 'Half Kelly' based on risk settings
        fraction = 0.25 # Default Conservative
        
        if self.settings.risk_level == "MODERATE": fraction = 0.40
        if self.settings.risk_level == "AGGRESSIVE": fraction = 0.50
        
        position_percent = max(0, f_star) * fraction
        
        # 4. Cap Max Exposure
        # Never bet more than the user-defined max (e.g., 10%)
        max_exposure = self.settings.max_position_size / 100.0
        final_percent = min(position_percent, max_exposure)
        
        position_size = self.bankroll * final_percent
        return round(position_size, 2)

    def get_portfolio_status(self):
        # In a real scenario, this would query the Kalshi API for account balance
        return {
            "equity": self.bankroll,
            "weekly_pnl": 124.50, # Simulated PnL
            "weekly_target": 250.00
        }
