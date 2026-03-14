# UI — Performance Dashboard (Step 3)

Streamlit-based trading performance dashboard accessible via cemini_os on port 8501.

## Files

- `performance.py` — main Streamlit app; 5 tabs (Regime / Signals / P&L / Risk / Health)
- `dashboard.py` — legacy dashboard (superseded by performance.py)
- `app.py` — thin launcher
- `Dockerfile.ui` — builds the Streamlit container

## Tabs

| Tab | Data source |
|-----|------------|
| Regime | `intel:playbook_snapshot`, `intel:vix_level`, `intel:spy_trend` |
| Signals | `playbook_logs` Postgres table |
| P&L | `trade_history` Postgres table |
| Risk | `intel:risk_metrics` |
| Health | All `intel:*` keys (recency check) |

## Key Notes

- Service name: `cemini_os` in `docker-compose.yml`
- Port 8501 (Streamlit default)
- Redis auth required — uses `REDIS_PASSWORD` env var
- `app_net` network only (reads Redis intel bus, no direct Postgres writes)
- Auto-refresh every 30s via `st.rerun()`
