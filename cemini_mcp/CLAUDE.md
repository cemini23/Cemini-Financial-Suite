# cemini_mcp — MCP Intelligence Server

Read-only MCP server exposing the Cemini intel:* Redis bus as typed, callable tools.
FastMCP 3.1.0. Streamable-HTTP transport. Port 8002 (localhost only).

## Token Efficiency
Always use RTK (installed globally) to compress verbose CLI output before sending to context.
RTK reduces directory trees, error logs, git diffs, and JSON payloads by 60-90%.

## Architecture

- `server.py` — FastMCP tool definitions (9 tools, all read-only)
- `readers.py` — Redis GET wrappers with staleness detection + Postgres risk reader
- `config.py`  — Env var config (REDIS_HOST, REDIS_PASSWORD, MCP_PORT, etc.)

## Tools

| Tool | Source | Return |
|------|--------|--------|
| `get_regime_status` | intel:playbook_snapshot | RegimeSnapshot fields |
| `get_signal_detections` | intel:playbook_snapshot | latest signal dict |
| `get_risk_metrics` | Postgres playbook_logs | RiskAssessment fields |
| `get_playbook_snapshot` | intel:playbook_snapshot | raw IntelPayload |
| `get_kalshi_intel` | intel:kalshi_orderbook_summary | market summary |
| `get_geopolitical_risk` | GDELT intel keys | risk score + events |
| `get_sentiment` | multiple intel:* keys | cross-asset sentiment |
| `get_strategy_mode` | strategy_mode + intel:* | mode + supporting signals |
| `get_data_health` | all intel:* + Postgres | pipeline health dashboard |

## Key Rules

- All tools annotated destructive=False / readOnly=True
- Stale data flagged: stale=True + age_seconds in every response
- Risk data is NOT in Redis — readers.py queries Postgres playbook_logs
- strategy_mode and GDELT keys have TTL=-1 (persistent, no envelope)
- intel:* keys use IntelPayload envelope: {value, source_system, timestamp, confidence}

## Networks

- app_net (Redis access)
- data_net (Postgres access)

## Testing

```bash
cd /opt/cemini && python3 -m pytest cemini_mcp/tests/ -v
```

## Rebuild Required After

Any change to server.py or readers.py requires docker compose build cemini_mcp.
