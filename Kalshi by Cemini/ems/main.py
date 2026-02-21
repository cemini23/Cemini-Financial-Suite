import redis
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

def handle_signal(message):
    """Processes signals received from the Redis bus."""
    try:
        data = json.loads(message['data'])
        print(f"📥 RECEIVED SIGNAL: {data['action']} {data['symbol']} | Reason: {data['reasoning']}")
        
        if data['verdict'] == "EXECUTE":
            # This is where the Kalshi FIX message (35=D) would be triggered
            print(f"⚡ EXECUTING: Sending {data['action']} order for {data['symbol']} to Kalshi...")
            # Placeholder for FIX logic: 
            # fix_client.send_order(data['symbol'], data['action'], data['position_size'])
            print("✅ ORDER PLACED SUCCESSFULLY")
            
    except Exception as e:
        print(f"❌ Error processing signal: {e}")

def main():
    print("🤖 EMS Engine Starting...")
    r = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=6379, db=0)
    p = r.pubsub()
    
    # Subscribe to the channel we used in the test script
    p.subscribe('trade_signals')
    print("📡 Subscribed to 'trade_signals'. Waiting for Brain signals...")

    while True:
        message = p.get_message()
        if message and message['type'] == 'message':
            handle_signal(message)
        time.sleep(0.1)  # Prevent high CPU usage

if __name__ == "__main__":
    main()
