"""
Cemini Financial Suite — Earnings Calendar Integration (Step 19)

Estimates upcoming earnings dates for tracked equities by analysing
historical 10-Q / 10-K filing cadence from SEC EDGAR submissions.

Data source: https://data.sec.gov/submissions/CIK{cik:010d}.json
No paid subscriptions required — EDGAR submissions API is free.

Published to: intel:earnings_calendar (TTL=7200, refresh every hour)
Wired into: scrapers/edgar/edgar_harvester.py as 4th APScheduler job

Architecture:
  1. For each tracked ticker, fetch submissions JSON (via shared http_client)
  2. Extract all 10-Q / 10-K dates → compute historical quarterly cadence
  3. Estimate next filing date (last_date + avg_interval)
  4. Classify: REPORTING_THIS_WEEK (≤3d) / REPORTING_SOON (≤7d)
              JUST_REPORTED (≤3d ago) / CLEAR
  5. Detect earnings cluster: >2 of top ETF holdings reporting same week
  6. Publish EarningsCalendarIntel to Intel Bus
"""

from __future__ import annotations

import asyncio
import logging
import math
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from statistics import mean, stdev
from typing import Optional

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from cemini_contracts._compat import safe_dump
from cemini_contracts.earnings import EarningsCalendarIntel, EarningsEvent
from core.intel_bus import IntelPublisher

logger = logging.getLogger("earnings_calendar")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EARNINGS_CALENDAR_INTEL_KEY = "intel:earnings_calendar"
EARNINGS_CALENDAR_TTL = 7200  # 2 hours; refresh every 1 hour so TTL > refresh
SOURCE_SYSTEM = "earnings_calendar"

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
EDGAR_HEADERS = {
    "User-Agent": "Cemini Financial Suite admin@cemini.com",
    "Accept-Encoding": "gzip, deflate",
}

RATE_LIMIT_SLEEP = 0.12  # EDGAR allows ≤10 req/sec; 0.12s ≈ 8.3 req/sec

# Equity symbols that have SEC filings (ETFs excluded)
EQUITY_SYMBOLS: list[str] = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL",
    "TSLA", "AMD", "SMCI", "PLTR", "AVGO",
    "COIN", "MSTR", "MARA",
    "JPM", "BAC", "GS",
    "DIS", "NFLX", "UBER",
    "QQQ",  # QQQ is a trust with some SEC filings; include for cluster detection via holdings
]

# ETFs that don't file earnings themselves — top 5 holdings tracked for cluster detection
ETF_TOP_HOLDINGS: dict[str, list[str]] = {
    "SPY": ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"],
    "QQQ": ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"],
    "IWM": ["SMCI", "MARA", "PLTR", "COIN", "AMD"],
    "DIA": ["JPM", "GS", "MSFT", "AMZN", "AAPL"],
}
ETF_SYMBOLS: frozenset[str] = frozenset(ETF_TOP_HOLDINGS.keys())

# All unique symbols to track for earnings (equities only, deduplicated)
TRACKED_FOR_EARNINGS: list[str] = sorted(
    {sym for sym in EQUITY_SYMBOLS if sym not in ETF_SYMBOLS}
    | {sym for holdings in ETF_TOP_HOLDINGS.values() for sym in holdings}
)

# Window thresholds (calendar days)
THIS_WEEK_DAYS = 3
SOON_DAYS = 7
JUST_REPORTED_DAYS = 3

# Minimum historical filings to compute cadence reliably
MIN_FILINGS_FOR_CADENCE = 2
# Typical quarterly filing interval (fallback when history is thin)
DEFAULT_QUARTERLY_INTERVAL = 91  # ~3 months


# ---------------------------------------------------------------------------
# Pure helper functions (fully testable without network/Redis)
# ---------------------------------------------------------------------------


def extract_quarterly_dates(submissions_data: dict) -> list[date]:
    """Extract 10-Q and 10-K filing dates from EDGAR submissions JSON.

    Returns dates sorted ascending. Duplicates removed.
    Returns empty list if data is malformed or no earnings filings found.
    """
    try:
        recent = submissions_data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates_raw = recent.get("filingDate", [])
    except (AttributeError, TypeError):
        return []

    seen: set[date] = set()
    results: list[date] = []
    for idx, form in enumerate(forms):
        if form not in ("10-Q", "10-K"):
            continue
        if idx >= len(dates_raw):
            continue
        raw_date = dates_raw[idx]
        try:
            parsed = date.fromisoformat(str(raw_date))
            if parsed not in seen:
                seen.add(parsed)
                results.append(parsed)
        except (ValueError, TypeError):
            continue

    return sorted(results)


