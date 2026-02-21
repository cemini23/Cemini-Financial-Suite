import tweepy
from textblob import TextBlob
from app.core.config import settings
from app.core.settings_manager import settings_manager
import asyncio
import time

class SocialAnalyzer:
    """
    Module 5: The Social Alpha Scanner.
    Filters high-value trader tweets and calculates institutional sentiment.
    """
    def __init__(self):
        self.auth = tweepy.OAuth2BearerHandler(settings.X_BEARER_TOKEN)
        self.api = tweepy.API(self.auth)
        self.client = tweepy.Client(bearer_token=settings.X_BEARER_TOKEN)
        
        self.keywords = {
            "news": ["news", "announced", "official", "report", "fed", "sec", "etf", "listing", "breaking"],
            "charts": ["charts", "ta", "rsi", "macd", "support", "resistance", "fibonacci", "volume", "candle", "breakout"],
            "sentiment": ["long", "short", "pump", "dump", "bullish", "bearish", "moon", "fud"],
            "cultural": ["meta", "hype", "community", "trend", "viral", "culture", "mainstream", "adoption", "alpha"],
            "weather": ["weather", "temp", "heatwave", "storm", "forecast", "degree", "hot", "cold", "record", "climate"]
        }

    def check_budget_safety(self):
        """
        Returns False if we are burning too much money or scanning too fast.
        """
        sys_settings = settings_manager.get_settings()
        
        # 1. Frequency Check
        now = time.time()
        if now - sys_settings.last_social_scan < (sys_settings.social_scan_frequency * 60):
            return False, "Scan Frequency Limit"
            
        # 2. Budget Check
        if sys_settings.x_api_total_spend >= (sys_settings.x_api_budget_limit * 0.9):
            print(f"[CRITICAL] X API Budget at 90% (${sys_settings.x_api_total_spend}). Stopping Social Scan.")
            return False, "Budget Limit Reached"
            
        return True, "Safe"

    async def get_target_sentiment(self):
        """
        Analyzes recent tweets from the target pool for BTC sentiment.
        """
        if not settings.X_BEARER_TOKEN:
            return {"status": "error", "msg": "X API Token Missing"}

        is_safe, reason = self.check_budget_safety()
        sys_settings = settings_manager.get_settings()
        
        if not is_safe:
            return {
                "status": "standby", 
                "msg": f"Scan skipped: {reason}",
                "traders_monitored": sys_settings.traders,
                "score": 0,
                "budget_used": sys_settings.x_api_total_spend,
                "aggregate_sentiment": "NEUTRAL"
            }

        # Update Last Scan Time
        sys_settings.last_social_scan = time.time()
        sys_settings.x_api_total_spend += 0.03 # Cost per scan
        settings_manager.save_settings(sys_settings)

        results = []
        total_polarity = 0
        
        # Use dynamic traders from settings
        targets = sys_settings.traders
        
        # Simulation for prototype
        simulated_tweets = [
            {"user": t, "text": f"BTC looks ready for a massive breakout here, RSI resetting perfectly. #{t}Alpha"}
            for t in targets[:3]
        ]

        for tweet in simulated_tweets:
            text = tweet['text'].lower()
            
            # Identify Intelligence Category
            category = "General"
            for cat, words in self.keywords.items():
                if any(w in text for w in words):
                    category = cat.capitalize()
                    break

            # Sentiment Analysis
            blob = TextBlob(tweet['text'])
            sentiment = blob.sentiment.polarity # -1.0 to 1.0
            
            results.append({
                "trader": tweet['user'],
                "category": category,
                "content": tweet['text'][:50] + "...",
                "polarity": round(sentiment, 2),
                "verdict": "BULLISH" if sentiment > 0.1 else "BEARISH" if sentiment < -0.1 else "NEUTRAL"
            })
            total_polarity += sentiment

        avg_sentiment = total_polarity / len(results) if results else 0
        
        return {
            "traders_monitored": targets,
            "signals": results,
            "aggregate_sentiment": "BULLISH" if avg_sentiment > 0.1 else "BEARISH" if avg_sentiment < -0.1 else "NEUTRAL",
            "score": round(avg_sentiment, 2),
            "budget_used": sys_settings.x_api_total_spend
        }
