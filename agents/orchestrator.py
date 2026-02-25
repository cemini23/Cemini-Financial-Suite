# CEMINI FINANCIAL SUITE™
# Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
# All Rights Reserved.
import asyncio
import json
import os
import psycopg2
import redis.asyncio as aioredis
import pandas as pd
from typing import TypedDict, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from core.schemas.trading_signals import TradingSignal
from core.intel_bus import IntelReader

# Full watchlist: equities + crypto native
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
    # Crypto native (ticks stored as BTC-USD etc.)
    "BTC", "ETH", "SOL", "DOGE", "ADA", "AVAX", "LINK",
]

# Crypto watchlist symbols → raw_market_ticks symbol format
CRYPTO_TICKERS = {"BTC", "ETH", "SOL", "DOGE", "ADA", "AVAX", "LINK"}
CRYPTO_TICK_MAP = {
    "BTC": "BTC-USD", "ETH": "ETH-USD", "SOL": "SOL-USD",
    "DOGE": "DOGE-USD", "ADA": "ADA-USD", "AVAX": "AVAX-USD",
    "LINK": "LINK-USD",
}


# ---------------------------------------------------------------------------
# 1. State definition
# ---------------------------------------------------------------------------

class TradingState(TypedDict):
    symbol: str
    target_system: Literal["QuantOS", "Kalshi By Cemini"]
    raw_market_data: str
    technical_analysis: str
    technical_score: float          # 0.0–1.0
    fundamental_analysis: str
    fundamental_score: float        # 0.0–1.0
    sentiment_analysis: str
    sentiment_score: float          # 0.0–1.0
    rsi: float                      # forwarded into signal payload
    latest_price: float             # forwarded into signal payload
    final_decision: Dict[str, Any]
    position_size: float
    pydantic_signal: TradingSignal
    execution_status: str


# ---------------------------------------------------------------------------
# 2. Helpers
# ---------------------------------------------------------------------------

def _db_connect():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        port=5432,
        user=os.getenv("QUESTDB_USER", "admin"),
        password=os.getenv("QUESTDB_PASSWORD", "quest"),
        database="qdb",
    )


def _sync_redis():
    import redis as _redis
    return _redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=6379,
        password=os.getenv("REDIS_PASSWORD", "cemini_redis_2026"),
        decode_responses=True,
        socket_connect_timeout=2,
    )


def _calc_rsi(prices, period=14):
    """Wilder RSI from a price list (oldest→newest)."""
    if len(prices) < period + 1:
        return None
    deltas = [prices[i + 1] - prices[i] for i in range(len(prices) - 1)]
    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _calc_sma(prices, period):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def _get_playbook_regime():
    """Read current macro regime from intel:playbook_snapshot. Returns str or None."""
    snap = IntelReader.read("intel:playbook_snapshot")
    if snap and isinstance(snap.get("value"), dict):
        return snap["value"].get("regime")
    return None


# ---------------------------------------------------------------------------
# 3. Analyst nodes
# ---------------------------------------------------------------------------

