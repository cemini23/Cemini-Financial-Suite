# CEMINI FINANCIAL SUITE™
# Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
# All Rights Reserved.
import json
import os
import redis.asyncio as redis
import pandas as pd
from typing import TypedDict, Dict, Any, List, Literal
from langgraph.graph import StateGraph, END
from core.schemas.trading_signals import TradingSignal

# Full watchlist: equities from tickers.json + crypto native
WATCHLIST = [
    # Indices
    "SPY", "QQQ", "IWM",
    # Mega cap
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL",
    # High beta
    "TSLA", "AMD", "SMCI", "PLTR", "AVGO",
    # Crypto proxies
    "COIN", "MSTR", "MARA",
    # Financials
    "JPM", "BAC", "GS",
    # Consumer / Tech
    "DIS", "NFLX", "UBER",
    # Crypto native
    "BTC", "ETH", "SOL", "DOGE", "ADA", "AVAX", "LINK",
]

# 1. Define the Global State (The 'Spinal Cord' memory)
class TradingState(TypedDict):
    symbol: str
    target_system: Literal["QuantOS", "Kalshi By Cemini"]
    raw_market_data: str            # Markdown OHLCV table from Polars
    technical_analysis: str
    fundamental_analysis: str
    sentiment_analysis: str
    final_decision: Dict[str, Any]  # Output from CIO (Debate) Node
    position_size: float            # Calculated via Kelly Criterion
    pydantic_signal: TradingSignal
    execution_status: str

# --- ANALYST NODES ---

def technical_analyst_node(state: TradingState):
    return {"technical_analysis": "BULLISH: RSI at 40, price rebounding from support level."}

def fundamental_analyst_node(state: TradingState):
    return {"fundamental_analysis": "NEUTRAL: Macro data stable, awaiting earnings report."}

def sentiment_analyst_node(state: TradingState):
    return {"sentiment_analysis": "BULLISH: High velocity detected in order book, smart money accumulating."}

# --- CIO DEBATE NODE (Hedge Fund Rulebook & Kelly Criterion) ---

def _parse_score(analysis_text: str) -> float:
    """Maps analyst text to a numeric score: BULLISH=1.0, BEARISH=0.0, NEUTRAL=0.5."""
    t = analysis_text.upper()
    if "BULLISH" in t:
        return 1.0
    if "BEARISH" in t:
        return 0.0
    return 0.5


def cio_debate_node(state: TradingState):
    """
    Acts as the Chief Investment Officer.
    Aggregates scores from technical, fundamental, and sentiment analysts.
    BUY if avg > 0.7, SELL if avg < 0.3, HOLD otherwise.
    LLM call is a placeholder for future integration.
    """
    tech = state['technical_analysis']
    fund = state['fundamental_analysis']
    sent = state['sentiment_analysis']

    tech_score = _parse_score(tech)
    fund_score = _parse_score(fund)
    sent_score = _parse_score(sent)
    avg_score = (tech_score + fund_score + sent_score) / 3.0

    if avg_score > 0.7:
        action, verdict = "BUY", "EXECUTE"
        confidence = avg_score
    elif avg_score < 0.3:
        action, verdict = "SELL", "EXECUTE"
        confidence = 1.0 - avg_score
    else:
        action, verdict = "HOLD", "PASS"
        confidence = 0.5

    kelly_factor = max(0.0, (confidence * 2) - 1)
    calculated_size = min(4.99, 4.99 * kelly_factor)

    decision = {
        "verdict": verdict,
        "confidence_score": round(confidence, 2),
        "action": action,
        "position_size": round(calculated_size, 2),
        "reasoning": (
            f"Score-weighted consensus for {state['symbol']}: "
            f"tech={tech_score:.1f}, fund={fund_score:.1f}, sent={sent_score:.1f} "
            f"→ avg={avg_score:.2f} → {action}"
        )
    }

    return {
        "final_decision": decision,
        "position_size": decision["position_size"]
    }

# --- REDIS PUBLISHER (The Bridge to EMS) ---

