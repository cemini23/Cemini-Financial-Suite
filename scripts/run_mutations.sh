#!/usr/bin/env bash
# Run mutation testing on critical trading logic modules.
# Usage: ./scripts/run_mutations.sh [module]
#
# Examples:
#   ./scripts/run_mutations.sh                        # all targets
#   ./scripts/run_mutations.sh risk_engine            # single module
#
# Results:
#   mutmut results         — summary table
#   mutmut show <id>       — inspect a surviving mutant
#   mutmut junitxml        — JUnit XML (CI integration)
#
# Target: >= 80% mutation score on each module.
# Runtime: 10-30 min depending on module size.
set -euo pipefail

MODULE=${1:-all}

TARGETS="trading_playbook/risk_engine.py,trading_playbook/macro_regime.py,core/intel_bus.py"

if [[ "$MODULE" == "risk_engine" ]]; then
    TARGETS="trading_playbook/risk_engine.py"
elif [[ "$MODULE" == "macro_regime" ]]; then
    TARGETS="trading_playbook/macro_regime.py"
elif [[ "$MODULE" == "fred_monitor" ]]; then
    TARGETS="scrapers/fred_monitor.py"
fi

echo "🧬 Mutation testing: $TARGETS"
echo "   (This may take 10-30 minutes)"
echo ""

mutmut run \
    --paths-to-mutate="$TARGETS" \
    --tests-dir=tests/ \
    --runner="python3 -m pytest tests/ -x -q --timeout=10 -m 'not fuzz'" \
    || true

echo ""
echo "📊 Results summary:"
mutmut results 2>/dev/null || echo "(run 'mutmut results' for detailed output)"

echo ""
echo "📄 Generating JUnit XML report..."
mutmut junitxml 2>/dev/null > tests/mutation_report.xml && \
    echo "   → tests/mutation_report.xml" || \
    echo "   (JUnit XML generation skipped)"

echo ""
echo "✅ Mutation run complete."
echo "   View surviving mutants: mutmut results | grep 'survived'"
echo "   Inspect a mutant: mutmut show <id>"
