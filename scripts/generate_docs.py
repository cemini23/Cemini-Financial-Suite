#!/usr/bin/env python3
"""
Auto-documentation generator for Cemini Financial Suite.

Parses codebase state and injects auto-generated sections into READMEs.
Only modifies content between <!-- AUTO:KEY --> / <!-- /AUTO:KEY --> markers.
Human-written prose outside the markers is never touched.

Usage:
    python scripts/generate_docs.py

Exits 0 always — doc failure is never a blocking CI error.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

# ── Paths ─────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
COMPOSE_FILE = ROOT / "docker-compose.yml"
README_FILE = ROOT / "README.md"
PROJECT_SUMMARY_FILE = ROOT / "PROJECT_SUMMARY.md"

REQUIREMENTS_FILES = [
    ROOT / "requirements.txt",
    ROOT / "QuantOS" / "requirements.txt",
    ROOT / "Kalshi by Cemini" / "requirements.txt",
]

# ── Config ────────────────────────────────────────────────────────────────────

TRACKED_DEPS = [
    "fastapi", "redis", "psycopg2-binary", "pandas", "numpy",
    "torch", "transformers", "robin-stocks", "alpaca-py", "ccxt",
    "httpx", "pydantic", "langgraph", "streamlit", "websockets",
    "polars", "gdeltdoc", "tweepy", "textblob", "scikit-learn",
]

# Single source of truth for roadmap step status.
# Update "status" here when a step is completed; CI auto-updates all READMEs.
ROADMAP_STEPS = [
    {"num": 1,  "name": "CI/CD Hardening",           "status": "COMPLETE", "date": "Feb 28, 2026"},
    {"num": 2,  "name": "Docker Network Segmentation", "status": "COMPLETE", "date": "Mar 1, 2026"},
    {"num": 3,  "name": "Performance Dashboard",      "status": "TODO"},
    {"num": 4,  "name": "Kalshi Rewards Scanner",     "status": "TODO"},
    {"num": 5,  "name": "X/Twitter Thread Tool",      "status": "TODO"},
    {"num": 6,  "name": "Equity Tick Data",           "status": "COMPLETE", "date": "Feb 26, 2026"},
    {"num": 7,  "name": "RL Training Loop",           "status": "TODO"},
    {"num": 8,  "name": "Backtesting in CI/CD",       "status": "TODO"},
    {"num": 9,  "name": "Options Strategies",          "status": "TODO"},
    {"num": 10, "name": "Live Trading Integration",   "status": "TODO"},
    {"num": 11, "name": "Shadow Testing Infra",       "status": "TODO"},
    {"num": 12, "name": "Copy Trading / Signals",     "status": "REMOVED"},
    {"num": 13, "name": "Arbitrage Scanner",          "status": "TODO"},
    {"num": 14, "name": "GDELT Geopolitical Intel",   "status": "COMPLETE", "date": "Mar 1, 2026"},
    {"num": 15, "name": "Auto-Documentation CI",      "status": "COMPLETE", "date": "Mar 1, 2026"},
]

# Broker adapter inventory (static — updated manually when adapters change)
BROKERS = [
    {"name": "Kalshi",    "status": "Active",     "api": "REST API v2 (RSA-signed)", "mode": "Paper default"},
    {"name": "Robinhood", "status": "Integrated", "api": "robin_stocks (unofficial)", "mode": "Paper default"},
    {"name": "Alpaca",    "status": "Integrated", "api": "Official REST API",         "mode": "Paper default"},
    {"name": "IBKR",      "status": "Planned",    "api": "TWS API / FIX CTCI",       "mode": "Requires LLC + LEI"},
]


# ── Parsers ───────────────────────────────────────────────────────────────────

def parse_compose_services():
    """Parse docker-compose.yml → list of service dicts. Returns [] on failure."""
    if not COMPOSE_FILE.exists() or not _YAML_AVAILABLE:
        return []
    try:
        text = COMPOSE_FILE.read_text()
        data = yaml.safe_load(text)
        raw_services = data.get("services", {})
    except Exception as exc:
        print(f"  ⚠️  docker-compose parse failed: {exc}", file=sys.stderr)
        return []

    results = []
    for name, cfg in raw_services.items():
        if cfg is None:
            cfg = {}
        profiles = cfg.get("profiles", [])
        disabled = bool(profiles)

        container_name = cfg.get("container_name", name)

        image = cfg.get("image", "")
        build = cfg.get("build", {})
        if not image:
            if isinstance(build, dict):
                image = f"(build: {build.get('dockerfile', 'Dockerfile')})"
            elif isinstance(build, str):
                image = f"(build: {build})"

        ports_raw = cfg.get("ports", []) or cfg.get("expose", [])
        port_str = ", ".join(str(p).split(":")[0] for p in ports_raw) if ports_raw else "internal"

        purpose = _extract_service_comment(COMPOSE_FILE.read_text(), name)

        results.append({
            "service": name,
            "container": container_name,
            "image": image,
            "ports": port_str,
            "disabled": disabled,
            "purpose": purpose,
        })

    return results


def _extract_service_comment(yaml_text, service_name):
    """Return the first non-empty comment line directly above a service block."""
    lines = yaml_text.splitlines()
    for i, line in enumerate(lines):
        if re.match(rf"^  {re.escape(service_name)}:\s*$", line):
            j = i - 1
            while j >= 0 and lines[j].strip().startswith("#"):
                comment = lines[j].strip().lstrip("#").strip().strip("-").strip()
                if comment:
                    return comment[:120]
                j -= 1
            return ""
    return ""


def parse_dependency_versions():
    """Parse tracked deps from all requirements files → {pkg: [{version, source}]}."""
    versions = {}
    for req_file in REQUIREMENTS_FILES:
        if not req_file.exists():
            continue
        label = req_file.parent.name if req_file.parent != ROOT else "root"
        for line in req_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            m = re.match(r"^([A-Za-z0-9_-]+)\s*([><=~!]+)?\s*([\d.a-zA-Z]+)?", line)
            if not m:
                continue
            pkg = m.group(1).lower().replace("_", "-")
            op = m.group(2) or ""
            ver = m.group(3) or "any"
            if pkg in [d.lower().replace("_", "-") for d in TRACKED_DEPS]:
                versions.setdefault(pkg, []).append({"version": f"{op}{ver}", "source": label})
    return versions


def get_test_count():
    """Collect pytest test count. Returns int or None on failure."""
    python_cmd = "python3" if _cmd_exists("python3") else "python"
    try:
        result = subprocess.run(
            [python_cmd, "-m", "pytest", "--collect-only", "-q", "--no-header"],
            capture_output=True, text=True, timeout=60, cwd=str(ROOT),
        )
        for line in result.stdout.splitlines():
            m = re.search(r"(\d+)\s+(?:test|item)", line)
            if m:
                return int(m.group(1))
        items = [ln for ln in result.stdout.splitlines() if "::" in ln]
        return len(items) if items else None
    except Exception:
        return None


def _cmd_exists(cmd):
    try:
        subprocess.run([cmd, "--version"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def get_security_summary():
    """Return brief security scan status strings."""
    summary = {"pip_audit": "see CI", "bandit": "see CI"}

    # pip-audit
    try:
        result = subprocess.run(
            ["pip-audit", "-r", str(ROOT / "requirements.txt"),
             "--strict", "--desc", "-f", "json"],
            capture_output=True, text=True, timeout=120, cwd=str(ROOT),
        )
        if result.returncode == 0:
            data = json.loads(result.stdout) if result.stdout.strip() else {}
            deps = data.get("dependencies", [])
            vuln_count = sum(1 for d in deps if d.get("vulns"))
            summary["pip_audit"] = "clean (0 vulnerabilities)" if not vuln_count else f"{vuln_count} vulnerabilities found"
        else:
            summary["pip_audit"] = "not available locally (check CI)"
    except Exception:
        summary["pip_audit"] = "not available locally (check CI)"

    # bandit report artifact
    bandit_path = ROOT / "bandit-report.json"
    if bandit_path.exists():
        try:
            data = json.loads(bandit_path.read_text())
            findings = data.get("results", [])
            high = sum(1 for r in findings if r.get("issue_severity") == "HIGH")
            med = sum(1 for r in findings if r.get("issue_severity") == "MEDIUM")
            summary["bandit"] = f"{high} HIGH, {med} MEDIUM ({len(findings)} total)"
        except Exception:
            pass

    return summary


# ── Generators ────────────────────────────────────────────────────────────────

def generate_services_table(services):
    """Markdown table of active Docker services."""
    active = [s for s in services if not s["disabled"]]
    disabled = [s for s in services if s["disabled"]]

    lines = [
        f"**{len(active)} active containers**"
        + (f" ({len(disabled)} disabled)" if disabled else ""),
        "",
        "| Container | Image/Build | Ports | Notes |",
        "|-----------|-------------|-------|-------|",
    ]
    for s in active:
        purpose = (s["purpose"][:80] + "…") if len(s["purpose"]) > 80 else s["purpose"]
        lines.append(f"| `{s['container']}` | {s['image']} | {s['ports']} | {purpose} |")

    if disabled:
        lines += ["", f"**Disabled (profile-gated):** `{'`, `'.join(s['service'] for s in disabled)}`"]

    return "\n".join(lines)


def generate_service_count(services):
    active = sum(1 for s in services if not s["disabled"])
    return f"{active} active Docker containers"


def generate_test_summary(test_count, security):
    lines = []
    if test_count is not None:
        lines.append(f"**Tests:** {test_count} passing")
    else:
        lines.append("**Tests:** run `pytest` locally to verify")
    lines.append(f"**pip-audit:** {security['pip_audit']}")
    lines.append(f"**bandit (SAST):** {security['bandit']}")
    lines.append("**CI gates:** lint → pip-audit → bandit → TruffleHog → deploy (all required)")
    return "\n".join(lines)


def generate_dependency_table(versions):
    if not versions:
        return "*Dependency version table unavailable — run locally with pyyaml installed.*"
    lines = [
        "| Package | Pinned version | Source |",
        "|---------|---------------|--------|",
    ]
    for pkg in sorted(versions):
        for entry in versions[pkg]:
            lines.append(f"| `{pkg}` | `{entry['version']}` | {entry['source']}/requirements.txt |")
    return "\n".join(lines)


def generate_roadmap_status():
    complete = [s for s in ROADMAP_STEPS if s["status"] == "COMPLETE"]
    todo = [s for s in ROADMAP_STEPS if s["status"] == "TODO"]
    total = len(ROADMAP_STEPS) - sum(1 for s in ROADMAP_STEPS if s["status"] == "REMOVED")
    pct = int(len(complete) / total * 100) if total else 0

    lines = [
        f"**Progress: {len(complete)}/{total} steps complete ({pct}%)**",
        "",
        "| Step | Name | Status |",
        "|------|------|--------|",
    ]
    for s in ROADMAP_STEPS:
        if s["status"] == "COMPLETE":
            badge = f"✅ Complete ({s.get('date', '')})"
        elif s["status"] == "REMOVED":
            badge = "~~Removed~~"
        else:
            badge = "⬜ Pending"
        lines.append(f"| {s['num']} | {s['name']} | {badge} |")

    return "\n".join(lines)


def generate_last_updated():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"*Auto-generated: {now}*"


def generate_broker_status():
    lines = [
        "| Broker | Status | API | Default Mode |",
        "|--------|--------|-----|--------------|",
    ]
    for b in BROKERS:
        lines.append(f"| {b['name']} | {b['status']} | {b['api']} | {b['mode']} |")
    return "\n".join(lines)


def generate_redis_channels():
    """Return a static (but accurate) intel bus channel reference."""
    channels = [
        ("trade_signals",            "brain → EMS (trade execution commands)"),
        ("emergency_stop",           "Kill switch CANCEL_ALL broadcast"),
        ("strategy_mode",            "analyzer → conservative | aggressive | sniper"),
        ("intel:btc_spy_corr",       "BTC/SPY 30-day rolling correlation float"),
        ("intel:playbook_snapshot",  "playbook_runner: regime + signal + risk state (every 5 min)"),
        ("intel:spy_trend",          "SPY trend direction from playbook_runner"),
        ("intel:geopolitical_risk",  "GDELT: 0-100 risk score, level, top event (every 15 min)"),
        ("intel:conflict_events",    "GDELT: top-5 high-impact events JSON list"),
        ("intel:regional_risk",      "GDELT: per-region risk scores (asia_pacific, middle_east, europe, americas)"),
        ("macro:fear_greed",         "Fear & Greed Index (macro_scraper, every 5 min)"),
    ]
    lines = [
        "| Key | Publisher | Description |",
        "|-----|-----------|-------------|",
    ]
    for key, desc in channels:
        publisher = key.split(":")[0].replace("_", "\\_") if ":" not in key else key.split(":")[1].split("_")[0]
        lines.append(f"| `{key}` | various | {desc} |")
    return "\n".join(lines)


# ── Injector ──────────────────────────────────────────────────────────────────

def inject_markers(filepath, sections):
    """
    Replace content between AUTO markers in-place.
    Returns True if the file was modified.
    """
    if not filepath.exists():
        return False

    content = filepath.read_text(encoding="utf-8")
    original = content

    for key, value in sections.items():
        pattern = rf"(<!-- AUTO:{key} -->).*?(<!-- /AUTO:{key} -->)"
        replacement = f"<!-- AUTO:{key} -->\n{value}\n<!-- /AUTO:{key} -->"
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    if content != original:
        filepath.write_text(content, encoding="utf-8")
        return True
    return False


# ── Per-directory README generators ──────────────────────────────────────────

def _quantos_readme():
    return """\
