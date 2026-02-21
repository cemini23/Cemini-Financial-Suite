import os
from dotenv import load_dotenv

# Load variables from .env file
# This assumes the execution context has access to the project root
load_dotenv()

class Credentials:
    # Data Ingestion
    POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
    ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
    ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
    
    # QuantOS (Crypto, Stocks, Options)
    RH_USERNAME = os.getenv('RH_USERNAME')
    RH_PASSWORD = os.getenv('RH_PASSWORD')
    COINBASE_API_KEY = os.getenv('COINBASE_API_KEY')
    COINBASE_API_SECRET = os.getenv('COINBASE_API_SECRET')
    
    # Kalshi By Cemini (Prediction Markets)
    KALSHI_EMAIL = os.getenv('KALSHI_EMAIL')
    KALSHI_PASSWORD = os.getenv('KALSHI_PASSWORD')
    KALSHI_API_KEY = os.getenv('KALSHI_API_KEY')
    KALSHI_SENDER_ID = os.getenv('KALSHI_SENDER_ID')
    KALSHI_TARGET_ID = os.getenv('KALSHI_TARGET_ID')
    
    # Social & Sentiment
    X_BEARER_TOKEN = os.getenv('X_BEARER_TOKEN')
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

def verify_credentials():
    """
    Validation check to ensure critical keys are loaded.
    """
    # Define which keys are strictly mandatory for core boot
    mandatory = [
        'POLYGON_API_KEY', 
        'RH_USERNAME', 
        'KALSHI_API_KEY'
    ]
    
    missing = [k for k in mandatory if getattr(Credentials, k) is None or "YOUR_" in str(getattr(Credentials, k))]
    
    if missing:
        print(f"⚠️  WARNING: Missing or placeholder credentials for: {', '.join(missing)}")
        return False
    else:
        print("✅ SUCCESS: Found existing credentials. System ready for boot.")
        return True

if __name__ == "__main__":
    verify_credentials()
