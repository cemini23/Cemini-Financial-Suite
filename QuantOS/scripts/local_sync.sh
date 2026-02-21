#!/bin/bash
# QuantOS v9.1 - Local Dual-Library Sync
# Synchronizes the Live project with the Private Backup repository.

LIVE_PATH="/Users/User/Desktop/QuantOS"
PRIVATE_PATH="/Users/User/Desktop/QuantOS_Private"

echo "🔄 Initiating Local Sync..."
echo "📍 Source: $LIVE_PATH"
echo "📍 Destination: $PRIVATE_PATH"

# Ensure private directory exists
mkdir -p "$PRIVATE_PATH"

# Perform Rsync
# -a: Archive mode
# -v: Verbose
# -z: Compress
# --delete: Mirror delete
rsync -avz --delete \
    --exclude='.git/' \
    --exclude='venv/' \
    --exclude='__pycache__/' \
    --exclude='*.log' \
    --exclude='.env' \
    --exclude='.pytest_cache/' \
    --exclude='build/' \
    --exclude='dist/' \
    "$LIVE_PATH/" "$PRIVATE_PATH/"

# Handle .env separately
if [ ! -f "$PRIVATE_PATH/.env" ] && [ -f "$LIVE_PATH/.env" ]; then
    cp "$LIVE_PATH/.env" "$PRIVATE_PATH/.env"
    echo "🔐 Initialized .env in Private Backup."
fi

echo "✅ Dual-Library Sync Complete. Your backup is now 1:1 with your live environment."
