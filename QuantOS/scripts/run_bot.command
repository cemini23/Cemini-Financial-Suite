#!/bin/bash
cd "$(dirname "$0")"

# 1. Activate Brain
source venv/bin/activate

# 2. RUN AUTO-UPDATER
echo "🔄 Checking for updates..."
python3 update.py

# 3. LAUNCH BOT (Insomniac Mode)
echo "---------------------------------"
echo "🚀 STARTING SURVIVOR BOT"
echo "☕️ Keeping Mac awake..."
echo "---------------------------------"

caffeinate -i python3 main.py

echo "---------------------------------"
echo "Bot stopped. Press Enter to close."
read