#!/usr/bin/env bash
# Cemini Financial Suite — Local Dev Setup
# Usage: ./setup.sh

set -e

VENV_DIR=".venv"

# ── 1. Python version check ──────────────────────────────────────────────────
echo "Checking Python version..."
PYTHON_BIN=""
for cmd in python3.12 python3.11 python3; do
    if command -v "$cmd" &>/dev/null; then
        version=$("$cmd" -c 'import sys; print(sys.version_info[:2])')
        major=$("$cmd" -c 'import sys; print(sys.version_info[0])')
        minor=$("$cmd" -c 'import sys; print(sys.version_info[1])')
        if [ "$major" -ge 3 ] && [ "$minor" -ge 11 ]; then
            PYTHON_BIN="$cmd"
            echo "  Found: $cmd ($version)"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "ERROR: Python 3.11+ is required but not found."
    echo "  Install it from https://www.python.org/downloads/ or via your package manager."
    exit 1
fi

# ── 2. Create venv ───────────────────────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR ..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists at $VENV_DIR"
fi

# ── 3. Install requirements ──────────────────────────────────────────────────
echo "Installing requirements..."
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r requirements.txt

# ── 4. Copy .env if missing ──────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env from .env.example"
else
    echo ".env already exists — skipping copy"
fi

# ── 5. Done ──────────────────────────────────────────────────────────────────
echo ""
echo "Setup complete! Edit .env with your API keys then run: docker compose up -d"
