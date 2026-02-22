# 🧠 QuantOS™ Intelligence & Architecture

This document outlines the high-level logic and decision-making frameworks that drive the QuantOS™ hybrid execution engine.

---

## 1. The Smart Selector (Instrument Decisioning)
QuantOS™ does not simply buy and sell; it strategically selects the instrument that offers the best risk-adjusted return for the current market state.

### **A. Instrument Routing**
- **Leveraged Attack (Options):** When the internal sentiment engine identifies a "High Conviction" state combined with favorable pricing, the bot utilizes derivative contracts to maximize capital efficiency.
- **Linear Growth (Equity):** In standard trending markets, the bot utilizes direct shares to avoid the complexities of time decay (Theta) and maintain a more stable delta.

### **B. The Volatility Guard**
The system continuously monitors Implied Volatility (IV) relative to historical norms. It is programmed to identify and avoid "Overcrowded Trades" where high IV makes options premiums mathematically unattractive, shifting focus to spot equity instead to avoid IV Crush.

### **C. Automated Hedging (The "Put" Protocol)**
In the event of a detected structural market breakdown or a break in key technical support levels, QuantOS™ can pivot to defensive instruments (Puts). This allows the system to remain resilient or even profit during high-velocity downward moves.

## 2. Institutional Execution (Anti-Manipulation)
QuantOS™ employs "Passive-Aggressive" execution to protect capital from predatory algorithms and market-maker front-running:
- **Mid-Point Logic:** Orders are placed at the Bid/Ask midpoint using Limit Orders rather than aggressive Market Orders.
- **Liquidity Filter:** The bot strictly avoids "Illiquid Traps"—contracts with wide spreads where slippage would significantly erode profit margins.

## 3. The Hybrid Data Layer
To ensure 100% dashboard uptime and decision-making continuity, QuantOS™ utilizes a tiered data approach:
1. **Primary:** Alpaca WebSocket Real-Time Stream (Direct Exchange Data).
2. **Failover:** Distributed public data endpoints (YFinance fallback) for view-only resilience during API interruptions.

## 4. Backtesting Engine (The Time Machine)
QuantOS™ includes a discrete-event simulator that allows for historical replay of OHLCV data. It calculates ROI, Drawdown, and Trade Frequency to validate strategies before live deployment.

---

## 5. The Intel Bus (Cross-System Intelligence Layer)

QuantOS™ participates in a shared Redis-backed signal bus (`core/intel_bus.py`) that enables real-time intelligence sharing with the Kalshi by Cemini module — without HTTP network calls between Docker containers.

All bus entries carry a structured payload: `{value, source_system, timestamp, confidence}`. Entries expire after **300 seconds (5 minutes)** to prevent stale signals from influencing decisions. All bus operations are **fail-silent** — a Redis failure is logged and swallowed, never crashing the parent process.

### Published Signals (QuantOS → Bus)

| Key | Publisher | Description |
| :--- | :--- | :--- |
| `intel:btc_volume_spike` | `CloudSignalEngine` | BTC volume anomaly detected in BigQuery real-time data |
| `intel:vix_level` | `Analyzer (Coach)` | VIX proxy derived from the Fear & Greed Index (range: 10–50) |
| `intel:spy_trend` | `Analyzer (Coach)` | Macro market bias: `bullish` / `bearish` / `neutral` |
| `intel:portfolio_heat` | `Analyzer (Coach)` | Combined position load across QuantOS + Kalshi (0.0 = empty, 1.0 = full) |

### Consumed Signals (Bus → QuantOS)

| Key | Consumer | Effect |
| :--- | :--- | :--- |
| `intel:fed_bias` | `TradingEngine` | +5% confidence score multiplier when bias is `dovish` |
| `intel:social_score` | `TradingEngine` | +3% confidence score multiplier when score > 0.3 |
| `intel:btc_volume_spike` | `MasterStrategyMatrix` | Adds a synthetic BTC spike entry if BigQuery has no BTC data |

### Signal Bus API

```python
from core.intel_bus import IntelPublisher, IntelReader

# Synchronous (use from threads / scripts)
IntelPublisher.publish("intel:my_key", value, source_system="MyModule", confidence=0.9)
payload = IntelReader.read("intel:my_key")  # returns dict or None

# Asynchronous (use from coroutines)
await IntelPublisher.publish_async("intel:my_key", value, source_system="MyModule")
payload = await IntelReader.read_async("intel:my_key")
```
