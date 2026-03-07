#!/usr/bin/env bash
# =============================================================================
# Cemini Financial Suite — Trivy Security Scanner (Step 34d)
# Run locally on the VPS server where Docker images are built.
#
# Usage:
#   ./scripts/trivy-scan.sh              # scan all images + filesystem
#   ./scripts/trivy-scan.sh --fs-only    # filesystem scan only
#   ./scripts/trivy-scan.sh --image <n>  # scan a specific image by name
#
# Prerequisites: trivy installed (https://aquasecurity.github.io/trivy/)
#   curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="${REPO_ROOT}/reports/trivy"
mkdir -p "${REPORT_DIR}"

SEVERITY="HIGH,CRITICAL"
EXIT_CODE_CRITICAL=1   # fail on CRITICAL; HIGH warns but does not fail

# Custom images built by Cemini (from Dockerfile.* at repo root)
CUSTOM_IMAGES=(
    "cemini-brain"
    "cemini-ems"
    "cemini-playbook"
    "cemini-ui"
    "cemini-autopilot"
    "cemini-ingestor"
    "cemini-scraper"
    "cemini-logger"
    "cemini-analyzer"
)

log() { echo "[trivy-scan] $*"; }

check_trivy() {
    if ! command -v trivy &>/dev/null; then
        echo "ERROR: trivy not found. Install with:"
        echo "  curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin"
        exit 1
    fi
    log "trivy version: $(trivy --version | head -1)"
}

scan_filesystem() {
    log "Scanning filesystem for misconfigs, secrets, and vuln packages..."
    trivy fs \
        --severity "${SEVERITY}" \
        --format sarif \
        --output "${REPORT_DIR}/fs-scan.sarif" \
        --exit-code 0 \
        "${REPO_ROOT}"
    trivy fs \
        --severity "${SEVERITY}" \
        --format table \
        "${REPO_ROOT}"
    log "FS SARIF report: ${REPORT_DIR}/fs-scan.sarif"
}

scan_image() {
    local image="$1"
    local tag="${2:-latest}"
    local full="${image}:${tag}"
    local safe_name="${image//\//_}"

    # Check image exists locally
    if ! docker image inspect "${full}" &>/dev/null 2>&1; then
        log "SKIP: image ${full} not found locally (not built yet)"
        return 0
    fi

    log "Scanning image: ${full}"
    trivy image \
        --severity "${SEVERITY}" \
        --format sarif \
        --output "${REPORT_DIR}/image-${safe_name}.sarif" \
        --exit-code 0 \
        "${full}"

    # Second pass: exit 1 on CRITICAL only
    trivy image \
        --severity "CRITICAL" \
        --format table \
        --exit-code "${EXIT_CODE_CRITICAL}" \
        "${full}" || {
            log "CRITICAL vulnerabilities found in ${full} — review required"
            return 1
        }
    log "Image ${full}: no CRITICAL CVEs"
}

scan_all_images() {
    local failed=0
    for image in "${CUSTOM_IMAGES[@]}"; do
        scan_image "${image}" || failed=$((failed + 1))
    done
    if [[ ${failed} -gt 0 ]]; then
        log "WARNING: ${failed} image(s) have CRITICAL CVEs — see reports in ${REPORT_DIR}/"
        return 1
    fi
    log "All images: no CRITICAL CVEs"
}

# ── Main ─────────────────────────────────────────────────────────────────────
check_trivy

case "${1:-all}" in
    --fs-only)
        scan_filesystem
        ;;
    --image)
        shift
        scan_image "${1}"
        ;;
    all)
        scan_filesystem
        scan_all_images
        ;;
    *)
        echo "Usage: $0 [--fs-only | --image <name> | all]"
        exit 1
        ;;
esac

log "Done. SARIF reports written to ${REPORT_DIR}/"
