#!/bin/bash
# QuantOS™ v7.1.1 - Installer (MAC)
# Copyright (c) 2026 Cemini23 / Claudio Barone Jr.

cd "$(dirname "$0")"

echo "------------------------------------------------"
echo "   🚀 QuantOS INSTALLER (MAC) 🚀"
echo "------------------------------------------------"

# Move to root if run from scripts
if [[ "$PWD" == *"/scripts" ]]; then
    cd ..
fi

# 0. Check for Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python3 not found. Please install it from python.org"
    exit 1
fi

# 1. Setup Python Environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ ERROR: Failed to create venv."
        exit 1
    fi
fi

# 2. Install Libraries
echo "⬇️  Installing dependencies (This may take a moment)..."
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# 3. Validation
python3 scripts/validate_env.py
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Installation failed validation."
    exit 1
fi

# 3. Create Config
if [ ! -f .env ]; then
    echo "⚙️  Creating config file..."
    cp .env.example .env
    echo "✅ Created .env file!"
    echo "⚠️  IMPORTANT: Open .env and add your Robinhood password!"
else
    echo "✅ Config found."
fi

echo "------------------------------------------------"
echo "🎉 INSTALLATION COMPLETE!"
echo "------------------------------------------------"