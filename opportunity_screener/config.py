"""
opportunity_screener/config.py — All thresholds via env vars (Step 26.1h)
"""
import os

# ── Watchlist thresholds ──────────────────────────────────────────────────────
SCREENER_PROMOTION_THRESHOLD: float = float(os.getenv("SCREENER_PROMOTION_THRESHOLD", "0.65"))
SCREENER_DEMOTION_THRESHOLD: float = float(os.getenv("SCREENER_DEMOTION_THRESHOLD", "0.45"))
SCREENER_MAX_DYNAMIC_TICKERS: int = int(os.getenv("SCREENER_MAX_DYNAMIC_TICKERS", "50"))
SCREENER_EVICTION_HYSTERESIS: float = float(os.getenv("SCREENER_EVICTION_HYSTERESIS", "0.05"))
SCREENER_STALE_TTL_HOURS: int = int(os.getenv("SCREENER_STALE_TTL_HOURS", "72"))

# ── Conviction decay ──────────────────────────────────────────────────────────
SCREENER_DECAY_RATE: float = float(os.getenv("SCREENER_DECAY_RATE", "0.995"))
SCREENER_DECAY_INTERVAL_SECONDS: int = int(os.getenv("SCREENER_DECAY_INTERVAL_SECONDS", "300"))

# ── Multi-source convergence ──────────────────────────────────────────────────
SCREENER_CONVERGENCE_WINDOW_MINUTES: int = int(os.getenv("SCREENER_CONVERGENCE_WINDOW_MINUTES", "30"))
SCREENER_CONVERGENCE_MULTIPLIER: float = float(os.getenv("SCREENER_CONVERGENCE_MULTIPLIER", "1.3"))

# ── Audit log flush ───────────────────────────────────────────────────────────
SCREENER_AUDIT_FLUSH_SECONDS: int = int(os.getenv("SCREENER_AUDIT_FLUSH_SECONDS", "30"))
SCREENER_AUDIT_FLUSH_BATCH_SIZE: int = int(os.getenv("SCREENER_AUDIT_FLUSH_BATCH_SIZE", "100"))

# ── Core watchlist (never evicted) ───────────────────────────────────────────
CORE_WATCHLIST: list[str] = os.getenv(
    "CORE_WATCHLIST", "SPY,QQQ,IWM,DIA,BTC-USD,ETH-USD"
).split(",")

# ── Screener polling ──────────────────────────────────────────────────────────
SCREENER_POLL_INTERVAL_SECONDS: int = int(os.getenv("SCREENER_POLL_INTERVAL_SECONDS", "30"))

# ── Redis ─────────────────────────────────────────────────────────────────────
REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "cemini_redis_2026")

# ── Postgres ──────────────────────────────────────────────────────────────────
DB_HOST: str = os.getenv("DB_HOST", "postgres")
DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
DB_USER: str = os.getenv("DB_USER", "admin")
DB_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "quest")
DB_NAME: str = os.getenv("DB_NAME", "qdb")

# ── App ───────────────────────────────────────────────────────────────────────
APP_HOST: str = os.getenv("SCREENER_HOST", "0.0.0.0")  # nosec B104
APP_PORT: int = int(os.getenv("SCREENER_PORT", "8003"))

# ── Intel channels to poll ────────────────────────────────────────────────────
INTEL_CHANNELS: list[str] = [
    "intel:playbook_snapshot",
    "intel:spy_trend",
    "intel:vix_level",
    "intel:portfolio_heat",
    "intel:btc_volume_spike",
    "intel:btc_sentiment",
    "intel:fed_bias",
    "intel:social_score",
    "intel:weather_edge",
    "intel:geo_risk_score",
    "intel:kalshi_oi",
    "intel:kalshi_liquidity_spike",
    "intel:kalshi_rewards",
]