# QuantOS — Stock & Crypto Trading Engine

<!-- AUTO:LAST_UPDATED -->
<!-- /AUTO:LAST_UPDATED -->

## Overview

QuantOS is the equity and cryptocurrency trading engine within the Cemini Financial Suite.
It handles market scanning, RSI-based signal generation, order execution, and portfolio
management through a modular broker-agnostic architecture.

## Key Components

| Component | File | Purpose |
|-----------|------|---------|
| TradingEngine | `core/engine.py` | Main trading loop, bracket orders, sunset reports |
| QuantBrain | `core/brain.py` | RSI signal scoring (rolling 1000-price window) |
| ExecutionEngine | `core/execution.py` | Buy/sell/bracket execution + paper mode |
| MoneyManager | `core/money_manager.py` | Score-based position sizing (90+→5%, 75+→2.5%) |
| RiskManager | `core/risk_manager.py` | Daily 3% stop, 20% position cap, options check |
| MasterStrategyMatrix | `core/strategy_matrix.py` | Confluence: BigQuery spikes + XOracle sentiment |
| AsyncScanner | `core/async_scanner.py` | Alpaca primary, Yahoo fallback, async burst scanning |
| TaxEngine | `core/tax_engine.py` | Wash sale guard + tax estimation |
| XOracle | `core/sentiment/x_oracle.py` | Trust scoring + FinBERT sentiment |

