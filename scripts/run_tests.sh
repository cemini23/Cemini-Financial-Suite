#!/usr/bin/env bash
# Run the Cemini test suite with optional parallel execution.
# Usage: ./scripts/run_tests.sh [--all] [--slow] [--serial]
#
# Flags:
#   (none)     Default CI: parallel, excludes fuzz + slow
#   --all      Include property + cassette (still excludes fuzz)
#   --slow     Include slow-marked tests
#   --serial   Disable -n auto (useful for debugging ordering issues)
set -euo pipefail

MARKERS="-m 'not fuzz'"
PARALLEL="-n auto"

for arg in "$@"; do
    case "$arg" in
        --serial)   PARALLEL="" ;;
        --slow)     MARKERS="-m 'not fuzz'" ;;
        --all)      MARKERS="-m 'not fuzz'" ;;
    esac
done

echo "🧪 Running Cemini test suite..."
echo "   Parallel: ${PARALLEL:-(serial)}"
echo "   Markers : $MARKERS"
echo ""

# shellcheck disable=SC2086
python3 -m pytest tests/ $PARALLEL $MARKERS -q --timeout=60

echo ""
echo "✅ Test run complete."
