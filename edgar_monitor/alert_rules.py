"""Cemini Financial Suite — EDGAR Alert Rules Engine (Step 17).

Scores each EDGAR filing on a 0-100 significance scale.
Alert threshold: score >= 60 → publish intel:edgar_alert.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from edgar_monitor.models import FilingSignificance

logger = logging.getLogger("edgar_monitor.alert_rules")

ALERT_THRESHOLD = 60

# Base significance score by form type
FILING_WEIGHTS: dict[str, int] = {
    "8-K": 70,      # Material events — high base significance
    "10-K": 40,     # Annual report — important but expected
    "10-Q": 30,     # Quarterly — routine
    "4": 50,        # Insider trade — moderate base, boosted by cluster
    "SC 13G": 45,   # Institutional holdings — moderate
    "SC 13D": 65,   # Activist position — high significance
    "S-1": 80,      # IPO filing — very high
    "DEF 14A": 35,  # Proxy statement — routine
}

# 8-K item number significance boosters (added to base score)
ITEM_8K_BOOSTERS: dict[str, int] = {
    "1.01": 30,  # Entry into Material Agreement
    "1.02": 25,  # Termination of Material Agreement
    "2.01": 20,  # Completion of Acquisition/Disposition
    "2.02": 35,  # Results of Operations (earnings surprise)
    "2.05": 25,  # Costs of Exit/Restructuring
    "2.06": 20,  # Material Impairments
    "3.01": 15,  # Delisting notice
    "4.01": 20,  # Auditor change
    "5.02": 30,  # Executive departure/appointment
    "7.01": 10,  # Reg FD disclosure
    "8.01": 15,  # Other events
}

AFTER_HOURS_BONUS = 10   # Filing detected outside 9:30-16:00 ET
WATCHLIST_BONUS = 10     # Ticker is in the active watchlist

# Core watchlist — SPY components + tracked equities (matches TRACKED_SYMBOLS in edgar_harvester)
_WATCHLIST = frozenset({
    "SPY", "QQQ", "IWM", "DIA",
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL",
    "TSLA", "AMD", "SMCI", "PLTR", "AVGO",
    "COIN", "MSTR", "MARA",
    "JPM", "BAC", "GS",
    "DIS", "NFLX", "UBER",
})


def _is_after_hours(filed_at: datetime) -> bool:
    """Return True if filing timestamp is outside US market hours (9:30–16:00 ET)."""
    # Convert to UTC-based "ET proxy" — offset by 5h during EST, 4h during EDT.
    # Using UTC 14:30–21:00 as approximate market hours (conservative).
    utc_hour = filed_at.astimezone(timezone.utc).hour
    return utc_hour < 14 or utc_hour >= 21


def _extract_item_numbers(description: str) -> list[str]:
    """Extract 8-K item numbers from a filing description string.

    EDGAR primaryDocDescription may contain text like:
    "8-K: 2.02 Results of Operations" or "Item 5.02" or just "8-K".
    Returns list of matched item numbers like ["2.02", "5.02"].
    """
    import re
    # Match patterns like "2.02", "Item 2.02", "item2.02"
    pattern = r"\b(\d\.\d{2})\b"
    return re.findall(pattern, description or "")


def score_filing(
    ticker: str,
    cik: str,
    form_type: str,
    accession_number: str,
    description: str = "",
    filed_at: datetime | None = None,
    item_numbers: list[str] | None = None,
) -> FilingSignificance:
    """Score a filing on a 0-100 significance scale.

    Args:
        ticker: Stock ticker symbol.
        cik: SEC CIK identifier.
        form_type: EDGAR form type (8-K, 10-K, etc.).
        accession_number: Unique EDGAR accession number.
        description: Filing description text (may contain item numbers).
        filed_at: Filing timestamp for after-hours bonus calculation.
        item_numbers: Explicit item numbers list (overrides description parsing).

    Returns:
        FilingSignificance with score and alert_triggered flag.
    """
    boosters: dict[str, int] = {}

    base_score = FILING_WEIGHTS.get(form_type, 20)

    # Extract item numbers from description if not provided explicitly
    if item_numbers is None:
        item_numbers = _extract_item_numbers(description)

    # Apply 8-K item boosters
    if form_type in ("8-K", "8-K/A"):
        for item in item_numbers:
            bonus = ITEM_8K_BOOSTERS.get(item, 0)
            if bonus > 0:
                boosters[f"item_{item}"] = bonus

    # Recency bonus — after-hours filings often move stocks the next morning
    if filed_at is not None and _is_after_hours(filed_at):
        boosters["after_hours"] = AFTER_HOURS_BONUS

    # Watchlist bonus
    if ticker.upper() in _WATCHLIST:
        boosters["watchlist"] = WATCHLIST_BONUS

    total_boost = sum(boosters.values())
    raw_score = base_score + total_boost
    significance_score = max(0, min(100, raw_score))

    alert_triggered = significance_score >= ALERT_THRESHOLD

    logger.debug(
        "Filing scored: %s %s base=%d boost=%d total=%d alert=%s",
        ticker, form_type, base_score, total_boost, significance_score, alert_triggered,
    )

    return FilingSignificance(
        ticker=ticker,
        cik=cik,
        form_type=form_type,
        accession_number=accession_number,
        significance_score=significance_score,
        base_score=base_score,
        boosters=boosters,
        alert_triggered=alert_triggered,
    )
