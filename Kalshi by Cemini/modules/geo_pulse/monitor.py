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
            print("[WARNING] Geo-Pulse: X_BEARER_TOKEN not configured. Returning NO_SIGNAL.")
            return {
                "module": "GEO-PULSE",
                "signals": [],
                "aggregate_impact_score": 0,
                "status": "NO_SIGNAL",
                "msg": "X_BEARER_TOKEN not configured"
            }

        # Cost tracking
        sys_settings = settings_manager.get_settings()
        sys_settings.x_api_total_spend += 0.05
        settings_manager.save_settings(sys_settings)

        signals = []

        # Fetch live tweets from X API for target accounts
        user_map = {"14094191": "DeItaone", "426742246": "AP_Politics"}
        live_data = []
        async with httpx.AsyncClient() as client:
            for user_id in self.targets:
                try:
                    resp = await client.get(
                        f"{self.base_url}/users/{user_id}/tweets",
                        headers=self.headers,
                        params={"max_results": 5, "tweet.fields": "text,created_at"},
                        timeout=5.0
                    )
                    if resp.status_code == 200:
                        tweets = resp.json().get('data', [])
                        user_name = user_map.get(user_id, user_id)
                        for tweet in tweets:
                            live_data.append({"user": user_name, "text": tweet['text']})
                    else:
                        print(f"[WARNING] Geo-Pulse: X API returned HTTP {resp.status_code} for user {user_id}.")
                except Exception as e:
                    print(f"[WARNING] Geo-Pulse: X API failed for user {user_id} ({e}).")

        if not live_data:
            print("[WARNING] Geo-Pulse: No tweets fetched from X API. Returning NO_SIGNAL.")
            return {
                "module": "GEO-PULSE",
                "signals": [],
                "aggregate_impact_score": 0,
                "status": "NO_SIGNAL",
                "msg": "X API returned no data"
            }

        total_score = 0
        for item in live_data:
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
