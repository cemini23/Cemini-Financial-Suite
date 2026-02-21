import httpx
import asyncio

class KalshiOracle:
    """
    QuantOS Macro Oracle.
    Queries the Kalshi by Cemini engine (Port 8000) for institutional arbitrage signals.
    """
    def __init__(self):
        self.KALSHI_URL = "http://127.0.0.1:8000/api/v1"

    async def get_macro_sentiment(self):
        """
        Asks Kalshi: "What is the Macro Outlook?"
        Returns a Risk Multiplier (0.5 = Defensive, 1.5 = Aggressive)
        """
        risk_multiplier = 1.0
        intel = []

        async with httpx.AsyncClient() as client:
            try:
                # 1. Check Fed Rates (The Powell Protocol)
                resp = await client.get(f"{self.KALSHI_URL}/powell/analyze", timeout=2.0)
                if resp.status_code == 200:
                    data = resp.json()
                    # Logic: Inversion or Cut probability increases aggression
                    if data['macro_indicators']['yield_curve'] == "INVERTED":
                        risk_multiplier += 0.2
                        intel.append("Yield Curve Inversion Detected (+Aggression)")
                    
                    p = data['adjusted_consensus']
                    if p['CUT_25'] > 0.4:
                        risk_multiplier += 0.3
                        intel.append("High Fed Cut Probability (+Bullish)")

                # 2. Check Social Alpha
                resp_social = await client.get(f"{self.KALSHI_URL}/social/analyze", timeout=2.0)
                if resp_social.status_code == 200:
                    social_data = resp_social.json()
                    if social_data['aggregate_sentiment'] == "BULLISH":
                        risk_multiplier += 0.1
                        intel.append("Social Alpha is Bullish (+Hype)")

            except Exception as e:
                intel.append(f"Connection to Kalshi Failed: {e}")
                
        return {
            "risk_modifier": round(risk_multiplier, 2),
            "source_intel": intel,
            "timestamp": asyncio.get_event_loop().time()
        }