def technical_analyst_node(state: TradingState):
    """
    Queries raw_market_ticks for real price history.
    Computes RSI-14, SMA-10/50, and price-change momentum.
    Returns a float score in [0.0, 1.0].
    """
    symbol = state["symbol"]
    tick_symbol = CRYPTO_TICK_MAP.get(symbol, symbol)

    try:
        conn = _db_connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT price FROM raw_market_ticks "
            "WHERE symbol = %s ORDER BY timestamp DESC LIMIT 30",
            (tick_symbol,),
        )
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        return {
            "technical_analysis": f"NEUTRAL: DB error ({e})",
            "technical_score": 0.5,
            "rsi": 50.0,
            "latest_price": 0.0,
        }

    if len(rows) < 2:
        return {
            "technical_analysis": "NEUTRAL: Insufficient price history",
            "technical_score": 0.5,
            "rsi": 50.0,
            "latest_price": 0.0,
        }

    # rows are DESC → reverse to get oldest-first for RSI
    prices = [float(r[0]) for r in reversed(rows)]
    latest_price = prices[-1]

    rsi = _calc_rsi(prices)
    if rsi is None:
        rsi = 50.0
        rsi_note = f"RSI=n/a ({len(prices)} bars)"
    else:
        rsi_note = f"RSI={rsi:.1f}"

    # Base score from RSI
    if rsi < 30:
        score = 0.8
        label = "BULLISH"
        reason = f"Oversold ({rsi_note})"
    elif rsi > 70:
        score = 0.2
        label = "BEARISH"
        reason = f"Overbought ({rsi_note})"
    elif rsi <= 50:
        score = 0.6
        label = "BULLISH"
        reason = f"Leaning bullish ({rsi_note})"
    else:
        score = 0.4
        label = "BEARISH"
        reason = f"Leaning bearish ({rsi_note})"

    # SMA modifier
    sma10 = _calc_sma(prices, 10)
    sma50 = _calc_sma(prices, 50)
    sma_note = ""
    if sma10 is not None and sma50 is not None:
        if sma10 > sma50:
            score = min(1.0, score + 0.1)
            sma_note = ", SMA10>SMA50(uptrend)"
        else:
            score = max(0.0, score - 0.1)
            sma_note = ", SMA10<SMA50(downtrend)"

    # Momentum: price change vs 10 bars ago
    lookback = min(10, len(prices) - 1)
    pct = (prices[-1] - prices[-1 - lookback]) / prices[-1 - lookback] * 100

    analysis = (
        f"{label}: {reason}{sma_note}, "
        f"Δ{pct:+.2f}%, price=${latest_price:.4f}"
    )
    return {
        "technical_analysis": analysis,
        "technical_score": round(score, 3),
        "rsi": round(rsi, 2),
        "latest_price": latest_price,
    }


def fundamental_analyst_node(state: TradingState):
    """
    Reads Fear & Greed, VIX, SPY trend, Fed bias from Redis.
    For crypto also applies the BTC sentiment signal.
    Returns a float score in [0.0, 1.0].
    """
    symbol = state["symbol"]
    is_crypto = symbol in CRYPTO_TICKERS

    # Raw Fear & Greed (set by macro_harvester as a plain float string)
    fg = 50.0
    try:
        r = _sync_redis()
        fg_raw = r.get("macro:fear_greed")
        r.close()
        if fg_raw:
            fg = float(fg_raw)
    except Exception:
        pass

    vix_sig = IntelReader.read("intel:vix_level")
    spy_sig = IntelReader.read("intel:spy_trend")
    fed_sig = IntelReader.read("intel:fed_bias")

    vix = float(vix_sig["value"]) if vix_sig else 20.0
    spy_trend = (spy_sig["value"] or "neutral").lower() if spy_sig else "neutral"
    fed_bias = "neutral"
    if fed_sig and isinstance(fed_sig.get("value"), dict):
        fed_bias = fed_sig["value"].get("bias", "neutral").lower()

    # Base score: contrarian Fear & Greed
    if fg < 20:
        score = 0.8
        fg_note = f"ExtremeFear(FGI={fg:.0f})→bullish"
    elif fg > 80:
        score = 0.2
        fg_note = f"ExtremeGreed(FGI={fg:.0f})→bearish"
    elif fg < 40:
        score = 0.6
        fg_note = f"Fear(FGI={fg:.0f})"
    elif fg <= 60:
        score = 0.5
        fg_note = f"Neutral(FGI={fg:.0f})"
    else:
        score = 0.4
        fg_note = f"Greed(FGI={fg:.0f})"

    # VIX modifier
    if vix > 30:
        score = min(1.0, score + 0.1)
        vix_note = f", VIX={vix:.0f}(fear→opp)"
    elif vix < 15:
        score = max(0.0, score - 0.1)
        vix_note = f", VIX={vix:.0f}(complacent)"
    else:
        vix_note = f", VIX={vix:.0f}"

    # SPY trend modifier
    if spy_trend == "bullish":
        score = min(1.0, score + 0.05)
        spy_note = ", SPY=bullish"
    elif spy_trend == "bearish":
        score = max(0.0, score - 0.05)
        spy_note = ", SPY=bearish"
    else:
        spy_note = ", SPY=neutral"

    # Fed modifier
    if fed_bias == "dovish":
        score = min(1.0, score + 0.05)
        fed_note = ", Fed=dovish"
    elif fed_bias == "hawkish":
        score = max(0.0, score - 0.05)
        fed_note = ", Fed=hawkish"
    else:
        fed_note = f", Fed={fed_bias}"

    # Crypto: BTC sentiment modifier
    btc_note = ""
    if is_crypto:
        btc_sig = IntelReader.read("intel:btc_sentiment")
        if btc_sig:
            btc_sent = float(btc_sig["value"])
            if btc_sent > 0.3:
                score = min(1.0, score + 0.05)
                btc_note = f", BTCsent={btc_sent:+.2f}"
            elif btc_sent < -0.3:
                score = max(0.0, score - 0.05)
                btc_note = f", BTCsent={btc_sent:+.2f}"

    label = (
        "BULLISH" if score >= 0.55 else
        ("BEARISH" if score <= 0.45 else "NEUTRAL")
    )
    analysis = f"{label}: {fg_note}{vix_note}{spy_note}{fed_note}{btc_note}"
    return {
        "fundamental_analysis": analysis,
        "fundamental_score": round(score, 3),
    }


