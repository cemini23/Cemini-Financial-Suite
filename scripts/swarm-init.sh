#!/usr/bin/env bash
# =============================================================================
# Cemini Financial Suite — Docker Swarm Initialization (Step 34a)
# Run ONCE on the VPS to migrate from docker compose to Swarm stack mode.
#
# IMPORTANT: Run this OUTSIDE market hours (Mon-Fri 9:30am-4pm ET).
#            All running containers will be stopped and restarted as Swarm
#            services. There will be ~60-120 seconds of downtime.
#
# Prerequisites:
#   - Docker Engine 24+ (already installed on the Hetzner VPS)
#   - /opt/cemini/.env and "Kalshi by Cemini/.env" present
#   - At least 200MB free RAM (Swarm manager overhead: ~60-80MB)
#
# Usage:
#   cd /opt/cemini
#   chmod +x scripts/swarm-init.sh
#   ./scripts/swarm-init.sh
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STACK_NAME="cemini"

log()  { echo "[swarm-init] $*"; }
warn() { echo "[swarm-init] WARNING: $*"; }
die()  { echo "[swarm-init] ERROR: $*" >&2; exit 1; }

cd "${REPO_ROOT}"

# ── Pre-flight checks ─────────────────────────────────────────────────────────
log "Pre-flight checks..."
[[ -f ".env" ]] || die ".env file missing at ${REPO_ROOT}/.env"
[[ -f "Kalshi by Cemini/.env" ]] || warn "Kalshi .env not found — kalshi services may fail"
docker info &>/dev/null || die "Docker daemon not running"

# Check if already in Swarm mode
SWARM_STATE=$(docker info --format '{{.Swarm.LocalNodeState}}' 2>/dev/null || echo "inactive")
if [[ "${SWARM_STATE}" == "active" ]]; then
    log "Swarm already initialized (node state: ${SWARM_STATE})"
else
    log "Initializing Docker Swarm (single-node)..."
    # Bind to the primary network interface; --advertise-addr can be localhost for single-node
    SWARM_IP=$(hostname -I | awk '{print $1}')
    docker swarm init --advertise-addr "${SWARM_IP}" # nosec B104
    log "Swarm initialized. Manager address: ${SWARM_IP}"
fi

# ── Build images ──────────────────────────────────────────────────────────────
log "Building all custom images via docker compose..."
docker compose build --parallel

# ── Stop existing compose stack (if running) ─────────────────────────────────
log "Stopping existing docker compose stack..."
docker compose down --remove-orphans || true

# ── Deploy as Swarm stack ─────────────────────────────────────────────────────
log "Deploying Cemini stack via docker stack deploy..."
docker stack deploy -c docker-compose.yml "${STACK_NAME}"

# ── Wait and validate ─────────────────────────────────────────────────────────
log "Waiting 30s for services to start..."
sleep 30

log "Stack services:"
docker stack services "${STACK_NAME}"

log "Checking for unhealthy services..."
FAILED=$(docker stack ps "${STACK_NAME}" --filter "desired-state=running" --format '{{.CurrentState}}' \
    | grep -v "Running\|Starting" | wc -l)

if [[ "${FAILED}" -gt 0 ]]; then
    warn "${FAILED} service(s) not in Running state — check: docker stack ps ${STACK_NAME}"
else
    log "All services running."
fi

log "Portainer available at: http://<server-ip>/portainer/ (first run requires admin setup)"
log ""
log "To update CI to use stack deploy, change the 'Update Bot on Server' step in"
log ".github/workflows/deploy.yml from:"
log "  docker compose down && docker compose up --build -d"
log "to:"
log "  docker compose build && docker stack deploy -c docker-compose.yml cemini"
