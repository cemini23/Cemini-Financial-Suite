"""
QuantOS™ v7.0.0 - Smart Updater
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import requests
import os
import time

# --- CONFIGURATION ---
# REPLACE "cemini23" with your real GitHub Username!
BASE_URL = "https://raw.githubUsercontent.com/cemini23/QuantOS/main/"
VERSION_URL = BASE_URL + "version.txt"

# List of files to update (Main system files)
FILES_TO_UPDATE = [
    "main.py",
    "core/execution.py",
    "core/brain.py",
    "core/ledger.py",
    "core/tax_engine.py",
    "core/money_manager.py",
    "core/broker_interface.py",
    "core/brokers/factory.py",
    "core/brokers/robinhood.py",
    "core/brokers/alpaca.py",
    "core/brokers/ibkr.py",
    "core/brokers/schwab.py",
    "interface/server.py",
    "interface/templates/index.html",
    "interface/templates/backtester.html",
    "interface/templates/settings.html",
    "interface/templates/analytics.html",
    "strategies/analysis.py",
    "strategies/backtester.py",
    "scripts/deploy_v4.sh",
    "requirements.txt"
]

CURRENT_VERSION_FILE = "version.txt"

def update_bot():
    print("☁️  Checking for updates...")
    
    # 1. Get Local Version
    try:
        with open(CURRENT_VERSION_FILE, "r") as f:
            local_version = f.read().strip()
    except:
        local_version = "0.0"

    # 2. Get Remote Version
    try:
        response = requests.get(VERSION_URL, timeout=5)
        if response.status_code != 200:
            print("⚠️  Update server offline. Skipping.")
            return False
            
        remote_version = response.text.strip()
        
        # 3. Compare & Update
        if remote_version > local_version:
            print(f"🚨 NEW VERSION FOUND: {remote_version} (Current: {local_version})")
            print("⬇️  Downloading new brains...")
            
            # Download EVERY file in the list
            for filename in FILES_TO_UPDATE:
                print(f"   - Updating {filename}...")
                file_url = BASE_URL + filename
                try:
                    r = requests.get(file_url, timeout=10)
                    
                    if r.status_code == 200:
                        with open(filename, "w") as f:
                            f.write(r.text)
                    else:
                        print(f"   ❌ Failed to download {filename}: {r.status_code}")
                except Exception as e:
                    print(f"   ❌ Error updating {filename}: {e}")
            
            # Update version file last
            with open(CURRENT_VERSION_FILE, "w") as f:
                f.write(remote_version)
                
            print("✅ UPDATE COMPLETE! Restarting bot...")
            time.sleep(2)
            return True # Signal to restart
            
        else:
            print("✅ Bot is up to date.")
            return False

    except Exception as e:
        print(f"⚠️  Update Check Failed: {e}")
        return False

if __name__ == "__main__":
    update_bot()