def sentiment_analyst_node(state: TradingState):
    """
    Blends Intel Bus social_score with recent x_tier sentiment from Postgres.
    Returns a float score in [0.0, 1.0].
    Neutral default = 0.5 (never 1.0).
    """
    # Intel Bus social score
    social_raw = 0.0
    social_sig = IntelReader.read("intel:social_score")
    if social_sig:
        val = social_sig.get("value")
        if isinstance(val, dict):
            social_raw = float(val.get("score", 0.0))
        elif val is not None:
            social_raw = float(val)

    # DB: average x_tier sentiment from last 2 hours
    db_score = None
    try:
        conn = _db_connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT AVG(sentiment_score) FROM sentiment_logs "
            "WHERE source LIKE 'x_tier%%' "
            "AND timestamp > NOW() - INTERVAL '2 hours'"
        )
        row = cursor.fetchone()
        conn.close()
        if row and row[0] is not None:
            db_score = float(row[0])
    except Exception:
        pass

    # Blend
    effective = social_raw
    if db_score is not None:
        effective = (social_raw + db_score) / 2.0

    # Score mapping
    if effective > 0.3:
        score = 0.8
        label = "BULLISH"
        detail = f"positive(score={effective:.3f})"
    elif effective < -0.3:
        score = 0.2
        label = "BEARISH"
        detail = f"negative(score={effective:.3f})"
    else:
        # Linear: -0.3→0.3 maps to 0.3→0.7
        score = 0.5 + (effective / 0.3) * 0.2
        score = max(0.3, min(0.7, score))
        label = "NEUTRAL"
        detail = f"neutral(score={effective:.3f})"

    db_note = f", DB={db_score:.3f}" if db_score is not None else ", DB=none"
    analysis = f"{label}: {detail}{db_note}"
    return {
        "sentiment_analysis": analysis,
        "sentiment_score": round(score, 3),
    }


# ---------------------------------------------------------------------------
# 4. CIO Debate node — uses numeric scores directly
# ---------------------------------------------------------------------------

def cio_debate_node(state: TradingState):
    """
    Aggregates real numeric scores from the three analysts.
    BUY if avg > 0.7, SELL if avg < 0.3, HOLD otherwise.

    NOTE: Simplified numeric scoring — pending LLM-backed debate validation.
    Thresholds (0.7 / 0.3) are empirically set; the regime gate in
    publish_signal_to_bus is the primary macro filter before any EXECUTE
    verdict reaches Redis.
    """
    tech_score = state.get("technical_score", 0.5)
    fund_score = state.get("fundamental_score", 0.5)
    sent_score = state.get("sentiment_score", 0.5)
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
            f"tech={tech_score:.2f}, fund={fund_score:.2f}, "
            f"sent={sent_score:.2f} → avg={avg_score:.2f} → {action}"
        ),
    }
    return {
        "final_decision": decision,
        "position_size": decision["position_size"],
    }


# ---------------------------------------------------------------------------
# 5. Redis publisher — includes real price and RSI in payload
# ---------------------------------------------------------------------------

