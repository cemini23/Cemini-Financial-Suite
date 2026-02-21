#!/bin/bash
echo "🚀 Starting QuantOS v2.0 System..."

# Trap Ctrl+C to kill both processes when you exit
trap "kill 0" EXIT

# Start the Dashboard (Backend + Frontend)
echo "📊 Launching Dashboard on http://127.0.0.1:8000..."
export PYTHONPATH=$PYTHONPATH:.
./venv/bin/python3 -m uvicorn interface.server:app --port 8000 &

# Wait 2 seconds for server to spin up
sleep 2

# Start the Trading Bot
echo "🤖 Launching Trading Engine..."
./venv/bin/python3 main.py &

# Keep script running
wait
