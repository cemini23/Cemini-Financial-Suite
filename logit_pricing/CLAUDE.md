# logit_pricing — Logit-Space Contract Pricing Library

Shaw & Dalen (2025) Logit Jump-Diffusion framework for Kalshi binary contracts.
Shared library — imported by autopilot, rover_scanner, and cemini_mcp.

## Token Efficiency
Always use RTK (installed globally) to compress verbose CLI output before sending to context.
RTK reduces directory trees, error logs, git diffs, and JSON payloads by 60-90%.

## Architecture

| Module | Role |
|--------|------|
| `transforms.py` | logit/inv_logit/logit_array — core math, all clamp-safe |
| `indicators.py` | logit-space SMA, EMA, Bollinger, Wilder RSI, mean-reversion score |
| `jump_diffusion.py` | Jump detection, regime classification, time-decay, fair value |
| `precision.py` | assert_finite, safe_divide, multiply_before_divide, clamp_probability |
| `pricing_engine.py` | LogitPricingEngine.assess_contract() → ContractAssessment |
| `models.py` | ContractAssessment Pydantic model |

## Key Rules

- RSI uses Wilder's SMMA (alpha=1/period), NOT SMA — see LESSONS.md
- Multiplication-before-division ordering in all Decimal calculations
- assert_finite() after every pricing output — never let NaN/Inf escape
- P_MIN=0.001, P_MAX=0.999 — clamp all input probabilities before logit
- JUMP_MIN_ABS_LOGIT=0.20 — absolute minimum for jump detection (prevents constant-delta false positives)
- LOGIT_EXIT_SENSITIVITY env var (default 1.0) controls exit σ threshold

## Integration Points

- SatoshiAnalyzer: 70/30 blend (existing score + logit mispricing)
- Exit engine: logit_exit_signal() fires before 90¢ TP / 10¢ SL backstops
- MCP server: get_contract_pricing() tool reads intel:logit_assessments
- rover_scanner: enriches intel:kalshi_orderbook_summary with assessments

## Testing

```bash
cd /opt/cemini && PYTHONPATH=/opt/cemini python3 -m pytest logit_pricing/tests/ -v
```
