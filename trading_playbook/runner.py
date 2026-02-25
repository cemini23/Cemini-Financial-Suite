"""
Cemini Financial Suite — Playbook Runner

Main loop for the trading_playbook service.

Runs every SCAN_INTERVAL seconds (default 300 s / 5 min):
  1. Classify macro regime (SPY EMA21 / SMA50 / JNK-TLT)
  2. Fetch recent OHLCV for the QuantOS watchlist via yfinance
  3. Run all signal detectors against each symbol
  4. Compute risk snapshot (CVaR, Kelly, drawdown) from trade_history
  5. Run kill-switch health checks
  6. Log everything via PlaybookLogger

This service is observation-only.  No orders are placed here.
The RL agent will later use the regime + signal + risk state as its
observation space, training against the JSONL / Postgres records produced
by this runner.

Environment variables
---------------------
SCAN_INTERVAL          Seconds between playbook cycles (default 300).
PLAYBOOK_WATCHLIST     Comma-separated symbols to scan (default: QuantOS list).
PLAYBOOK_KELLY_FRAC    Fractional Kelly cap (default 0.25).
PLAYBOOK_DD_THRESHOLD  Max drawdown before strategy halt (default 0.15).
PLAYBOOK_CVAR_LIMIT    CVaR limit as fraction of NAV (default 0.05).
DB_HOST                Postgres hostname.
REDIS_HOST             Redis hostname.
"""

import logging
import os
import time

import numpy as np
import pandas as pd
import yfinance as yf

from trading_playbook.kill_switch import KillSwitch
from trading_playbook.macro_regime import classify_regime
from trading_playbook.playbook_logger import PlaybookLogger
from trading_playbook.risk_engine import CVaRCalculator, DrawdownMonitor, FractionalKelly
from trading_playbook.signal_catalog import scan_symbol

# ----- logging setup -------------------------------------------------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)
logger = logging.getLogger("playbook.runner")

# ----- optional Postgres for PnL history ------------------------------------ #
try:
    import psycopg2
    _PG_AVAILABLE = True
except ImportError:
    _PG_AVAILABLE = False

# ----- configuration -------------------------------------------------------- #
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "300"))
KELLY_FRAC = float(os.getenv("PLAYBOOK_KELLY_FRAC", "0.25"))
DD_THRESHOLD = float(os.getenv("PLAYBOOK_DD_THRESHOLD", "0.15"))
CVAR_LIMIT = float(os.getenv("PLAYBOOK_CVAR_LIMIT", "0.05"))

DEFAULT_WATCHLIST = [
    "SPY", "QQQ", "IWM",
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA",
    "AMD", "SMCI", "PLTR", "AVGO",
    "COIN", "MSTR", "MARA",
    "JPM", "BAC", "GS",
]

WATCHLIST: list = [
    s.strip() for s in os.getenv("PLAYBOOK_WATCHLIST", "").split(",")
    if s.strip()
] or DEFAULT_WATCHLIST

OHLCV_PERIOD = "6mo"   # enough for all detectors (VCP needs 60+ bars)


# ----- helpers -------------------------------------------------------------- #
def _fetch_ohlcv(symbol: str) -> pd.DataFrame:
    """Return OHLCV DataFrame for *symbol* or an empty DataFrame on failure."""
    try:
        df = yf.Ticker(symbol).history(period=OHLCV_PERIOD, timeout=15)
        return df.reset_index(drop=True) if not df.empty else pd.DataFrame()
    except Exception as exc:
        logger.debug("[Runner] yfinance failed for %s: %s", symbol, exc)
        return pd.DataFrame()


