# shared/safety — Pre-Live Safety Hardening (Step 49)

Seven defense-in-depth safety modules that wrap every live order path.
All modules are fail-safe by default: unknown state → block the order.

## Modules

| File | Class | Purpose |
|------|-------|---------|
| `idempotency.py` | `IdempotencyGuard` | Redis SET NX dedup — prevents double-fills on retry |
| `state_hydrator.py` | `StateHydrator` | Loads executed_trades + positions on engine restart (L1 fix) |
| `exposure_gate.py` | `ExposureGate` | Hard-blocks per-ticker over-exposure (C6/L2 fix) |
| `hitl_gate.py` | `HITLGate` | Human-in-the-loop approval queue — auto-rejects at timeout |
| `mfa_handler.py` | `MFAHandler` | Robinhood TOTP via pyotp |
| `self_match_lock.py` | `SelfMatchLock` | Kalshi self-match prevention (CFTC) |

## Redis key namespace

```
idempotency:order:{sha256[:16]}   TTL 86400s
safety:exposure:{ticker}          TTL 86400s (daily reset)
safety:hitl:pending               LIST — pending approvals
safety:hitl:decision:{id}         TTL = HITL_TIMEOUT_SECONDS (default 300)
safety:self_match:{market_id}     TTL 3600s
```

## Env vars

| Var | Default | Notes |
|-----|---------|-------|
| `LIVE_TRADING` | `false` | Enable live broker queries in ExposureGate |
| `HITL_TIMEOUT_SECONDS` | `300` | Auto-reject window |
| `HITL_CONFIDENCE_FLOOR` | `0.85` | Signals at/above this trigger HITL |
| `DISCORD_WEBHOOK_URL` | `` | Optional — HITL alert channel |
| `ROBINHOOD_MFA_SECRET` | `` | Base-32 TOTP secret |

## Known Pitfalls

- **ExposureGate fail-closed**: if `LIVE_TRADING=true` and `buying_power` is not
  passed explicitly, the gate returns 0 and blocks the order. This is intentional.
- **IdempotencyGuard is fail-open**: if Redis is down, orders are allowed through
  (availability > safety for the idempotency layer; ExposureGate is the hard stop).
- **HITLGate blocks the calling thread** during `wait_for_decision()`. Do not call
  from an async context without wrapping in `asyncio.to_thread()`.
- **SelfMatchLock only prevents YES↔NO conflicts**, not duplicate YES orders.
  Position sizing is handled by ExposureGate.
- **pyotp is optional**: if not installed, MFAHandler returns None codes and logs a
  warning. Install with `pip install pyotp`.
