"""mutmut configuration for Cemini Financial Suite (Step 42c).

Targeted mutation testing: only mutates high-value trading logic modules
to keep runtime reasonable (full codebase would take hours).

Usage:
    mutmut run --paths-to-mutate="trading_playbook/risk_engine.py"
    mutmut results
    mutmut show <id>
    ./scripts/run_mutations.sh

Target mutation score: >= 80% on listed modules.
"""


def pre_mutation(context):
    """Skip mutations on non-critical code to keep runtime practical."""
    # Only mutate high-value modules with clear invariants
    _allowed = [
        "trading_playbook/risk_engine.py",
        "trading_playbook/macro_regime.py",
        "trading_playbook/signal_catalog.py",
        "trading_playbook/kill_switch.py",
        "core/intel_bus.py",
        "scrapers/fred_monitor.py",
    ]
    if not any(p in (context.filename or "") for p in _allowed):
        context.skip = True
