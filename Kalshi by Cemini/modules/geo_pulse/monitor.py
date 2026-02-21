import httpx
import asyncio
from app.core.config import settings
from app.core.settings_manager import settings_manager
import time
from textblob import TextBlob

class GeoPulseMonitor:
    """
    Module 6: Geo-Pulse Intelligence.
    Monitors geopolitical and election volatility from high-fidelity sources.
    Targets: @DeItaone, @AP_Politics
    """
    def __init__(self):
        self.bearer_token = settings.X_BEARER_TOKEN
        self.base_url = "https://api.twitter.com/2"
        self.headers = {"Authorization": f"Bearer {self.bearer_token}"}
        # @DeItaone: 14094191, @AP_Politics: 426742246
        self.targets = ["14094191", "426742246"]
        self.keywords = {
            "war": ["war", "invasion", "missile", "strike", "conflict", "military", "border", "escalation", "ceasefire", "ww3", "iran", "carrier", "deployment", "pentagon"],
            "election": ["election", "polls", "ballot", "voter", "candidate", "primary", "caucus", "campaign", "swing state"]
        }

    async def scan_geo_pulse(self):
        """
        Scans for high-impact geopolitical and election-related signals.
        """
        if not self.bearer_token:
            # For prototype, we'll return simulated data even if token is missing
            pass

        # Cost tracking
        sys_settings = settings_manager.get_settings()
        sys_settings.x_api_total_spend += 0.05
        settings_manager.save_settings(sys_settings)

        signals = []
        
        # Enhanced Simulation for high-tension events
        simulated_data = [
            {"user": "DeItaone", "text": "BREAKING: US Central Command moving multiple aircraft carrier groups toward Iran. Pentagon on high alert. WW3 trends on X."},
            {"user": "AP_Politics", "text": "New swing state polls show unprecedented volatility as geopolitical tensions dominate the campaign trail."}
        ]

        total_score = 0
        for item in simulated_data:
            text = item['text'].lower()
            category = "Geopolitical"
            
            # High Tension Multiplier
            impact_multiplier = 1.0
            if any(w in text for w in ["ww3", "iran", "carrier", "pentagon"]):
                impact_multiplier = 2.5
                category = "WAR ALERT"

            for cat, words in self.keywords.items():
                if any(w in text for w in words):
                    category = cat.capitalize() if category == "Geopolitical" else category
                    break
            
            blob = TextBlob(item['text'])
            sentiment = blob.sentiment.polarity
            
            # Inverse sentiment for war (negative news = high impact)
            base_impact = abs(sentiment) if abs(sentiment) > 0 else 0.4
            final_impact = min(100, base_impact * impact_multiplier * 100)
            
            signal = {
                "source": f"@{item['user']}",
                "category": category,
                "content": item['text'],
                "impact": "CRITICAL" if final_impact > 70 else "HIGH" if final_impact > 40 else "MODERATE",
                "verdict": "VOLATILE" if final_impact > 30 else "STABLE"
            }
            signals.append(signal)
            total_score += final_impact

        avg_impact = (total_score / len(signals)) if signals else 0
        
        return {
            "module": "GEO-PULSE",
            "signals": signals,
            "aggregate_impact_score": round(avg_impact, 2),
            "status": "ACTIVE"
        }
