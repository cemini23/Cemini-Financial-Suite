# CEMINI FINANCIAL SUITE™
# Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
# All Rights Reserved.
"""
QuantOS™ v9.4.0 - Unified Launcher
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import sys
import os
import subprocess

if __name__ == "__main__":
    print(f"🚀 QuantOS v9.4.0 Unified Startup")
    print("Copyright (c) 2026 Cemini23 / Claudio Barone Jr.")
    print("-" * 40)

    # In v9.4, main.py is multi-threaded and handles UI + Engine.
    # We simply launch main.py.
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 QuantOS shutting down...")
        sys.exit(0)
