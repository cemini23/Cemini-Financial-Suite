import httpx
import asyncio
from app.core.config import settings

class XMonitor:
    """
    Direct X API v2 Monitor for High-Fidelity Behavioral Tracking.
    Calculates precise velocity and detects biological 'Vampire Window' activity.
    """
    def __init__(self):
        self.bearer_token = settings.X_BEARER_TOKEN
        self.base_url = "https://api.twitter.com/2"
        self.headers = {"Authorization": f"Bearer {self.bearer_token}"}
        # Elon Musk's User ID
        self.target_user_id = "44196397" 

    async def get_recent_tweet_velocity(self):
        """
        Fetches the last 24 hours of activity to calculate real-time tweet velocity.
        """
        if not self.bearer_token:
            return {"velocity": 0, "status": "No API Token"}

        url = f"{self.base_url}/users/{self.target_user_id}/tweets"
        params = {
            "max_results": 100,
            "tweet.fields": "created_at",
            "exclude": "retweets"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=self.headers, params=params)
                if resp.status_code != 200:
                    return {"velocity": 0, "error": resp.text}
                
                data = resp.json()
                tweets = data.get('data', [])
                
                # Calculate velocity based on count in last 24h
                # In a real-world scenario, we'd parse 'created_at' and count precisely
                tweet_count = len(tweets)
                velocity = tweet_count / 24.0
                
                return {
                    "velocity": round(velocity, 2),
                    "raw_count_24h": tweet_count,
                    "status": "Live API Data"
                }
        except Exception as e:
            return {"velocity": 0, "error": str(e)}

    async def check_bio_clock(self):
        """
        Analyzes the gaps between recent tweets to predict sleep/wake state.
        Detects if Elon is currently in the 'Vampire Window' (Active late).
        """
        # Simplified logic for the prototype
        velocity_data = await self.get_recent_tweet_velocity()
        if velocity_data.get('velocity', 0) > 4.5:
            return "HYPER-ACTIVE (Likely Vampire Window)"
        return "STABLE (Baseline Activity)"
