#!/usr/bin/env bash
# =============================================================================
# Cemini Financial Suite — Semgrep Security Scanner (Step 34e)
# Runs 4 custom trading-specific rules + Trail of Bits baseline.
#
# Usage:
#   ./scripts/semgrep-scan.sh              # custom rules + Trail of Bits
#   ./scripts/semgrep-scan.sh --custom     # custom rules only (faster)
#   ./scripts/semgrep-scan.sh --tob        # Trail of Bits only
#   ./scripts/semgrep-scan.sh --sarif      # output SARIF to semgrep.sarif
#
# Prerequisites: pip install semgrep
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="${REPO_ROOT}/reports/semgrep"
mkdir -p "${REPORT_DIR}"

log() { echo "[semgrep-scan] $*"; }

check_semgrep() {
    if ! command -v semgrep &>/dev/null; then
        echo "ERROR: semgrep not found. Install with: pip install semgrep"
        exit 1
    fi
    log "semgrep version: $(semgrep --version)"
}

run_scan() {
    local config_args=("$@")
    semgrep scan \
        "${config_args[@]}" \
        --metrics=off \
        "${REPO_ROOT}"
}

# ── Main ─────────────────────────────────────────────────────────────────────
check_semgrep

case "${1:---all}" in
    --custom)
        log "Running custom trading rules only..."
        run_scan --config "${REPO_ROOT}/.semgrep/"
        ;;
    --tob)
        log "Running Trail of Bits rules only..."
        run_scan --config p/trailofbits
        ;;
    --sarif)
        log "Running full scan with SARIF output..."
        run_scan \
            --config "${REPO_ROOT}/.semgrep/" \
            --config p/trailofbits \
            --sarif \
            -o "${REPORT_DIR}/semgrep.sarif"
        log "SARIF report: ${REPORT_DIR}/semgrep.sarif"
        ;;
    --all|-*)
        log "Running custom rules + Trail of Bits..."
        run_scan \
            --config "${REPO_ROOT}/.semgrep/" \
            --config p/trailofbits
        ;;
esac

log "Done."