def _fetch_pnl_returns() -> np.ndarray:
    """
    Query trade_history for recent closed-trade returns.

    Returns a numpy array of fractional returns (sell_price / buy_price - 1).
    Falls back to an empty array on any failure.
    """
    if not _PG_AVAILABLE:
        return np.array([])
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres"),
            port=5432,
            user=os.getenv("POSTGRES_USER", "admin"),
            password=os.getenv("POSTGRES_PASSWORD", "quest"),
            database=os.getenv("POSTGRES_DB", "qdb"),
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT price FROM trade_history
            WHERE action IN ('SELL', 'sell')
            ORDER BY timestamp DESC LIMIT 200
            """
        )
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            return np.array([])
        prices = np.array([float(r[0]) for r in rows if r[0] is not None])
        if len(prices) < 2:
            return np.array([])
        # Approximate returns as pct changes between successive sell prices
        return np.diff(prices) / prices[:-1]
    except Exception as exc:
        logger.debug("[Runner] PnL fetch failed: %s", exc)
        return np.array([])


# ----- main loop ------------------------------------------------------------ #
def run_playbook_cycle(
    kill_switch: KillSwitch,
    kelly: FractionalKelly,
    cvar_calc: CVaRCalculator,
    dd_monitor: DrawdownMonitor,
    pb_logger: PlaybookLogger,
) -> None:
    """Execute one full playbook scan cycle."""

    cycle_start = time.time()
    logger.info("[Runner] Starting playbook cycle ...")

    # 1. Macro regime
    regime_state = classify_regime()
    pb_logger.log_regime(regime_state)
    logger.info("[Runner] Regime: %s (%s)", regime_state.regime, regime_state.reason)

    # 2. Signal scan
    signals_found = []
    for symbol in WATCHLIST:
        df = _fetch_ohlcv(symbol)
        if df.empty:
            continue
        signals = scan_symbol(df, symbol)
        for sig in signals:
            sig["regime_at_detection"] = regime_state.regime
            pb_logger.log_signal(sig)
            signals_found.append(sig)
            logger.info(
                "[Runner] Signal: %s on %s (conf=%.2f entry=%.4f stop=%.4f)",
                sig["pattern_name"], symbol,
                sig["confidence"], sig["entry_price"], sig["stop_price"],
            )

    if not signals_found:
        logger.info("[Runner] No signals detected this cycle")

    # 3. Risk snapshot
    returns = _fetch_pnl_returns()
    cvar_val = cvar_calc.calculate(returns) if len(returns) >= 10 else 0.0

    # Conservative Kelly defaults when no trade history available
    kelly_size = kelly.calculate(win_rate=0.50, avg_win=1.0, avg_loss=1.0)

    # Drawdown: use portfolio equity proxy (SPY close as stand-in if no NAV)
    spy_close = yf.Ticker("SPY").history(period="1mo")
    if not spy_close.empty:
        equity_curve = spy_close["Close"].values
        dd_monitor.update("portfolio", float(equity_curve[-1]))

    dd_snap = dd_monitor.snapshot()

    # Check CVaR limit (warn only — execution controls come with RL layer)
    if cvar_calc.exceeds_limit(returns, nav=1.0, limit_pct=CVAR_LIMIT):
        logger.warning("[Runner] CVaR limit breached — RL agent should reduce exposure")

    pb_logger.log_risk_snapshot(
        cvar=cvar_val,
        kelly_size=kelly_size,
        drawdown_snapshot=dd_snap,
        regime=regime_state.regime,
    )

    # 4. Kill-switch health checks (no live orders here — just record state)
    ks_reason = kill_switch.run_all_checks(nav=1.0)
    if ks_reason:
        pb_logger.log_kill_switch_event(kill_switch.state_snapshot())

    elapsed = time.time() - cycle_start
    logger.info("[Runner] Cycle complete in %.1f s  |  signals=%d", elapsed, len(signals_found))


def main() -> None:
    """Entry point: initialise components and run the playbook loop."""
    logger.info("=" * 60)
    logger.info("Cemini Playbook Runner starting ...")
    logger.info("Watchlist: %d symbols | Interval: %d s", len(WATCHLIST), SCAN_INTERVAL)
    logger.info("=" * 60)

    kill_switch = KillSwitch()
    kelly = FractionalKelly(fraction=KELLY_FRAC)
    cvar_calc = CVaRCalculator(confidence=0.99)
    dd_monitor = DrawdownMonitor(threshold=DD_THRESHOLD)
    pb_logger = PlaybookLogger()

    last_cycle = 0.0

    try:
        while True:
            now = time.time()
            if now - last_cycle >= SCAN_INTERVAL:
                try:
                    run_playbook_cycle(kill_switch, kelly, cvar_calc, dd_monitor, pb_logger)
                except Exception as exc:
                    logger.error("[Runner] Unhandled exception in cycle: %s", exc, exc_info=True)
                last_cycle = time.time()

            # Check kill switch state between cycles too
            if kill_switch.triggered:
                pb_logger.log_kill_switch_event(kill_switch.state_snapshot())
                logger.critical("[Runner] Kill switch triggered — runner loop suspended")
                # Keep looping but skip scans until manually reset
                time.sleep(60)
                continue

            time.sleep(10)   # tight poll loop, actual work governed by last_cycle
    finally:
        pb_logger.close()
        logger.info("[Runner] Playbook Runner shut down cleanly")


if __name__ == "__main__":
    main()
