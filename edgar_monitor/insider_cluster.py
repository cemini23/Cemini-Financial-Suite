"""Cemini Financial Suite — Insider Cluster Detector (Step 17).

Detects coordinated insider buying: 2+ distinct insiders at the same company
purchasing shares within a configurable time window. Cluster buying is one of
the strongest signals in EDGAR data.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import NamedTuple

from edgar_monitor.models import InsiderCluster

logger = logging.getLogger("edgar_monitor.insider_cluster")

# Titles that indicate CEO or CFO (case-insensitive substring match)
_CEO_CFO_TITLES = frozenset({"chief executive", "ceo", "chief financial", "cfo"})


class InsiderTrade(NamedTuple):
    """Lightweight representation of a single insider transaction."""

    ticker: str
    cik: str
    insider_name: str
    title: str  # e.g. "Chief Executive Officer"
    transaction_type: str  # "P" = purchase, "S" = sale
    shares: float
    price_per_share: float
    total_value: float
    filed_at: datetime


def _is_ceo_cfo(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in _CEO_CFO_TITLES)


def _base_cluster_score(insider_count: int) -> int:
    if insider_count >= 3:
        return 85
    return 70  # exactly 2 insiders


def detect_clusters(
    trades: list[InsiderTrade],
    window_days: int = 7,
    min_insiders: int = 2,
    min_total_value: float = 100_000.0,
) -> list[InsiderCluster]:
    """Detect insider buying clusters.

    A cluster = 2+ distinct insiders buying the same ticker within window_days.
    Only purchase transactions ("P") are counted toward cluster detection.

    Scoring bonuses:
    - 3+ insiders buying  → base 85 (vs 70 for exactly 2)
    - CEO/CFO involved    → +15
    - Total value > $500K → +10

    Args:
        trades: List of insider transactions to evaluate.
        window_days: Rolling window in days for cluster detection.
        min_insiders: Minimum distinct insiders required to form a cluster.
        min_total_value: Minimum combined purchase value to qualify.

    Returns:
        List of detected InsiderCluster objects.
    """
    # Group purchases by ticker
    by_ticker: dict[str, list[InsiderTrade]] = defaultdict(list)
    for trade in trades:
        if trade.transaction_type == "P":
            by_ticker[trade.ticker].append(trade)

    clusters: list[InsiderCluster] = []

    for ticker, ticker_trades in by_ticker.items():
        if len(ticker_trades) < min_insiders:
            continue

        # Sort by filing date descending — most recent anchor first so the
        # widest backward window is checked first (catches all in-window trades)
        sorted_trades = sorted(ticker_trades, key=lambda tr: tr.filed_at, reverse=True)

        # Sliding window: for each trade, look for a cluster ending at that trade
        for idx, anchor in enumerate(sorted_trades):
            window_start = anchor.filed_at - timedelta(days=window_days)
            window_trades = [
                tr for tr in ticker_trades
                if window_start <= tr.filed_at <= anchor.filed_at
            ]

            distinct_insiders = list({tr.insider_name for tr in window_trades})
            if len(distinct_insiders) < min_insiders:
                continue

            total_value = sum(tr.total_value for tr in window_trades)
            if total_value < min_total_value:
                continue

            includes_ceo_cfo = any(_is_ceo_cfo(tr.title) for tr in window_trades)

            base_score = _base_cluster_score(len(distinct_insiders))
            bonuses = 0
            if includes_ceo_cfo:
                bonuses += 15
            if total_value > 500_000:
                bonuses += 10
            cluster_score = max(0, min(100, base_score + bonuses))

            earliest = min(tr.filed_at for tr in window_trades)
            latest = max(tr.filed_at for tr in window_trades)

            cluster = InsiderCluster(
                ticker=ticker,
                window_start=earliest,
                window_end=latest,
                insiders=distinct_insiders,
                insider_count=len(distinct_insiders),
                total_value=total_value,
                includes_ceo_cfo=includes_ceo_cfo,
                cluster_score=cluster_score,
                transaction_type="P",
            )
            clusters.append(cluster)
            logger.info(
                "CLUSTER detected: %s — %d insiders, $%.0f total, score=%d",
                ticker, len(distinct_insiders), total_value, cluster_score,
            )
            break  # one cluster per ticker per scan to avoid duplicates

    return clusters
