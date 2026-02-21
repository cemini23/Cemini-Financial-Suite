"""
Trigger a fresh start (full position liquidation) in the QuantOS Trading Engine.

The engine checks Redis for the 'quantos:fresh_start_requested' key on every
open-market loop iteration. Setting it to 'true' causes the engine to call
liquidate_all_positions() on the next cycle and then reset the key to 'false'.

Usage (local):
    REDIS_HOST=localhost python QuantOS/scripts/trigger_fresh_start.py

Usage (Docker):
    docker exec -it signal_generator python scripts/trigger_fresh_start.py
"""
import redis
import os


def trigger_fresh_start():
    host = os.getenv("REDIS_HOST", "localhost")
    r = redis.Redis(host=host, port=6379, decode_responses=True)
    r.set("quantos:fresh_start_requested", "true")
    print(f"✅ Fresh start requested (Redis @ {host}). "
          "The engine will liquidate all positions on the next open-market cycle.")
    r.close()


def cancel_fresh_start():
    host = os.getenv("REDIS_HOST", "localhost")
    r = redis.Redis(host=host, port=6379, decode_responses=True)
    r.set("quantos:fresh_start_requested", "false")
    print(f"🚫 Fresh start cancelled (Redis @ {host}).")
    r.close()


def status():
    host = os.getenv("REDIS_HOST", "localhost")
    r = redis.Redis(host=host, port=6379, decode_responses=True)
    val = r.get("quantos:fresh_start_requested") or "false"
    print(f"📊 Fresh start requested: {val}")
    r.close()


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "trigger"
    if cmd == "cancel":
        cancel_fresh_start()
    elif cmd == "status":
        status()
    else:
        trigger_fresh_start()
