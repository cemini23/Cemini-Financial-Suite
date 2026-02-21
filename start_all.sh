#!/bin/bash
# ==========================================
#        CEMINI SUITE MASTER LAUNCHER
# Optimized for M4 Apple Silicon & Docker
# ==========================================

# 1. Environment Check
if [ ! -f ".env" ]; then
    echo "⚠️  WARNING: .env file not found in root. Please create it based on README.md."
    exit 1
fi

# 2. Infrastructure Optimization (Optional but recommended for high-load DBs)
echo "🧠 Optimizing Docker VM..."
docker run --privileged --rm alpine sysctl -w vm.max_map_count=1048576 --quiet 2>/dev/null || echo "⚠️  Skipping kernel optimization (requires privileged access)."

# 3. Launch Docker Suite
echo "🚀 Starting Cemini Financial Suite (Docker)..."
docker-compose up -d --build

# 4. Success Check
if [ $? -eq 0 ]; then
    echo "✅ Suite is LIVE."
    echo "🖥️  UI Dashboard (Deephaven): http://localhost:10000"
    echo "🐘 DB Manager (pgAdmin): http://localhost:5050"
    echo "   Login: admin@cemini.com / admin"
    echo ""
    echo "To view logs, run: docker-compose logs -f"
else
    echo "❌ ERROR: Failed to start Docker suite."
    exit 1
fi
