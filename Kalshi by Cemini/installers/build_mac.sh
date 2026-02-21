#!/bin/bash

echo "=================================================="
echo "      KALSHI BY CEMINI | MAC BUILD SYSTEM"
echo "=================================================="

# 1. Install Requirements
echo "[*] Checking dependencies..."
python3 -m pip install -r requirements.txt

# 2. Clean previous builds
echo "[*] Cleaning old builds..."
rm -rf build dist

# 3. Build the App
echo "[*] Compiling Application..."
pyinstaller --name "KalshiByCemini" --onedir --clean --noconfirm app/main.py

# 4. Copy Frontend Assets
echo "[*] Copying Dashboard & Logo..."
cp -R "frontend" "dist/KalshiByCemini/frontend"

echo ""
echo "=================================================="
echo "[OK] BUILD COMPLETE!"
echo "=================================================="
echo "Your app is ready in: dist/KalshiByCemini/KalshiByCemini"
