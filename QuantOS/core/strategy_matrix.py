"""
QuantOS™ v15.0.0 - Master Strategy Matrix (Confluence Engine)
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
from core.logger_config import get_logger

logger = get_logger("strategy_matrix")

class MasterStrategyMatrix:
    """
    The Master Confluence Engine.
    Filters out noise by requiring both a quantitative anomaly (BigQuery)
    and a qualitative catalyst (FinBERT News).
    """
    def __init__(self, engine, cloud_signals, x_oracle):
        self.engine = engine # Refers to TradingEngine
        self.signals = cloud_signals
        self.oracle = x_oracle

    async def evaluate_market(self):
        """The core loop: Synchronizes BigQuery data with FinBERT news signals."""
        current_data = self.signals.get_current_signals()
        spikes = current_data.get('volume_spikes', [])
        
        # Pull high-conviction FinBERT signals from the Oracle
        recent_news = self.oracle.get_active_signals() 
        
        for asset in spikes:
            symbol = asset['symbol']
            multiplier = asset['multiplier']
            price_change = asset['price_change_5m']
            
            # 1. Look for a verified confluence catalyst
            catalyst = recent_news.get(symbol)
            
            if not catalyst:
                # No trusted news for this spike. Algorithmic noise.
                continue 
                
            sentiment = catalyst['sentiment']
            confidence = catalyst['confidence']
            trust_score = catalyst['trust_score']
            source = catalyst['source']
            
            category = self.engine.symbol_category_map.get(symbol, "unknown")

            # SCENARIO A: The "Overreaction Dip" (Panic Sell on Bullish News)
            if multiplier >= 3.0 and price_change <= -2.0 and sentiment == "positive":
                logger.info(f"🔥 CONFLUENCE: Overreaction Detected on {symbol}!")
                logger.info(f"   ↳ Catalyst: @{source} (Trust: {trust_score}) - {confidence*100}% Bullish")
                await self.engine.execute_dip_buy(symbol, self.engine.broker.get_latest_price(symbol), category, self.engine.execution_engine)
                
            # SCENARIO B: The "Confirmed Breakout" (Surge on Bullish News)
            elif multiplier >= 3.0 and price_change >= 2.0 and sentiment == "positive":
                logger.info(f"🚀 CONFLUENCE: Breakout Confirmed on {symbol}!")
                logger.info(f"   ↳ Catalyst: @{source} (Trust: {trust_score}) - {confidence*100}% Bullish")
                # Momentum-specific execution can go here
                await self.engine.execute_dip_buy(symbol, self.engine.broker.get_latest_price(symbol), category, self.engine.execution_engine)
                
            # SCENARIO C: The "Death Spiral" (Crash on Bearish News)
            elif multiplier >= 3.0 and price_change <= -2.0 and sentiment == "negative":
                logger.info(f"☠️  CONFLUENCE: Death Spiral on {symbol}. Catalyst is BEARISH. Avoid dip buy.")
                # Opportunity for shorting or protecting existing positions
