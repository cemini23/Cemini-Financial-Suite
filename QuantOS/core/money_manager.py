"""
QuantOS™ v7.0.0 - Money Manager
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
from core.logger_config import get_logger

logger = get_logger("money_manager")

class MoneyManager:
    def __init__(self):
        self.max_portfolio_exposure = 0.10  # Hard cap: 10% max for any single trade

    def calculate_position_size(self, portfolio_total, confidence_score, min_threshold=75):
        """
        Logic uses dynamic threshold passed from execution engine.
        """
        if confidence_score >= 90:
            percentage = 0.05
        elif confidence_score >= min_threshold:
            percentage = 0.025
        else:
            percentage = 0.0
            
        # Apply hard cap safety
        if percentage > self.max_portfolio_exposure:
            logger.warning(f"Position size {percentage*100}% exceeded hard cap. Capping at {self.max_portfolio_exposure*100}%.")
            percentage = self.max_portfolio_exposure
            
        amount = portfolio_total * percentage
        logger.info(f"💰 Money Manager: Score {confidence_score} -> {percentage*100}% allocation (${amount:.2f})")
        return amount

money_manager = MoneyManager()
