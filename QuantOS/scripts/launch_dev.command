#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo "☕️ Keeping Mac awake..."
caffeinate -i python3 main.py