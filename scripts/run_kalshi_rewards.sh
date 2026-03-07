#!/usr/bin/env bash
# =============================================================================
# scripts/run_kalshi_rewards.sh — Kalshi Rewards Tracker cron wrapper
#
# Sources the root .env and Kalshi .env, then runs kalshi_rewards.py.
# Designed to be called from cron or manually.
#
# Cron setup (8:00 AM ET Mon-Fri = 12:00 UTC standard / 13:00 UTC DST):
#   As root:  crontab -e
#   Add line:
#     0 12 * * 1-5 /opt/cemini/scripts/run_kalshi_rewards.sh >> /mnt/archive/kalshi_rewards/cron.log 2>&1
#
# Manual run:
#   /opt/cemini/scripts/run_kalshi_rewards.sh
# =============================================================================
set -euo pipefail

REPO_ROOT="/opt/cemini"
cd "${REPO_ROOT}"

# Source root .env (REDIS_PASSWORD, etc.)
if [[ -f ".env" ]]; then
    set -o allexport
    # shellcheck disable=SC1091
    source <(grep -v '^#' .env | grep '=')
    set +o allexport
fi

# Source Kalshi-specific .env (KALSHI_API_KEY, KALSHI_PRIVATE_KEY_PATH)
KALSHI_ENV="Kalshi by Cemini/.env"
if [[ -f "${KALSHI_ENV}" ]]; then
    set -o allexport
    # shellcheck disable=SC1091
    source <(grep -v '^#' "${KALSHI_ENV}" | grep '=')
    set +o allexport
fi

# Defaults
export REDIS_HOST="${REDIS_HOST:-localhost}"
export KALSHI_ENVIRONMENT="${KALSHI_ENVIRONMENT:-production}"
export KALSHI_PRIVATE_KEY_PATH="${KALSHI_PRIVATE_KEY_PATH:-${REPO_ROOT}/Kalshi by Cemini/private_key.pem}"

export PYTHONPATH="${REPO_ROOT}"

echo "[run_kalshi_rewards] $(date -u '+%Y-%m-%dT%H:%M:%SZ') Starting rewards check"
/usr/bin/python3 "${REPO_ROOT}/scripts/kalshi_rewards.py"
echo "[run_kalshi_rewards] $(date -u '+%Y-%m-%dT%H:%M:%SZ') Done"
