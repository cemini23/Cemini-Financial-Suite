#!/usr/bin/env bash
# Run Schemathesis API fuzz tests against live Docker services.
# Usage: ./scripts/run_fuzz.sh [kalshi|screener|mcp|all]
#
# Requires: schemathesis installed, target service running.
# Does NOT run in CI — execute manually before major releases.
set -euo pipefail

TARGET=${1:-all}

_check_service() {
    local name="$1"
    local url="$2"
    if curl -sf "$url" >/dev/null 2>&1; then
        echo "✅ $name is up ($url)"
        return 0
    else
        echo "⚠️  $name unavailable at $url — skipping"
        return 1
    fi
}

echo "🔍 Cemini API Fuzz Testing — target: $TARGET"
echo ""

if [[ "$TARGET" == "kalshi" || "$TARGET" == "all" ]]; then
    if _check_service "Kalshi API" "http://localhost:8000/openapi.json"; then
        echo "🧪 Fuzzing Kalshi API (port 8000)..."
        schemathesis run http://localhost:8000/openapi.json \
            --checks all \
            --max-response-time=5000 \
            --hypothesis-max-examples=200 \
            --stateful=links \
            --output-truncate=true \
            --exitfirst || true
    fi
fi

if [[ "$TARGET" == "screener" || "$TARGET" == "all" ]]; then
    if _check_service "Opportunity Screener" "http://localhost:8003/openapi.json"; then
        echo "🧪 Fuzzing Opportunity Screener (port 8003)..."
        schemathesis run http://localhost:8003/openapi.json \
            --checks all \
            --max-response-time=5000 \
            --hypothesis-max-examples=200 \
            --output-truncate=true \
            --exitfirst || true
    fi
fi

if [[ "$TARGET" == "mcp" || "$TARGET" == "all" ]]; then
    if _check_service "cemini_mcp" "http://localhost:8002/openapi.json"; then
        echo "🧪 Fuzzing cemini_mcp (port 8002)..."
        schemathesis run http://localhost:8002/openapi.json \
            --checks all \
            --max-response-time=5000 \
            --hypothesis-max-examples=100 \
            --output-truncate=true \
            --exitfirst || true
    fi
fi

echo ""
echo "✅ Fuzz run complete."
