"""
QuantOS™ v14.0.0 - FinBERT NLP Engine
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
from transformers import pipeline
import logging
from core.logger_config import get_logger

# Suppress the heavy HuggingFace loading logs
logging.getLogger("transformers").setLevel(logging.ERROR)
logger = get_logger("nlp_engine")

class FinBERTSentiment:
    def __init__(self):
        logger.info("🧠 INITIALIZING NLP: Loading FinBERT (This may take a minute on the first boot)...")
        try:
            # ProsusAI/finbert is the industry standard open-source financial NLP model
            self.analyzer = pipeline("sentiment-analysis", model="ProsusAI/finbert")
            logger.info("✅ NLP ENGINE ONLINE: Ready to parse market sentiment.")
        except Exception as e:
            logger.error(f"❌ Failed to load NLP model: {e}")
            self.analyzer = None

    def analyze_text(self, text):
        """
        Reads the text and returns a structured sentiment profile.
        Returns: sentiment (positive, negative, neutral) and a confidence score (0.0 to 1.0)
        """
        if not self.analyzer:
            return {"sentiment": "neutral", "confidence": 0.0}

        try:
            # The model returns a list containing a dictionary
            result = self.analyzer(text)[0] 
            
            sentiment = result['label'].lower()
            confidence = result['score']
            
            # Filter low-confidence signals to prevent over-trading
            if confidence < 0.75:
                sentiment = "neutral"
                
            return {
                "sentiment": sentiment,
                "confidence": round(confidence, 3)
            }
        except Exception as e:
            logger.error(f"⚠️ NLP Processing Error: {e}")
            return {"sentiment": "neutral", "confidence": 0.0}