async def publish_signal_to_bus(state: TradingState):
    """
    Publishes the validated trade signal to Redis 'trade_signals'.
    Payload now includes price and rsi so EMS/logger can record real values.
    """
    decision = state.get("final_decision")

    if decision and decision.get("verdict") == "EXECUTE":
        # ── REGIME GATE ────────────────────────────────────────────────────────
        # Playbook regime is authoritative over strategy_mode.
        # YELLOW / RED = macro deterioration; no new longs are permitted.
        # SELL signals are allowed through in any regime (reducing exposure is safe).
        if decision.get("action", "").upper() == "BUY":
            regime = _get_playbook_regime()
            if regime in ("YELLOW", "RED"):
                print(
                    f"⛔ Trade blocked: regime={regime}, no new longs permitted"
                    f" — {state['symbol']} {decision['action']}"
                    f" (score={decision.get('confidence_score', 0):.2f})"
                )
                return {"execution_status": "BLOCKED_BY_REGIME"}
        # ── END REGIME GATE ────────────────────────────────────────────────────

        # Log to Postgres audit table
        try:
            db_host = os.getenv("DB_HOST", "postgres")
            conn = psycopg2.connect(
                host=db_host, port=5432,
                user=os.getenv("QUESTDB_USER", "admin"),
                password=os.getenv("QUESTDB_PASSWORD", "quest"),
                database="qdb",
            )
            conn.autocommit = True
            cursor = conn.cursor()
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
                "INSERT INTO ai_trade_logs "
                "(symbol, action, verdict, confidence, size, reasoning, timestamp) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    state["symbol"], decision["action"], decision["verdict"],
                    decision["confidence_score"], state["position_size"],
                    decision["reasoning"], pd.Timestamp.now(tz="UTC"),
                ),
            )
            conn.close()
            print("📊 UI: Decision logged to Postgres.")
        except Exception as qe:
            print(f"⚠️ UI: Could not log to Postgres: {qe}")

        # Publish to Redis
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_pass = os.getenv("REDIS_PASSWORD", "cemini_redis_2026")
        r = aioredis.from_url(
            f"redis://:{redis_pass}@{redis_host}:6379",
            decode_responses=True,
        )
        try:
            payload = json.dumps({
                "pydantic_signal": {
                    "ticker_or_event": state["symbol"],
                    "action": decision["action"].lower(),
                    "target_system": state.get("target_system", "QuantOS"),
                    "target_brokerage": (
                        "Kalshi"
                        if state.get("target_system") == "Kalshi By Cemini"
                        else "Robinhood"
                    ),
                    "asset_class": "equity",
                    "confidence_score": decision["confidence_score"],
                    "proposed_allocation_pct": min(
                        0.10, state.get("position_size", 0.0) / 250.0
                    ),
                    "agent_reasoning": decision.get(
                        "reasoning", "Automated signal from orchestrator."
                    ),
                },
                "decision": decision,
                # Real market data forwarded to EMS/logger
                "price": state.get("latest_price", 0.0),
                "rsi": state.get("rsi", 0.0),
            })
            await r.publish("trade_signals", payload)
            print(
                f"📡 Signal published → trade_signals: "
                f"{state['symbol']} {decision['action']}"
            )
            return {"execution_status": "SIGNAL_PUBLISHED"}
        except Exception as pub_e:
            print(f"❌ Failed to publish signal to Redis: {pub_e}")
            return {"execution_status": "PUBLISH_FAILED"}
        finally:
            await r.aclose()

    return {"execution_status": "NO_ACTION_TAKEN"}


# ---------------------------------------------------------------------------
# 6. Router
# ---------------------------------------------------------------------------

def should_continue(state: TradingState):
    decision = state.get("final_decision", {})
    if decision.get("verdict") == "EXECUTE":
        return "publish_to_bus"
    return END


# ---------------------------------------------------------------------------
# 7. Compile StateGraph
# ---------------------------------------------------------------------------

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
        {"publish_to_bus": "publish_to_bus", END: END},
    )
    workflow.add_edge("publish_to_bus", END)

    return workflow.compile()


# ---------------------------------------------------------------------------
# 8. Main loop
# ---------------------------------------------------------------------------

async def main():
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
                    "technical_score": 0.5,
                    "fundamental_analysis": "",
                    "fundamental_score": 0.5,
                    "sentiment_analysis": "",
                    "sentiment_score": 0.5,
                    "rsi": 50.0,
                    "latest_price": 0.0,
                    "final_decision": {},
                    "position_size": 0.0,
                    "execution_status": "",
                }
                print(f"🧠 Cemini Brain: Processing {symbol}...")
                await brain.ainvoke(initial_state)
                await asyncio.sleep(2)
            except Exception as e:
                print(f"❌ Cemini Brain: Error processing {symbol}: {e}")

        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
