import redis
import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "cemini_redis_2026")

def trigger_panic():
    print("🚨 CEMINI SUITE: PANIC BUTTON ACTIVATED")
    try:
        r = redis.Redis(host=REDIS_HOST, port=6379, password=REDIS_PASSWORD, decode_responses=True)
        r.publish("emergency_stop", "CANCEL_ALL")
        print("✅ Emergency signal broadcasted to EMS.")
    except Exception as e:
        print(f"❌ Failed to broadcast emergency signal: {e}")

if __name__ == "__main__":
    trigger_panic()
