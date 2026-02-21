"""
QuantOS™ v14.2.0 - X-Oracle Sentiment Engine (AI-Powered)
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import threading
from datetime import datetime, timezone
from core.logger_config import get_logger
from core.sentiment.nlp_engine import FinBERTSentiment

logger = get_logger("x_oracle")

class CredibilityEngine:
    def __init__(self):
        # Tier 1: The "God Tier" (100% Trust)
        self.tier_1_whitelist = [
            "tier10k", "unusual_whales", "WalterBloomberg", 
            "charliebilello", "WSJmarkets"
        ]
        
        # Max age of a tweet to be considered actionable (e.g., 15 minutes)
        self.MAX_AGE_SECONDS = 900 
        
        # Initialize the AI reader
        self.nlp = FinBERTSentiment()
        
        # Thread-safe signal cache: {ticker: {signal_data}}
        self.active_signals = {}
        self._lock = threading.Lock()

    def get_active_signals(self):
        """Returns the current cache of high-conviction signals."""
        with self._lock:
            # Clean up old signals (older than MAX_AGE_SECONDS)
            now = datetime.now(timezone.utc)
            expired = []
            for ticker, signal in self.active_signals.items():
                ts = datetime.fromisoformat(signal['timestamp'].replace('Z', '+00:00'))
                if (now - ts).total_seconds() > self.MAX_AGE_SECONDS:
                    expired.append(ticker)
            for ticker in expired:
                del self.active_signals[ticker]
            
            return self.active_signals.copy()

    def calculate_trust_score(self, tweet_data, user_data):
        """
        Dynamically scores an account from 0.0 to 1.0.
        """
        username = user_data.get("username")
        
        # 1. Check the Whitelist
        if username in self.tier_1_whitelist:
            return 1.0
            
        score = 0.0
        
        # 2. Follower/Following Ratio (Filters out bot networks)
        followers = user_data.get("public_metrics", {}).get("followers_count", 0)
        following = user_data.get("public_metrics", {}).get("following_count", 1)
        
        if followers > 10000 and (followers / following) > 5.0:
            score += 0.4
        elif followers < 500:
            return 0.0    
            
        # 3. Account Age
        try:
            created_at_str = user_data.get("created_at")
            if created_at_str:
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                age_years = (datetime.now(timezone.utc) - created_at).days / 365
                if age_years > 3.0:
                    score += 0.3
        except Exception as e:
            logger.error(f"Error calculating account age: {e}")
            
        # 4. Verification Status
        if user_data.get("verified"):
            score += 0.2
            
        # 5. Engagement Quality
        retweets = tweet_data.get("public_metrics", {}).get("retweet_count", 0)
        if retweets > 50:
            score += 0.1
            
        return min(score, 1.0)

    def process_incoming_tweet(self, tweet_payload, ticker_context=None):
        """Filters tweets by credibility, then reads them for trading signals."""
        try:
            tweet_time_str = tweet_payload['data']['created_at']
            tweet_time = datetime.fromisoformat(tweet_time_str.replace('Z', '+00:00'))
            age_seconds = (datetime.now(timezone.utc) - tweet_time).total_seconds()
            
            # HARD FILTER: Check the Date/Time
            if age_seconds > self.MAX_AGE_SECONDS:
                return None
                
            # DYNAMIC FILTER: Calculate the Score
            user_info = tweet_payload['includes']['users'][0]
            trust_score = self.calculate_trust_score(
                tweet_data=tweet_payload['data'], 
                user_data=user_info
            )
            
            if trust_score < 0.5:
                return None
            
            # If the account is trusted, let FinBERT read the actual text
            text = tweet_payload['data']['text']
            nlp_result = self.nlp.analyze_text(text)
            
            # Ignore neutral news to prevent over-trading
            if nlp_result["sentiment"] == "neutral":
                return None
                
            signal = {
                "source": user_info['username'],
                "trust_score": trust_score,
                "sentiment": nlp_result["sentiment"],  # 'positive' or 'negative'
                "confidence": nlp_result["confidence"],
                "text": text,
                "related_ticker": ticker_context,
                "timestamp": tweet_time_str
            }
            
            logger.info(f"🔥 HIGH-CONVICTION NEWS: [{signal['source']}] | {signal['sentiment'].upper()} ({signal['confidence']*100}%)")
            
            # CACHE the signal for confluence
            if ticker_context:
                with self._lock:
                    self.active_signals[ticker_context] = signal
            
            return signal
            
        except Exception as e:
            logger.error(f"Error processing tweet: {e}")
            return None

# Singleton instance
x_oracle = CredibilityEngine()
