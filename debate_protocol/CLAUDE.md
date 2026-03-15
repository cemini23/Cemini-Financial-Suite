# Devil's Advocate Debate Protocol (Step 47)

Multi-agent debate topology with Shared Blackboard architecture.
**No LLM required** — all agents are deterministic (rule-based).

## Architecture

```
Redis Blackboard (debate:{session_id}, TTL 3600s)
    ↑ write / ↓ read
MacroAgent → BullAgent → BearAgent → RiskAgent → TraderAgent
             ↑ read macro context from blackboard
```

## Files

| File | Purpose |
|------|---------|
| `models.py` | Pydantic v2: DebateState, AgentArgument, CrossExamination, Rebuttal, DebateVerdict |
| `blackboard.py` | Redis Shared Blackboard (STRING key, TTL 3600s) |
| `config.py` | Weights, thresholds, Intel channel names |
| `tie_breaker.py` | Regime-weighted scoring (GREEN=1.2x bull, RED=1.2x bear) |
| `debate_logger.py` | Postgres + JSONL + audit chain + intel:debate_verdict |
| `state_machine.py` | `run_debate()` — 5-phase orchestration |
| `agents/macro_agent.py` | Phase 1: reads Intel Bus, sets macro context |
| `agents/bull_agent.py` | Phase 2: argues FOR the trade |
| `agents/bear_agent.py` | Phase 2: argues AGAINST the trade |
| `agents/risk_agent.py` | Phase 3: Devil's Advocate, generates CrossExamination |
| `agents/trader_agent.py` | Phase 5: synthesizes DebateVerdict |

## Public API

```python
from debate_protocol.state_machine import run_debate
verdict = await run_debate("AAPL", redis_client=rdb_async, db_conn=pg, sync_redis=rdb_sync)

from debate_protocol.tie_breaker import resolve
action, multiplier_applied, tie_break_used = resolve(0.65, 0.50, "GREEN")
# → ("BUY", True, False)
```

## 5-Phase Flow

1. **GATHERING** — MacroAgent reads Intel Bus (playbook_snapshot, vix, spy_trend, FRED, EDGAR, social)
2. **ARGUING** — BullAgent + BearAgent each write an argument to the blackboard
3. **CROSS_EXAMINING** — RiskAgent (Devil's Advocate) challenges the strongest argument:
   - Regime contradiction (bull in RED, bear in GREEN)
   - Insider data contradiction
   - Single-indicator concentration risk
4. **REBUTTING** — Bull/Bear respond to each challenge; confidence adjusts
5. **DECIDING** — TraderAgent synthesizes DebateVerdict via `tie_breaker.resolve()`

## Tie-Breaking

- GREEN regime: `bull_score × 1.2`
- RED regime: `bear_score × 1.2`
- YELLOW regime: no multiplier
- Margin < 0.10 → HOLD (conservative)
- Margin < 0.20 → tie_break_used = True

## Redis

- Blackboard key: `debate:{session_id}` (STRING, TTL 3600s)
- Intel Bus output: `intel:debate_verdict` (SET, TTL 1800s)

## DB

- `debate_sessions` table — migration `20260315120000_add_debate_sessions.sql`

## Archive

- `/mnt/archive/debates/YYYY-MM-DD.jsonl` (override with `DEBATE_ARCHIVE_DIR` env var)

## Integration with Orchestrator

`run_debate()` is called as a standalone coroutine. To integrate with the existing
LangGraph orchestrator (`agents/orchestrator.py`):

```python
# Add to orchestrator graph node:
async def debate_node(state: TradingState) -> TradingState:
    verdict = await run_debate(state["symbol"], redis_client=rdb_async)
    state["debate_verdict"] = verdict.model_dump()
    return state
```

## Known Gotchas

- `redis_client` in the blackboard must be `redis.asyncio.Redis` (async)
- `sync_redis` (for MacroAgent Intel Bus reads + intel:debate_verdict publish) must be synchronous `redis.Redis`
- If Redis is unavailable, `run_debate()` returns `action="NO_ACTION"` gracefully (never raises)
- `MacroAgent.redis_client=None` → all Intel Bus reads return None → YELLOW/neutral defaults
- Agents are NOT parallel in this implementation (sequential for determinism); parallelism is a future upgrade