def estimate_next_earnings(
    historical_dates: list[date],
    today: Optional[date] = None,
) -> tuple[Optional[date], float]:
    """Estimate the next earnings date from historical 10-Q/10-K cadence.

    Returns (estimated_date, confidence).
    confidence: 0.0 (no data) → 1.0 (very regular cadence, many filings).

    Algorithm:
      - With 0 dates: (None, 0.0)
      - With 1 date: last_date + DEFAULT_QUARTERLY_INTERVAL, confidence=0.3
      - With 2+ dates: compute avg interval, confidence from CoV of intervals
        (low coefficient of variation → high confidence)
    """
    if today is None:
        today = date.today()

    if not historical_dates:
        return None, 0.0

    last_date = historical_dates[-1]

    if len(historical_dates) == 1:
        estimated = last_date + timedelta(days=DEFAULT_QUARTERLY_INTERVAL)
        # If already past, advance by another quarter
        while estimated <= today:
            estimated += timedelta(days=DEFAULT_QUARTERLY_INTERVAL)
        return estimated, 0.3

    # Compute intervals between consecutive filings
    intervals = [
        (historical_dates[i + 1] - historical_dates[i]).days
        for i in range(len(historical_dates) - 1)
    ]
    avg_interval = mean(intervals)

    # Confidence: 1 - normalized CoV (lower variation = higher confidence)
    if len(intervals) >= 2 and avg_interval > 0:
        try:
            std = stdev(intervals)
            cov = std / avg_interval  # coefficient of variation
            confidence = max(0.0, min(1.0, 1.0 - cov))
        except Exception:
            confidence = 0.5
    else:
        confidence = 0.5  # only 1 interval; reasonable estimate but uncertain

    # Project forward from last filing date
    estimated = last_date + timedelta(days=round(avg_interval))
    # Advance past today if already historical
    while estimated <= today:
        estimated += timedelta(days=round(avg_interval))

    return estimated, round(confidence, 3)


def classify_earnings_status(
    estimated_next: Optional[date],
    last_filing_date: Optional[date],
    today: Optional[date] = None,
) -> tuple[str, Optional[int]]:
    """Return (status, days_until_earnings).

    Priority order: JUST_REPORTED > REPORTING_THIS_WEEK > REPORTING_SOON > CLEAR
    days_until_earnings is None if no estimate is available.
    """
    if today is None:
        today = date.today()

    # Check JUST_REPORTED: recent filing within last N days
    if last_filing_date is not None:
        days_since = (today - last_filing_date).days
        if 0 <= days_since <= JUST_REPORTED_DAYS:
            return "JUST_REPORTED", None

    if estimated_next is None:
        return "CLEAR", None

    days_until = (estimated_next - today).days

    if days_until < 0:
        # Estimate is in the past — couldn't project properly
        return "CLEAR", None
    if days_until <= THIS_WEEK_DAYS:
        return "REPORTING_THIS_WEEK", days_until
    if days_until <= SOON_DAYS:
        return "REPORTING_SOON", days_until

    return "CLEAR", days_until


def detect_earnings_cluster(events: dict[str, EarningsEvent]) -> bool:
    """Return True if more than 2 ETF top holdings are reporting in the same week.

    Checks across all ETF_TOP_HOLDINGS sets. A holding counts as "reporting"
    if status is REPORTING_THIS_WEEK or REPORTING_SOON.
    """
    active_statuses = {"REPORTING_THIS_WEEK", "REPORTING_SOON"}
    for etf, holdings in ETF_TOP_HOLDINGS.items():
        count = sum(
            1 for sym in holdings
            if sym in events and events[sym].status in active_statuses
        )
        if count > 2:
            return True
    return False


# ---------------------------------------------------------------------------
# Async fetch functions (wired to edgar_harvester's http_client)
# ---------------------------------------------------------------------------


async def _fetch_submissions(http_client, cik: str) -> Optional[dict]:
    """Fetch EDGAR submissions JSON for a CIK. Returns None on any failure."""
    url = SUBMISSIONS_URL.format(cik=cik)
    try:
        resp = await http_client.get(url, headers=EDGAR_HEADERS)
        if resp.status_code != 200:
            logger.debug("[EarningsCal] Non-200 for CIK %s: %d", cik, resp.status_code)
            return None
        return resp.json()
    except Exception as exc:
        logger.debug("[EarningsCal] Fetch failed for CIK %s: %s", cik, exc)
        return None


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------


