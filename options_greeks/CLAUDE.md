# options_greeks — Service Overview (Step 23)

**What this does:** Pure-math options pricing and realized volatility library.
No Docker service — computation library called from the playbook runner.

## Module Map

| File | Purpose |
|------|---------|
| `black_scholes.py` | BS pricing + 5 closed-form Greeks (stdlib math only) |
| `implied_vol.py` | IV solver: Newton-Raphson → bisection fallback |
| `binary_greeks.py` | Cash-or-nothing binary Greeks (Kalshi complement) |
| `realized_vol.py` | Close-to-close, Parkinson, EWM vol + regime + beta |
| `vol_monitor.py` | DB reader + Intel Bus publisher (playbook integration) |

## Key Functions

```python
from options_greeks.black_scholes import bs_price, greeks
from options_greeks.implied_vol import implied_volatility
from options_greeks.binary_greeks import binary_greeks
from options_greeks.realized_vol import realized_vol, parkinson_vol, vol_regime, rolling_beta
from options_greeks.vol_monitor import run_vol_monitor

# Black-Scholes
price = bs_price(S=100, K=100, T=1.0, r=0.05, sigma=0.20, option_type="call")
g = greeks(100, 100, 1.0, 0.05, 0.20)  # dict: price, delta, gamma, theta, vega, rho

# Implied vol (Newton-Raphson + bisection)
iv = implied_volatility(market_price=10.45, S=100, K=100, T=1.0, r=0.05)

# Binary (Kalshi) Greeks
bg = binary_greeks(S=100, K=100, T=0.25, r=0.05, sigma=0.25)

# Realized vol from OHLCV closes (no DB — pass list of floats)
rv = realized_vol(closes=[100, 101, 99, 102, 98, ...])  # annualised decimal
pv = parkinson_vol(highs=[...], lows=[...])              # Parkinson estimator
regime = vol_regime(current_vol=0.25, lookback_vols=[0.20, 0.22, ...])  # LOW/NORMAL/HIGH
beta = rolling_beta(stock_closes=[...], spy_closes=[...])

# Vol surface monitor (called from playbook runner; needs active psycopg2 conn)
payload = run_vol_monitor(conn)
```

## Relationship to Other Modules

- **logit_pricing/**: Kalshi fair value via logit jump-diffusion. No standard BS.
  `options_greeks` adds sensitivity analysis (Greeks) for the same contracts.
- **trading_playbook/runner.py**: Calls `run_vol_monitor()` every 6th cycle (~30 min).
- **intel:vol_surface**: TTL=3600 — symbols, vol_regime, beta, approx_iv.
- **Step 22 (Alpaca OPRA)**: When activated, replace `approx_iv` with real IV from options chain.
- **Step 7 (RL)**: realized_vol + vol_regime + beta are high-value observation space features.

## No Dependencies Beyond Stdlib

All of `black_scholes.py`, `implied_vol.py`, `binary_greeks.py`, `realized_vol.py`
use only Python `math` and `statistics` stdlib modules. No scipy, no numpy.

`vol_monitor.py` imports from `core.intel_bus` (Redis) and `psycopg2` (Postgres).

## Known Limitations

- **approx_iv**: Beta-adjusted VIX proxy. Rough first-order approximation.
  Replace with real OPRA data when Step 22 activates.
- **raw_market_ticks**: If less than 21 days of ticks exist for a symbol, it is skipped.
- **Intraday Parkinson**: Current implementation uses 1-min OHLCV H/L from
  `raw_market_ticks`. True Parkinson uses daily H/L bars; 1-min H/L understates vol.
- **Binary theta sign**: Negative = binary call loses value as calendar time passes
  (standard convention for long options).