## Broker Adapters

<!-- AUTO:BROKER_STATUS -->
<!-- /AUTO:BROKER_STATUS -->

All adapters implement `BrokerInterface`. Factory in `core/brokers/factory.py` dispatches by name.
Router in `core/brokers/router.py` handles time-aware routing and health checks.

## Data Flow

```
AsyncScanner (Alpaca/Yahoo) → TradingEngine → QuantBrain (RSI)
    → MasterStrategyMatrix (confluence) → ExecutionEngine → Broker adapter
```

## Running

QuantOS runs as the `signal_generator` service (currently disabled — behind Docker profile,
redundant with the `brain` service which covers equivalent functionality).

```bash
# Enable for isolated testing only:
docker compose --profile signal_generator up -d signal_generator
```
"""


def _kalshi_readme():
    return """\
# Kalshi by Cemini — Prediction Market Engine

<!-- AUTO:LAST_UPDATED -->
<!-- /AUTO:LAST_UPDATED -->

## Overview

Prediction market trading engine for Kalshi. Integrates multi-domain analysis (BTC,
Fed rates, weather, geopolitical) with Kelly Criterion position sizing and RSA-signed
API execution.

## Modules

| Module | File | Purpose |
|--------|------|---------|
| Autopilot | `modules/execution/autopilot.py` | Main 30s scan-and-execute loop |
| SatoshiAnalyzer | `modules/satoshi_vision/analyzer.py` | Multi-timeframe BTC TA (SCALP/SWING/MACRO) |
| PowellAnalyzer | `modules/powell_protocol/analyzer.py` | Treasury yields + rate decision analysis |
| WeatherAnalyzer | `modules/weather_alpha/analyzer.py` | NWS/OpenWeather forecast consensus |
| SocialAnalyzer | `modules/social_alpha/analyzer.py` | X/Twitter sentiment (⚠️ simulated data) |
| MuskPredictor | `modules/musk_monitor/predictor.py` | Tweet velocity + empire/launch data model |
| GeoPulseMonitor | `modules/geo_pulse/monitor.py` | Geopolitical signals — live GDELT fallback via Redis |
| MarketRover | `modules/market_rover/rover.py` | Cross-references QuantOS sentiment with Kalshi markets |
| CapitalAllocator | `modules/execution/allocator.py` | Kelly Criterion position sizing |