async def run_earnings_calendar(
    http_client,
    cik_map: dict[str, str],
    today: Optional[date] = None,
) -> Optional[EarningsCalendarIntel]:
    """Scan tracked symbols for upcoming earnings and publish to Intel Bus.

    Args:
        http_client: async httpx/Hishel client (shared from edgar_harvester).
        cik_map: ticker→padded-CIK mapping (from edgar_harvester._CIK_MAP).
        today: override date for testing.

    Returns:
        EarningsCalendarIntel, or None on complete failure.
    """
    if today is None:
        today = date.today()

    start = time.time()
    logger.info("[EarningsCal] Starting scan for %d symbols", len(TRACKED_FOR_EARNINGS))

    events: dict[str, EarningsEvent] = {}

    for symbol in TRACKED_FOR_EARNINGS:
        cik = cik_map.get(symbol)
        if not cik:
            logger.debug("[EarningsCal] No CIK for %s — skipped", symbol)
            await asyncio.sleep(RATE_LIMIT_SLEEP)
            continue

        data = await _fetch_submissions(http_client, cik)
        await asyncio.sleep(RATE_LIMIT_SLEEP)

        if data is None:
            continue

        company_name = data.get("name", symbol)
        dates = extract_quarterly_dates(data)

        last_date = dates[-1] if dates else None
        last_type: Optional[str] = None
        if last_date and data:
            # Find the form type of the last filing
            try:
                recent = data.get("filings", {}).get("recent", {})
                forms = recent.get("form", [])
                date_strs = recent.get("filingDate", [])
                last_str = str(last_date)
                for idx, ds in enumerate(date_strs):
                    if ds == last_str and idx < len(forms) and forms[idx] in ("10-Q", "10-K"):
                        last_type = forms[idx]
                        break
            except Exception:
                pass

        estimated_next, confidence = estimate_next_earnings(dates, today)
        status, days_until = classify_earnings_status(estimated_next, last_date, today)

        events[symbol] = EarningsEvent(
            symbol=symbol,
            cik=cik,
            company_name=company_name,
            last_filing_date=last_date,
            last_filing_type=last_type,
            estimated_next_date=estimated_next,
            days_until_earnings=days_until,
            status=status,
            confidence=confidence,
        )

    if not events:
        logger.warning("[EarningsCal] No events computed — check CIK mapping")
        return None

    # Aggregate into calendar
    reporting_this_week = [s for s, e in events.items() if e.status == "REPORTING_THIS_WEEK"]
    reporting_soon = [s for s, e in events.items() if e.status == "REPORTING_SOON"]
    just_reported = [s for s, e in events.items() if e.status == "JUST_REPORTED"]
    cluster = detect_earnings_cluster(events)

    intel = EarningsCalendarIntel(
        timestamp=datetime.now(timezone.utc),
        reporting_this_week=sorted(reporting_this_week),
        reporting_soon=sorted(reporting_soon),
        just_reported=sorted(just_reported),
        earnings_cluster=cluster,
        events=events,
        total_tracked=len(events),
    )

    # Publish to Intel Bus — serialize events as plain dicts for Redis
    intel_value = {
        "reporting_this_week": intel.reporting_this_week,
        "reporting_soon": intel.reporting_soon,
        "just_reported": intel.just_reported,
        "earnings_cluster": intel.earnings_cluster,
        "total_tracked": intel.total_tracked,
        "timestamp": intel.timestamp.isoformat(),
        "events": {
            sym: {
                "symbol": ev.symbol,
                "cik": ev.cik,
                "company_name": ev.company_name,
                "last_filing_date": str(ev.last_filing_date) if ev.last_filing_date else None,
                "last_filing_type": ev.last_filing_type,
                "estimated_next_date": str(ev.estimated_next_date) if ev.estimated_next_date else None,
                "days_until_earnings": ev.days_until_earnings,
                "status": ev.status,
                "confidence": ev.confidence,
            }
            for sym, ev in intel.events.items()
        },
    }

    IntelPublisher.publish(
        key=EARNINGS_CALENDAR_INTEL_KEY,
        value=intel_value,
        source_system=SOURCE_SYSTEM,
        confidence=1.0,
        ttl=EARNINGS_CALENDAR_TTL,
    )

    elapsed = time.time() - start
    logger.info(
        "[EarningsCal] Done in %.1fs | tracked=%d this_week=%d soon=%d just_reported=%d cluster=%s",
        elapsed,
        len(events),
        len(reporting_this_week),
        len(reporting_soon),
        len(just_reported),
        cluster,
    )

    return intel
