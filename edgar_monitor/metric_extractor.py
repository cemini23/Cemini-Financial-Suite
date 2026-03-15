"""Cemini Financial Suite — 8-K Metric Extractor (Step 17).

Extracts structured, actionable metrics from EDGAR filing payloads.
Uses form_type and item numbers — full NLP text extraction deferred to Step 23 (Finnhub).
"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger("edgar_monitor.metric_extractor")

# Item number → event type mapping
_ITEM_EVENT_MAP: dict[str, str] = {
    "2.02": "earnings",               # Results of Operations
    "2.01": "acquisition",            # Completion of Acquisition/Disposition
    "1.01": "material_agreement",     # Entry into Material Agreement
    "1.02": "agreement_terminated",   # Termination of Material Agreement
    "2.05": "restructuring",          # Costs of Exit/Restructuring
    "2.06": "impairment",             # Material Impairments
    "3.01": "delisting",              # Delisting notice
    "4.01": "auditor_change",         # Change in Auditor
    "5.02": "executive_change",       # Executive departure/appointment
    "7.01": "reg_fd",                 # Reg FD disclosure
    "8.01": "other",                  # Other events
}

_ITEM_PATTERN = re.compile(r"\b(\d\.\d{2})\b")


def _parse_item_numbers(description: str) -> list[str]:
    """Extract item numbers from a description string."""
    return _ITEM_PATTERN.findall(description or "")


def extract_8k_metrics(filing: dict) -> dict:
    """Extract actionable metrics from an 8-K filing payload dict.

    Accepts a dict with at minimum: form_type, description, and optionally
    item_numbers (list[str]).

    Returns a metrics dict with at minimum an "event_type" key when items
    are identified. Returns an empty dict for non-8-K filings or when no
    recognisable item numbers are found.
    """
    form_type = filing.get("form_type", "")
    if form_type not in ("8-K", "8-K/A"):
        return {}

    item_numbers: list[str] = filing.get("item_numbers") or _parse_item_numbers(
        filing.get("description", "")
    )

    if not item_numbers:
        return {}

    metrics: dict = {}

    # Determine primary event type (use first recognised item)
    for item in item_numbers:
        event_type = _ITEM_EVENT_MAP.get(item)
        if event_type and "event_type" not in metrics:
            metrics["event_type"] = event_type

    metrics["item_numbers"] = item_numbers
    metrics["item_count"] = len(item_numbers)

    logger.debug(
        "Extracted 8-K metrics for %s: event_type=%s items=%s",
        filing.get("ticker", "?"),
        metrics.get("event_type"),
        item_numbers,
    )
    return metrics
