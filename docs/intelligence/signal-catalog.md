# Signal Catalog

The Signal Catalog is the registry of discrete tactical setups. Each detector implements a `detect(df, symbol)` method that accepts a pandas OHLCV DataFrame and returns a signal dict or `None`. Detectors are read-only — they never place orders.

---

## Signal Schema

Every returned signal follows this schema:

```python
{
    "pattern_name": str,       # e.g. "EpisodicPivot"
    "symbol":       str,       # ticker symbol
    "confidence":   float,     # 0.0 – 1.0
    "entry_price":  float,     # suggested entry
    "stop_price":   float,     # hard stop loss
    "detected_at":  str,       # ISO-8601 UTC timestamp
    "metadata":     dict,      # pattern-specific supporting data
}
```

---

## Detector Catalog

| Detector | Pattern | Timeframe | Min Rows | Key Condition |
|---|---|---|---|---|
| **EpisodicPivot** | Sudden high-volume breakout above resistance | Daily | 20 | Volume >2× 20-day avg + close above prior high |
| **MomentumBurst** | Multi-bar price + volume acceleration | Daily | 10 | 3+ consecutive higher closes, volume trending up |
| **ElephantBar** | Single oversized bullish candle | Daily | 5 | Bar range >2× ATR, close in top 25% of range |
| **VCP** | Volatility Contraction Pattern (Minervini) | Weekly/Daily | 60 | 3 contracting price waves + volume dry-up on last pullback |
| **HighTightFlag** | 100%+ advance in ≤8 weeks, tight consolidation | Weekly | 60 | Weinstein Stage 2 + flag depth <20% + volume expansion on breakout |
| **InsideBar212** | 2-1-2 compression then breakout | Daily | 5 | Three bars: wide outside → narrow inside → breakout candle |

---

## EpisodicPivot

The EpisodicPivot captures stocks experiencing sudden institutional accumulation — a single session where the price gaps or thrusts above a prior resistance level on dramatically elevated volume, signaling a change in fundamental or narrative perception.

**Detection logic:**
- Look back 20 bars for the highest high (resistance level)
- Volume on the trigger bar must exceed 2× the 20-bar average
- Close must be above the 20-bar resistance

**Confidence scoring:** Based on volume ratio (higher volume → higher confidence, capped at 0.95).

---

## MomentumBurst

MomentumBurst identifies stocks in a sustained momentum phase — consecutive closes above the prior bar's high, with volume trending upward. This is a trend-continuation setup rather than a breakout setup.

**Detection logic:**
- Minimum 3 consecutive bars with higher closes
- Volume trend (linear regression slope) must be positive
- RSI context check (not overbought above 80)

---

## ElephantBar

The ElephantBar is a single-session institutional accumulation bar — unusually wide range, heavy volume, close near the top of the bar. Named for its outsized footprint in the chart.

**Detection logic:**
- Bar range (High − Low) must exceed 2× ATR(14)
- Close must be in the top 25% of the bar range
- Volume must be above the 20-bar average

---

## VCP (Volatility Contraction Pattern)

The VCP is Mark Minervini's breakout setup. Price makes a series of contracting pullbacks (each shallower than the last), with volume drying up on the final contraction. The breakout from the last pivot on expanding volume is the entry trigger.

**Detection logic:**
- Identify 3 local maxima (waves) using scipy-style peak detection
- Each successive pullback must be shallower (contracting volatility)
- Volume on the final contraction leg must be below the 20-bar average

---

## HighTightFlag

The HighTightFlag is William O'Neil's most powerful base pattern — a stock that more than doubles in 8 weeks or less, then consolidates in a tight, orderly flag for 3–5 weeks before breaking out.

**Detection logic:**
- Look back 60 bars for a doubling move in ≤40 bars
- Flag consolidation: no close more than 20% below the flag high
- Flag must be at least 3 bars long
- Volume contraction during the flag

---

## InsideBar212

The InsideBar212 is a compression-then-breakout pattern: a wide outside bar (2) followed by a narrow inside bar (1) contained entirely within the outside bar, followed by a breakout bar (2) that exceeds the outside bar's range.

**Detection logic:**
- Bar[−2] (outside bar): establishes the range
- Bar[−1] (inside bar): High < Bar[−2].High and Low > Bar[−2].Low
- Bar[0] (current): Close > Bar[−2].High (bullish breakout)

---

## Pre-Evaluation Intent Logging

**This is the most important property of the Signal Catalog for buyers.**

In `scan_symbol()`, the audit trail intent log is written **before** `detector.detect()` is called:

```python
# Log intent BEFORE detection — proves no cherry-picking (Step 43)
if _INTENT_LOG_AVAILABLE:
    log_intent(
        symbol=symbol,
        signal_type=detector.name,
        scan_timestamp=datetime.now(timezone.utc).isoformat(),
    )

result = detector.detect(df, symbol)  # detection runs AFTER intent is logged
```

This guarantees that every evaluation attempt — including misses — is recorded. A buyer auditing the chain will see that the system evaluated every ticker it claimed to evaluate, not just the profitable ones.