async def publish_signal_to_bus(state: TradingState):
    """
    Publishes the validated trade signal to the Redis 'trade_signals' channel.
    """
    decision = state.get("final_decision")

    if decision and decision.get("verdict") == "EXECUTE":
        # --- NEW: Log to Postgres for UI Visualization ---
        try:
            import psycopg2
            db_host = os.getenv("DB_HOST", "postgres")
            conn = psycopg2.connect(
                host=db_host,
                port=5432,
                user=os.getenv("QUESTDB_USER", "admin"),
                password=os.getenv("QUESTDB_PASSWORD", "quest"),
                database="qdb"
            )
            conn.autocommit = True
            cursor = conn.cursor()

            # Ensure the audit table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_trade_logs (
                    symbol VARCHAR(50),
                    action VARCHAR(20),
                    verdict VARCHAR(20),
                    confidence DOUBLE PRECISION,
                    size DOUBLE PRECISION,
                    reasoning TEXT,
                    timestamp TIMESTAMP WITH TIME ZONE
                );
            """)

            cursor.execute(
                "INSERT INTO ai_trade_logs (symbol, action, verdict, confidence, size, reasoning, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (state['symbol'], decision['action'], decision['verdict'], decision['confidence_score'], state['position_size'], decision['reasoning'], pd.Timestamp.now(tz='UTC'))
            )
            conn.close()
            print("📊 UI: Decision logged to Postgres.")
        except Exception as qe:
            print(f"⚠️ UI: Could not log to Postgres: {qe}")

        # Connect to Redis and publish signal
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_pass = os.getenv('REDIS_PASSWORD', 'cemini_redis_2026')
        r = redis.from_url(f"redis://:{redis_pass}@{redis_host}:6379", decode_responses=True)
        try:
            payload = json.dumps({
                "pydantic_signal": {
                    "ticker_or_event": state['symbol'],
                    "action": decision['action'].lower(),
                    "target_system": state.get('target_system', 'QuantOS'),
                    "target_brokerage": (
                        "Kalshi" if state.get('target_system') == "Kalshi By Cemini"
                        else "Robinhood"
                    ),
                    "asset_class": "equity",
                    "confidence_score": decision['confidence_score'],
                    "proposed_allocation_pct": min(
                        0.10, state.get('position_size', 0.0) / 250.0
                    ),
                    "agent_reasoning": decision.get(
                        'reasoning', 'Automated signal from orchestrator.'
                    ),
                },
                "decision": decision,
            })
            await r.publish('trade_signals', payload)
            print(f"📡 Signal published → trade_signals: {state['symbol']} {decision['action']}")
            return {"execution_status": "SIGNAL_PUBLISHED"}
        except Exception as pub_e:
            print(f"❌ Failed to publish signal to Redis: {pub_e}")
            return {"execution_status": "PUBLISH_FAILED"}
        finally:
            await r.aclose()

    return {"execution_status": "NO_ACTION_TAKEN"}

# --- ROUTER LOGIC ---

def should_continue(state: TradingState):
    decision = state.get("final_decision", {})
    if decision.get("verdict") == "EXECUTE":
        return "publish_to_bus"
    return END

# --- COMPILE STATEGRAPH ---

def create_cemini_brain():
    workflow = StateGraph(TradingState)

    workflow.add_node("technical_analyst", technical_analyst_node)
    workflow.add_node("fundamental_analyst", fundamental_analyst_node)
    workflow.add_node("sentiment_analyst", sentiment_analyst_node)
    workflow.add_node("cio_debate", cio_debate_node)
    workflow.add_node("publish_to_bus", publish_signal_to_bus)

    workflow.set_entry_point("technical_analyst")
    workflow.add_edge("technical_analyst", "fundamental_analyst")
    workflow.add_edge("fundamental_analyst", "sentiment_analyst")
    workflow.add_edge("sentiment_analyst", "cio_debate")

    workflow.add_conditional_edges(
        "cio_debate",
        should_continue,
        {
            "publish_to_bus": "publish_to_bus",
            END: END
        }
    )

    workflow.add_edge("publish_to_bus", END)

    return workflow.compile()

async def main():
    """
    Main loop to run the Cemini Brain periodically.
    Scans all symbols in WATCHLIST each cycle, with a 60-second rest between cycles.
    """
    brain = create_cemini_brain()
    print(
        f"🧠 Cemini Brain: Orchestrator started. "
        f"Scanning {len(WATCHLIST)} symbols per cycle (60s between cycles)..."
    )

    while True:
        for symbol in WATCHLIST:
            try:
                initial_state = {
                    "symbol": symbol,
                    "target_system": "QuantOS",
                    "raw_market_data": "",
                    "technical_analysis": "",
                    "fundamental_analysis": "",
                    "sentiment_analysis": "",
                    "final_decision": {},
                    "position_size": 0.0,
                    "execution_status": ""
                }

                print(f"🧠 Cemini Brain: Processing {symbol}...")
                await brain.ainvoke(initial_state)
                await asyncio.sleep(2)  # brief pause between symbols

            except Exception as e:
                print(f"❌ Cemini Brain: Error processing {symbol}: {e}")

        await asyncio.sleep(60)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