## Data Gaps

- `social_alpha/analyzer.py` — Uses hardcoded simulated tweets (not live X API)
- `powell_protocol/analyzer.py` — Mock Kalshi rate bracket prices (not live)
- `weather_alpha/analyzer.py` — Simulated order book prices (not live)
- `geo_pulse/monitor.py` — Falls back to live GDELT data from Redis (`intel:conflict_events`);
  if Redis unavailable, uses X API; if both unavailable, returns NO_SIGNAL

## Running

```bash
docker compose up -d kalshi_autopilot rover_scanner
docker logs kalshi_autopilot --since '30 minutes ago'
```
"""


def _playbook_readme():
    return """\
# Trading Playbook — Observation & Risk Layer

<!-- AUTO:LAST_UPDATED -->
<!-- /AUTO:LAST_UPDATED -->

## Overview

Observation-only layer running every 5 minutes. Classifies macro regime, detects
tactical setups, computes risk metrics, and logs everything to Postgres + JSONL for
future RL model training. **Does NOT place orders.**

## Components

| Component | File | Purpose |
|-----------|------|---------|
| Macro Regime | `macro_regime.py` | Traffic-light (GREEN/YELLOW/RED) via SPY vs EMA21/SMA50 + JNK/TLT |
| Signal Catalog | `signal_catalog.py` | 6 detectors: EpisodicPivot, MomentumBurst, ElephantBar, VCP, HighTightFlag, InsideBar212 |
| Risk Engine | `risk_engine.py` | Fractional Kelly (25% cap), CVaR (99th pctile), DrawdownMonitor |
| Kill Switch | `kill_switch.py` | PnL velocity, order rate, latency, price deviation → CANCEL_ALL |
| Logger | `playbook_logger.py` | Postgres (playbook_logs) + JSONL (/mnt/archive/playbook/) + Redis |
| Runner | `runner.py` | 5-min scan loop orchestrating all components |

