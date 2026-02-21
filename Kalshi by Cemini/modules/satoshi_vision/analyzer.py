from modules.satoshi_vision.charts import ChartReader
from modules.satoshi_vision.technicals import TechnicalAnalyst
import pandas as pd
import asyncio

class SatoshiAnalyzer:
    def __init__(self):
        self.reader = ChartReader()
        self.ta = TechnicalAnalyst()

    async def analyze_btc_market(self):
        """Legacy support for the standard 5m dashboard route."""
        return await self.analyze_multiframe(asset="BTC", horizon="SCALP")

    async def analyze_multiframe(self, asset="BTC", horizon="SCALP"):
        """
        Multi-Timeframe Strategy Switcher with Dynamic ATR Risk Management.
        """
        try:
            # 1. Select Timeframe based on Horizon
            if horizon == "SCALP":
                tf, limit = '5m', 100
            elif horizon == "SWING":
                tf, limit = '4h', 200
            elif horizon == "MACRO":
                tf, limit = '1d', 365 
            else:
                tf, limit = '1h', 100

            # 2. Get Data
            symbol = f"{asset}/USD"
            df = await self.reader.get_candles(symbol, timeframe=tf, limit=limit)
            if df.empty: return {"status": "error", "msg": "No Market Data"}

            # 3. Apply Advanced Math
            df = self.ta.apply_advanced_indicators(df)
            curr = df.iloc[-1]
            
            # 4. Dynamic Risk Management (The QuantOS Upgrade)
            atr = curr['ATR']
            current_price = curr['close']
            
            # Safe Stop = 2x ATR | Target = 3x ATR (1.5 R/R Ratio)
            stop_loss = current_price - (2.0 * atr)
            take_profit = current_price + (3.0 * atr)

            # 5. Strategy Confluence Scoring
            score = 0
            reasons = []

            if horizon == "SCALP":
                if curr['RSI'] < 30: 
                    score += 30; reasons.append("Oversold (RSI < 30)")
                if curr['close'] < curr['BBL_20_2.0']: 
                    score += 20; reasons.append("Bollinger Band Breakout (Lower)")
                if curr['close'] > curr['VWAP_D']:
                    score += 15; reasons.append("Above Institutional VWAP")

            elif horizon == "SWING":
                if curr['MACD_12_26_9'] > curr['MACDs_12_26_9']:
                    score += 30; reasons.append("Bullish MACD Momentum Cross")
                if curr['close'] > curr['EMA_50']:
                    score += 30; reasons.append("Price Holding above 50 EMA")
                if curr['ADX_14'] > 25:
                    score += 10; reasons.append("Strong Trend Strength (ADX)")

            elif horizon == "MACRO":
                if curr['close'] > curr['EMA_200']:
                    score += 60; reasons.append("Bull Market Regime (Above 200 EMA)")
                else:
                    score -= 40; reasons.append("Bear Market Regime (Below 200 EMA)")
                past = df.iloc[-30]
                if curr['OBV'] > past['OBV']:
                    score += 20; reasons.append("Long-term Volume Accumulation (OBV)")

            # 6. Verdict Calculation
            sentiment = "NEUTRAL"
            if score > 50:
                sentiment = "INSTITUTIONAL BULL" if score > 75 else "BULLISH"
            elif score < 25:
                sentiment = "BEARISH"

            action = "WAIT / CHOP"
            if score >= 65: action = "ENTER LONG (CALL)"
            elif score <= 20: action = "ENTER SHORT (PUT)"

            return {
                "market": symbol,
                "horizon": horizon,
                "sentiment": sentiment,
                "score": f"{score}/100",
                "price": {
                    "current": round(current_price, 2),
                    "atr_volatility": round(atr, 2)
                },
                "trade_setup": {
                    "action": action,
                    "stop_loss": round(stop_loss, 2),
                    "take_profit": round(take_profit, 2),
                    "risk_reward": "1:1.5"
                },
                "indicators": {
                    "RSI": round(curr['RSI'], 1),
                    "ADX": round(curr['ADX_14'], 1),
                    "ATR": round(atr, 2)
                },
                "logic": reasons
            }
        finally:
            await self.reader.close()
