import redis
import json
import os
from dotenv import load_dotenv

# Load variables from .env (ensure your keys are there!)
load_dotenv()

def send_test_trade():
    try:
        # Connect to the Redis container running on your Mac
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # This is a manual trigger for a  test trade
        # Ensure 'KXGOLD-24DEC-B2500' is an active ticker or replace with one that is
        test_trade = {
            "verdict": "EXECUTE",
            "symbol": "KXGOLD-24DEC-B2500", 
            "action": "BUY",
            "position_size": 1.00,
            "confidence_score": 1.0,
            "reasoning": "M4 System Sanity Check - Manual Trigger"
        }
        
        r.publish('trade_signals', json.dumps(test_trade))
        print("🚀 Signal sent to Redis bus! Check ems_executor logs for the FIX message.")
        
    except redis.exceptions.ConnectionError:
        print("❌ Error: Could not connect to Redis. Is the container running?")

if __name__ == "__main__":
    send_test_trade()
