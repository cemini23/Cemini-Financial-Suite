"""
QuantOS™ v7.0.0 - Tax Engine
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import pandas as pd
from datetime import datetime, timedelta
from config.settings_manager import settings_manager
from core.logger_config import get_logger
from core import ledger

logger = get_logger("tax_engine")

class TaxEngine:
    def __init__(self):
        self.wash_sale_days = 30

    def is_wash_sale_risk(self, symbol, current_date=None) -> bool:
        """
        Rule: If a stock was sold for a loss within the last 30 days, flag it.
        """
        if not current_date:
            current_date = datetime.now()
        
        # Load full history to find recent losses
        history = ledger.get_trade_history(limit=1000)
        if not history:
            return False

        cutoff_date = current_date - timedelta(days=self.wash_sale_days)
        
        # We need to track the FIFO PnL of each trade to know if it was a loss
        # Simplified: Check if any 'SELL' action for this symbol in last 30 days had (Price < AvgBuyPrice)
        # Note: ledger.py doesn't store PnL per row, so we might need a quick calculation here
        
        # To accurately detect wash sale, we look for realized losses in the period
        # For QuantOS v6.0, we'll implement a simplified check:
        # If there's a SELL in the last 30 days, we check if it was likely a loss.
        
        # For simplicity in this implementation, we'll use a helper to scan the ledger
        try:
            df = pd.read_csv(ledger.LEDGER_FILE)
            df['Date'] = pd.to_datetime(df['Date'])
            
            # Filter for this symbol and within 30 days
            recent_sells = df[(df['Ticker'] == symbol) & 
                              (df['Action'] == 'SELL') & 
                              (df['Date'] > cutoff_date)]
            
            if recent_sells.empty:
                return False

            # In a real system, we'd match with specific buy lots.
            # Simplified: if 'Reason' contains 'Stop' or 'Panic', it's likely a loss or risk we want to avoid re-entering.
            # Real logic: We should check the profit.
            # Let's see if any recent sell was below the average buy price at that time.
            # This is complex without a full PnL log. 
            
            # CFO Decision: If 'Reason' contains 'Stop', we flag it as a wash sale risk.
            for _, row in recent_sells.iterrows():
                if "Stop" in str(row['Reason']) or "Panic" in str(row['Reason']):
                    logger.info(f"🚩 Wash Sale Risk detected for {symbol}: Recent exit due to {row['Reason']}")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking wash sale risk: {e}")
            return False

    def estimate_tax_bill(self, gross_profit) -> float:
        """
        Calculate estimated tax based on tax bracket setting.
        """
        rate = settings_manager.get("tax_bracket_pct") / 100.0
        if gross_profit <= 0:
            return 0.0
        return gross_profit * rate

    def get_net_profit(self, gross_profit) -> float:
        """
        Returns Gross - Est. Tax.
        """
        return gross_profit - self.estimate_tax_bill(gross_profit)

tax_engine = TaxEngine()
