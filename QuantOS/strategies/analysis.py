"""
QuantOS™ v7.0.0 - Strategy Analysis Engine
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import pandas as pd
import ta
import joblib
import os
import threading
import numpy as np
from core.logger_config import get_logger
from strategies import analytics

logger = get_logger("analysis")

# Load ML Model Asynchronously
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core', 'model_v1.pkl')
ml_model = None

def load_model_async():
    global ml_model
    if os.path.exists(MODEL_PATH):
        try:
            ml_model = joblib.load(MODEL_PATH)
            logger.info("ML Model loaded successfully in Analysis Engine.")
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
    else:
        logger.warning(f"ML Model file not found at {MODEL_PATH}. AI Forecaster will be disabled.")

# Start loading in a separate thread
threading.Thread(target=load_model_async, daemon=True).start()

def calculate_confidence_score(symbol, history, rsi_realtime=None, is_simulation=False):
    """
    Returns a confidence score from 0-100.
    """
    if history.empty:
        return 0, {}

    try:
        close = history['Close']
        current_price = close.iloc[-1]
        
        # 1. Technical Indicators
        # A) RSI (Use pre-calculated if available, otherwise calculate on slice)
        if 'RSI' in history.columns:
            rsi_val = history['RSI'].iloc[-1]
        else:
            rsi_val = rsi_realtime if rsi_realtime is not None else ta.momentum.rsi(close, window=14).iloc[-1]
        
        # B) MACD
        macd = ta.trend.MACD(close)
        macd_line = macd.macd().iloc[-1]
        signal_line = macd.macd_signal().iloc[-1]
        
        # C) Bollinger Bands
        bollinger = ta.volatility.BollingerBands(close, window=20, window_dev=2)
        lower_band = bollinger.bollinger_lband().iloc[-1]
        
        # D) Moving Averages (Use pre-calculated if available)
        if 'SMA_50' in history.columns and 'SMA_200' in history.columns:
            sma_50 = history['SMA_50'].iloc[-1]
            sma_200 = history['SMA_200'].iloc[-1]
        else:
            sma_50 = close.rolling(window=50).mean().iloc[-1]
            sma_200 = close.rolling(window=200).mean().iloc[-1]

        # 2. Scoring System (0-100)
        score = 0
        reasons = []

        # RSI Oversold (Max 25)
        if rsi_val < 30:
            score += 25
            reasons.append("RSI Critical Oversold (+25)")
        elif rsi_val < 35:
            score += 15
            reasons.append("RSI Oversold (+15)")
        
        # MACD Bullish Crossover (Max 20)
        if macd_line > signal_line:
            score += 20
            reasons.append("MACD Bullish (+20)")
            
        # Bollinger Dip (Max 20)
        if current_price < lower_band * 1.02:
            score += 20
            reasons.append("Bollinger Dip (+20)")
            
        # Golden Cross (Max 15)
        if sma_50 > sma_200:
            score += 15
            reasons.append("Golden Cross (+15)")

        # External Data / AI Forecaster (Max 20)
        if not is_simulation:
            # Future: add get_news_sentiment() here
            if ml_model is not None:
                try:
                    volume = history['volume'].iloc[-1] if 'volume' in history.columns else 0
                    features = pd.DataFrame([[rsi_val, macd_line, volume]], columns=['RSI', 'MACD', 'Volume'])
                    pred = ml_model.predict(features)[0]
                    if pred == 1:
                        score += 20
                        reasons.append("AI Bullish (+20)")
                except Exception as e:
                    logger.warning(f"ML Prediction failed for {symbol}: {e}")
        else:
            # SIMULATION FALLBACK: Add dummy weight for missing live factors
            score += 15
            reasons.append("Sim Fallback (+15)")

        indicators = {
            'rsi': rsi_val,
            'macd': macd_line,
            'score': score,
            'reasons': reasons
        }

        return score, indicators

    except Exception as e:
        logger.error(f"Analysis Error on {symbol}: {e}")
        return 0, {}
