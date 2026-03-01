# QuantOS — Stock & Crypto Trading Engine

<!-- AUTO:LAST_UPDATED -->
*Auto-generated: 2026-03-01 20:30 UTC*
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
| Broker | Status | API | Default Mode |
|--------|--------|-----|--------------|
| Kalshi | Active | REST API v2 (RSA-signed) | Paper default |
| Robinhood | Integrated | robin_stocks (unofficial) | Paper default |
| Alpaca | Integrated | Official REST API | Paper default |
| IBKR | Planned | TWS API / FIX CTCI | Requires LLC + LEI |
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
