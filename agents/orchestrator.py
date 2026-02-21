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

def cio_debate_node(state: TradingState):
    """
    Acts as the Chief Investment Officer. 
    Implements the 'Autopilot Protocol' and 'Hedge Fund Rulebook'.
    """
    tech = state['technical_analysis']
    fund = state['fundamental_analysis']
    sent = state['sentiment_analysis']
    
    # SYSTEM PROMPT FOR CIO LLM
    prompt = f"""
    Evaluate the following analyst reports for {state['symbol']}.
    - Tech: {tech}
    - Fund: {fund}
    - Sent: {sent}

    HEDGE FUND RULEBOOK:
    1. 3-Way Consensus (BULLISH/BULLISH/BULLISH) -> 0.95 Confidence, EXECUTE.
    2. Sentiment Priority: If Sentiment is BULLISH and Volume > 2x Avg -> Weight Sentiment at 70%.
    3. Conflict: If 2+ reports are NEUTRAL -> PASS.
    4. Max Position: Absolute cap of $250 USD.
    5. Kelly Criterion: Size = (Confidence * 2) - 1. Multiply this factor by the $250 cap.

    Output JSON:
    {{
      "verdict": "EXECUTE/PASS/WATCH",
      "confidence_score": 0.0-1.0,
      "action": "BUY/SELL/HOLD",
      "reasoning": "Explain the weighted logic applied"
    }}
    """
    
    # Simulated LLM decision logic
    # --- SAFETY: Allowing execution but capped at $4.99 ---
    confidence = 0.85
    kelly_factor = (confidence * 2) - 1 # 0.70
    calculated_size = min(4.99, 4.99 * kelly_factor) # Strictly capped at $4.99

    decision = {
        "verdict": "EXECUTE",
        "confidence_score": confidence,
        "action": "BUY",
        "position_size": round(calculated_size, 2),
        "reasoning": f"TESTING: Bullish bias detected. Executing micro-position for {state['symbol']}."
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
                user="admin",
                password="quest",
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

        # Connect to Redis
        redis_host = os.getenv('REDIS_HOST', 'redis')
        r = redis.from_url(f"redis://{redis_host}:6379", decode_responses=True)
        
        # --- POSITION LOCK CHECK ---
    
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
    """
    brain = create_cemini_brain()
    print("🧠 Cemini Brain: Orchestrator started. Running workflow every 60 seconds...")
    
    while True:
        try:
            initial_state = {
                "symbol": "DOGE",
                "target_system": "QuantOS",
                "raw_market_data": "",
                "technical_analysis": "",
                "fundamental_analysis": "",
                "sentiment_analysis": "",
                "final_decision": {},
                "position_size": 0.0,
                "execution_status": ""
            }
            
            # Run the workflow
            print(f"🧠 Cemini Brain: Processing {initial_state['symbol']}...")
            await brain.ainvoke(initial_state)
            
        except Exception as e:
            print(f"❌ Cemini Brain: Error in workflow: {e}")
            
        await asyncio.sleep(60)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
