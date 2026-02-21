#!/bin/bash
# QuantOS v7.0.0 - Tri-Sync Deployment Script
# Copyright (c) 2026 Cemini23 / Claudio Barone Jr.

echo "⛓️ Starting Tri-Sync Deployment (v8.9.1)..."

# 1. SECURITY SWEEP
python3 scripts/security_sweep.py
if [ $? -ne 0 ]; then
    echo "🚨 DEPLOYMENT ABORTED: Security Sweep Failed."
    exit 1
fi

# 2. PRIVATE BACKUP (Location B)
PRIVATE_PATH="/Users/User/Desktop/QuantOS_Private"
echo "💾 Syncing to Private Backup: $PRIVATE_PATH..."
mkdir -p "$PRIVATE_PATH"

# Sync excluding sensitive or temporary files
# We use -a (archive), -v (verbose), -z (compress)
rsync -avz --exclude='.git/' --exclude='__pycache__/' --exclude='*.log' --exclude='.env' ./ "$PRIVATE_PATH/"

# Handle .env separately (only copy if missing in destination)
if [ ! -f "$PRIVATE_PATH/.env" ]; then
    if [ -f ".env" ]; then
        cp ".env" "$PRIVATE_PATH/.env"
        echo "📝 Initialized .env in private backup."
    fi
fi

# 3. GITHUB SYNC (Location C)
echo "🌐 Syncing to GitHub..."
git add .
git commit -m "v8.9.1 - Force Sync Update (Aggressive Git Reset Logic)"
git push origin main

echo "✅ All 3 locations (Live, Private, Remote) are synced."
