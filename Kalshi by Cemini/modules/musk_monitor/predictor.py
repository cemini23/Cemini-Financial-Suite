from modules.musk_monitor.sources import MuskDataSources
from modules.musk_monitor.personality import PersonalityMatrix
from modules.musk_monitor.x_api import XMonitor
import asyncio

class MuskPredictor:
    def __init__(self):
        self.sources = MuskDataSources()
        self.personality = PersonalityMatrix()
        self.x_monitor = XMonitor()
        self.BASELINE_DAILY = 100 

    async def predict_today(self):
        # 1. Gather Intelligence in Parallel
        empire_task = self.sources.get_empire_status()
        launches_task = self.sources.get_spacex_launches()
        x_task = self.x_monitor.get_recent_tweet_velocity()
        
        empire, launches, x_data = await asyncio.gather(empire_task, launches_task, x_task)
        
        # Synchronous factors
        bio = self.personality.get_biological_factor()
        meme = self.personality.get_meme_index()

        # 2. Calculate Modifiers
        score = self.BASELINE_DAILY
        
        # Factor in Real-Time Velocity from X API
        if x_data.get('velocity'):
            # If current velocity is high, it heavily weights the daily score up
            score = (score * 0.4) + (x_data['velocity'] * 24 * 0.6)
        
        news_impact = empire['volatility_score'] * 5 
        score += news_impact
        
        launch_impact = 0
        for l in launches:
            if l['intensity'] == "EXTREME": launch_impact += 50
            else: launch_impact += 15
        score += launch_impact
        
        score = score * meme['multiplier']
        
        # 3. Final Output & Variance
        prediction_low = int(score * 0.85)
        prediction_high = int(score * 1.15)
        
        # Use X API data to refine current velocity
        current_velocity = x_data.get('velocity', (score / 24) * bio['factor'])

        return {
            "prediction": {
                "total_daily_tweets": f"{prediction_low} - {prediction_high}",
                "current_status": x_data.get('status', bio['status']),
                "velocity_per_hour": round(current_velocity, 1)
            },
            "factors": {
                "x_api_sync": "CONNECTED" if x_data.get('status') == "Live API Data" else "OFFLINE (Using Proxy)",
                "news_volatility": f"Score {empire['volatility_score']} ({len(empire['active_headlines'])} headlines)",
                "active_launches": [l['mission'] for l in launches] if launches else "None",
                "meme_triggers": meme['triggers']
            }
        }