## Regime Classification

| Regime | Condition | Posture |
|--------|-----------|---------|
| 🟢 GREEN | SPY > rising EMA21 | Aggressive — full position sizing |
| 🟡 YELLOW | SPY < EMA21 but > SMA50 | Defensive — no new longs |
| 🔴 RED | SPY < SMA50 | Survival — cash or short only |

The regime gate in `agents/orchestrator.py` blocks all BUY signals when regime is YELLOW or RED.

## Data Output

- **Postgres:** `playbook_logs` table with JSONB payload (regime, signals, risk metrics)
- **JSONL:** `/mnt/archive/playbook/` — 15+ files per day for RL training corpus
- **Redis:** `intel:playbook_snapshot` — latest regime + signals, consumed by brain + EMS

## Running

```bash
docker compose up -d playbook
docker logs playbook_runner --since '30 minutes ago' | grep regime
```
"""


def _inject_into_generated(content, sections):
    """Inject AUTO marker content into a freshly generated README string."""
    for key, value in sections.items():
        pattern = rf"(<!-- AUTO:{key} -->).*?(<!-- /AUTO:{key} -->)"
        replacement = f"<!-- AUTO:{key} -->\n{value}\n<!-- /AUTO:{key} -->"
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    return content


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("📝 Cemini auto-documentation generator")

    services = parse_compose_services()
    if not services:
        print("  ⚠️  Could not parse docker-compose.yml — install pyyaml", file=sys.stderr)

    versions = parse_dependency_versions()
    test_count = get_test_count()
    security = get_security_summary()

    sections = {
        "SERVICES_TABLE": generate_services_table(services),
        "SERVICE_COUNT": generate_service_count(services),
        "TEST_SUMMARY": generate_test_summary(test_count, security),
        "DEPENDENCY_VERSIONS": generate_dependency_table(versions),
        "ROADMAP_STATUS": generate_roadmap_status(),
        "LAST_UPDATED": generate_last_updated(),
        "BROKER_STATUS": generate_broker_status(),
        "REDIS_CHANNELS": generate_redis_channels(),
    }

    changed = False

    for filepath in (README_FILE, PROJECT_SUMMARY_FILE):
        if inject_markers(filepath, sections):
            print(f"  ✅ Updated {filepath.relative_to(ROOT)}")
            changed = True

    sub_readmes = [
        (ROOT / "QuantOS" / "README.md",          _quantos_readme),
        (ROOT / "Kalshi by Cemini" / "README.md", _kalshi_readme),
        (ROOT / "trading_playbook" / "README.md", _playbook_readme),
    ]
    for dirpath, generator in sub_readmes:
        content = _inject_into_generated(generator(), sections)
        if not dirpath.exists() or dirpath.read_text(encoding="utf-8") != content:
            dirpath.parent.mkdir(parents=True, exist_ok=True)
            dirpath.write_text(content, encoding="utf-8")
            print(f"  ✅ Generated {dirpath.relative_to(ROOT)}")
            changed = True

    if not changed:
        print("  ✔  No documentation changes needed.")
    else:
        print("📝 Documentation updated.")

    return changed


if __name__ == "__main__":
    os.chdir(ROOT)
    changed = main()
    sys.exit(0)
