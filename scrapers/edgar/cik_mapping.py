"""Cemini Financial Suite — EDGAR CIK Mapping (Step 40).

Downloads and caches the SEC's official ticker→CIK mapping.
Provides get_cik(ticker) → zero-padded 10-digit CIK string, or None if unknown.

Source: https://www.sec.gov/files/company_tickers.json
Updated daily by the SEC; Hishel HTTP caching handles 304 Not Modified responses.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("edgar.cik_mapping")

# Module-level in-memory cache: TICKER (upper) → zero-padded 10-digit CIK string
_CIK_MAP: dict[str, str] = {}

CIK_JSON_URL = "https://www.sec.gov/files/company_tickers.json"

EDGAR_HEADERS = {
    "User-Agent": "Cemini Financial Suite admin@cemini.com",
    "Accept-Encoding": "gzip, deflate",
}


def _pad_cik(cik_int: int) -> str:
    """Zero-pad CIK to 10 digits as required by EDGAR data APIs."""
    return str(cik_int).zfill(10)


def _parse_cik_json(data: dict) -> dict[str, str]:
    """Parse company_tickers.json into ticker→padded-CIK mapping.

    SEC format: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}
    """
    result: dict[str, str] = {}
    for entry in data.values():
        ticker = str(entry.get("ticker", "")).upper().strip()
        cik_raw = entry.get("cik_str") or entry.get("cik")
        if ticker and cik_raw is not None:
            try:
                result[ticker] = _pad_cik(int(cik_raw))
            except (ValueError, TypeError):
                logger.warning("Invalid CIK value for ticker %s: %r", ticker, cik_raw)
    return result


async def load_cik_map(client) -> None:
    """Download company_tickers.json and populate the module-level _CIK_MAP.

    Safe to call multiple times — subsequent calls refresh the cache.
    Uses the provided httpx.AsyncClient (Hishel-cached for 304 support).
    Logs a warning and leaves the existing map intact on network errors.
    """
    global _CIK_MAP
    try:
        resp = await client.get(CIK_JSON_URL, headers=EDGAR_HEADERS)
        resp.raise_for_status()
        data = resp.json()
        new_map = _parse_cik_json(data)
        _CIK_MAP = new_map
        logger.info("CIK map loaded: %d tickers", len(_CIK_MAP))
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load CIK map from %s: %s", CIK_JSON_URL, exc)


def get_cik(ticker: str) -> Optional[str]:
    """Return zero-padded 10-digit CIK for ticker, or None if not found.

    Lookup is case-insensitive. Logs WARNING for unknown tickers.
    """
    result = _CIK_MAP.get(ticker.upper().strip())
    if result is None:
        logger.warning("CIK not found for ticker: %s (map size=%d)", ticker, len(_CIK_MAP))
    return result


def get_cik_map_size() -> int:
    """Return current number of tickers in the CIK cache."""
    return len(_CIK_MAP)


def load_cik_map_from_dict(data: dict) -> None:
    """Synchronous loader for testing — populate _CIK_MAP from a pre-parsed dict."""
    global _CIK_MAP
    _CIK_MAP = _parse_cik_json(data)
