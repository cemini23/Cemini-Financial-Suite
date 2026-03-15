"""Cemini Financial Suite — Debate Protocol Configuration (Step 47)."""
from __future__ import annotations

# ── Blackboard ─────────────────────────────────────────────────────────────────
BLACKBOARD_TTL = 3600          # 1 hour — full debate window

# ── Tie-breaking thresholds ────────────────────────────────────────────────────
TIE_THRESHOLD = 0.10           # Minimum score margin to avoid HOLD
CLOSE_CALL_THRESHOLD = 0.20    # Within this margin → tie_break_used=True
REGIME_BULL_MULTIPLIER = 1.2   # GREEN regime bonus for bull score
REGIME_BEAR_MULTIPLIER = 1.2   # RED regime bonus for bear score

# ── Agent defaults ─────────────────────────────────────────────────────────────
BASE_CONFIDENCE = 0.5          # Starting confidence for agents
SIGNAL_CONFIRMING_WEIGHT = 0.1 # Each confirming signal adds this much to confidence
MAX_SIGNALS_CHECKED = 5        # Cap the number of signals checked per agent

# ── Intel channels read by debate agents ───────────────────────────────────────
INTEL_PLAYBOOK_SNAPSHOT = "intel:playbook_snapshot"
INTEL_VIX_LEVEL = "intel:vix_level"
INTEL_SPY_TREND = "intel:spy_trend"
INTEL_EDGAR_ALERT = "intel:edgar_alert"
INTEL_FRED_YIELD_CURVE = "intel:fred_yield_curve"
INTEL_FRED_CREDIT_SPREAD = "intel:fred_credit_spread"
INTEL_SOCIAL_SCORE = "intel:social_score"
INTEL_BTC_SENTIMENT = "intel:btc_sentiment"

# ── Output channel ─────────────────────────────────────────────────────────────
INTEL_DEBATE_VERDICT = "intel:debate_verdict"
DEBATE_VERDICT_TTL = 1800      # 30 minutes

# ── Archive ────────────────────────────────────────────────────────────────────
ARCHIVE_ROOT_DEFAULT = "/mnt/archive/debates"

# ── Regime VIX thresholds (read from macro context) ───────────────────────────
VIX_ELEVATED = 25.0            # VIX above this → bearish signal
VIX_EXTREME = 40.0             # VIX above this → very bearish
