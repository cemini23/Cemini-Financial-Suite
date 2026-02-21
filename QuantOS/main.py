# CEMINI FINANCIAL SUITE™
# Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
# All Rights Reserved.
"""
QuantOS™ v1.5.0 - Cemini Financial Suite Standard
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import os
import sys
import socket
import threading
import time
import webbrowser
import requests
import uvicorn
from interface import create_app
from core.engine import TradingEngine
from core.logger_config import get_logger

logger = get_logger("launcher")

# --- CONFIGURATION ---
PORT = 8001
CHECK_INTERVAL = 0.5  # Seconds between health checks
MAX_WAIT_TIME = 10    # Max seconds to wait for server

def wait_for_server(port):
    """Pings the server until it responds or times out."""
    url = f"http://127.0.0.1:{port}/"
    start_time = time.time()
    
    print(f"🏥 Performing health checks on port {port}...", end="", flush=True)
    
    while time.time() - start_time < MAX_WAIT_TIME:
        try:
            # We check if the server is up and returning something
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                print(" ✅ ONLINE")
                return True
        except (requests.ConnectionError, requests.Timeout):
            pass
        time.sleep(CHECK_INTERVAL)
        print(".", end="", flush=True)
    
    print(" ❌ TIMEOUT")
    return False

def launch_browser_safely(port):
    """Waits for server health check, then opens browser."""
    if wait_for_server(port):
        print(f"🚀 Launching Dashboard: http://127.0.0.1:{port}")
        webbrowser.open(f"http://127.0.0.1:{port}")
    else:
        print("\n⚠️  WARNING: Browser launch skipped (Server not responding).")
        print(f"   Please manually visit: http://127.0.0.1:{port}")

def start_engine_background():
    """Starts the trading bot without blocking the UI."""
    try:
        logger.info("📡 Initializing Trading Engine thread...")
        bot = TradingEngine()
        # Run even if closed for monitoring and sunset reporting
        bot.run()
    except Exception as e:
        logger.error(f"⚠️  Engine Error: {e}")
        print(f"\n⚠️  TRADING ENGINE ERROR: {e}")

# --- MAIN ENTRY POINT ---
if __name__ == "__main__":
    print(f"✅ Selected Port: {PORT}")

    # 2. Initialize App (FastAPI)
    app = create_app()

    # 3. Start Trading Engine (Background Thread)
    engine_thread = threading.Thread(target=start_engine_background, daemon=True)
    engine_thread.start()

    # 4. Start Browser Launcher (Background Thread)
    launcher_thread = threading.Thread(target=launch_browser_safely, args=(PORT,), daemon=True)
    launcher_thread.start()

    # 5. Start Web Server (Blocking)
    print("⚡ Starting QuantOS Web Server...")
    try:
        # Fixed to 127.0.0.1 and Port 8001 for Suite Protocol
        uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="error")
    except Exception as e:
        print(f"❌ Server Crash: {e}")
        logger.error(f"Server crashed: {e}")
