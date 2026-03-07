"""
opportunity_screener/entity_extractor.py — Ticker Entity Extraction (Step 26.1b)

Two-tier pipeline:
  Tier 1 — Cheap regex extraction (runs on every intel message)
  Tier 2 — LLM entity resolution (stub; wired in Phase 3)

Confidence levels:
  1.0 — $TICKER pattern (explicit dollar-sign prefix)
  0.9 — exact company name match (case-insensitive)
  0.7 — alias map match
  0.5 — contextual / fuzzy

Short tickers that are common English words (A, IT, ALL, ARE, etc.) are only
extracted when preceded by '$' to avoid false positives in prose.
"""
import json
import logging
import re
import time
from pathlib import Path
from typing import Any

from beartype import beartype

from cemini_contracts.discovery import ExtractedTicker

logger = logging.getLogger("screener.entity_extractor")

# ── Constants ────────────────────────────────────────────────────────────────

_DATA_DIR = Path(__file__).parent.parent / "data"

# Tickers ≤3 chars that appear in common English prose — require $PREFIX
_AMBIGUOUS_SHORT = frozenset({
    "A", "AT", "AN", "AS", "BE", "BY", "DO", "GO", "IN", "IS", "IT",
    "NO", "OF", "ON", "OR", "SO", "TO", "UP", "US", "WE", "ALL", "AND",
    "ARE", "BUT", "CAN", "FOR", "GET", "HAS", "HAD", "HIM", "HIS", "HOW",
    "ITS", "MAY", "MET", "NEW", "NOT", "NOW", "OFF", "OLD", "OUT", "OWN",
    "PUT", "RUN", "SAW", "SAY", "SET", "SHE", "THE", "TOO", "TWO", "USE",
    "WAS", "WHO", "WHY", "YET",
    # Financial abbreviations that collide with tickers
    "EPS", "GDP", "IPO", "AUM", "ETF", "NAV", "MOM", "PEG", "RSI",
    "PPI", "CPI", "PMI", "FFR", "ECB", "IMF", "BIS", "SEC", "FTC",
})

# Core tickers always tracked (never evicted)
CORE_TICKERS = {"SPY", "QQQ", "IWM", "DIA", "BTC-USD", "ETH-USD"}

# Regex: $TICKER (explicit)
_DOLLAR_PATTERN = re.compile(r'\$([A-Z]{1,5}(?:\.[A-Z])?|-[A-Z]{1,5})', re.ASCII)
# Regex: bare TICKER — ALL-CAPS word 1-5 chars, with optional .X suffix
# Only matches if surrounded by non-alphanumeric boundaries
_BARE_PATTERN = re.compile(r'(?<![A-Z])([A-Z]{2,5}(?:\.[A-Z])?)(?![A-Z])', re.ASCII)
# Crypto: bare BTC-USD style
_CRYPTO_BARE = re.compile(r'\b(BTC-USD|ETH-USD|SOL-USD|XRP-USD|ADA-USD|DOGE-USD|LTC-USD)\b')


def _load_json(filename: str) -> dict:
    path = _DATA_DIR / filename
    if path.exists():
        with open(path) as f:
            return json.load(f)
    logger.warning("Data file not found: %s", path)
    return {}


def _build_registry() -> frozenset[str]:
    sp500 = _load_json("sp500_tickers.json")
    tickers = set(sp500.get("tickers", []))
    # add core crypto
    tickers.update({"BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD"})
    return frozenset(tickers)


def _build_alias_map() -> dict[str, list[str]]:
    """Returns lower-cased alias → list[canonical_ticker]."""
    raw = _load_json("ticker_aliases.json")
    return {k.lower(): v for k, v in raw.get("aliases", {}).items()}


def _build_company_map() -> dict[str, str]:
    """Returns lower-cased company name → ticker for exact-match extraction."""
    # Subset of high-value names for fast lookup
    return {
        "apple": "AAPL", "microsoft": "MSFT", "nvidia": "NVDA",
        "alphabet": "GOOGL", "google": "GOOGL", "amazon": "AMZN",
        "meta": "META", "tesla": "TSLA", "netflix": "NFLX",
        "salesforce": "CRM", "adobe": "ADBE", "intel": "INTC",
        "qualcomm": "QCOM", "broadcom": "AVGO",
        "jpmorgan": "JPM", "jp morgan": "JPM",
        "bank of america": "BAC", "goldman sachs": "GS",
        "morgan stanley": "MS", "wells fargo": "WFC",
        "citigroup": "C", "blackrock": "BLK",
        "berkshire hathaway": "BRK.B", "berkshire": "BRK.B",
        "johnson & johnson": "JNJ", "pfizer": "PFE", "moderna": "MRNA",
        "eli lilly": "LLY", "abbvie": "ABBV", "merck": "MRK",
        "unitedhealth": "UNH", "walmart": "WMT", "target": "TGT",
        "home depot": "HD", "costco": "COST", "starbucks": "SBUX",
        "disney": "DIS", "exxon": "XOM", "exxonmobil": "XOM",
        "chevron": "CVX", "boeing": "BA", "caterpillar": "CAT",
        "general motors": "GM", "ford": "F", "visa": "V",
        "mastercard": "MA", "paypal": "PYPL", "deere": "DE",
        "lockheed martin": "LMT", "raytheon": "RTX",
    }


# Singletons (module-level, loaded once)
_REGISTRY: frozenset[str] = frozenset()
_ALIAS_MAP: dict[str, list[str]] = {}
_COMPANY_MAP: dict[str, str] = {}
_initialized = False


def _ensure_loaded() -> None:
    global _REGISTRY, _ALIAS_MAP, _COMPANY_MAP, _initialized
    if not _initialized:
        _REGISTRY = _build_registry()
        _ALIAS_MAP = _build_alias_map()
        _COMPANY_MAP = _build_company_map()
        _initialized = True


def _text_from_payload(payload: Any) -> str:
    """Flatten an intel payload to a searchable string."""
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload
    if isinstance(payload, (int, float, bool)):
        return str(payload)
    if isinstance(payload, dict):
        return " ".join(str(v) for v in payload.values() if v is not None)
    if isinstance(payload, list):
        return " ".join(str(x) for x in payload)
    return str(payload)


@beartype
def extract_tickers(
    channel: str,
    payload: Any,
    timestamp: float | None = None,
) -> list[ExtractedTicker]:
    """
    Tier 1 entity extraction. Runs on every intel message.

    Returns list of ExtractedTicker sorted by confidence descending.
    Never raises — returns [] on any error.
    """
    _ensure_loaded()
    ts = timestamp or time.time()
    text = _text_from_payload(payload)
    if not text:
        return []

    results: dict[str, ExtractedTicker] = {}  # symbol → best result

    def _add(symbol: str, confidence: float, method: str) -> None:
        symbol = symbol.upper()
        if symbol not in _REGISTRY:
            return
        if symbol in results and results[symbol].confidence >= confidence:
            return
        results[symbol] = ExtractedTicker(
            symbol=symbol,
            source_channel=channel,
            confidence=confidence,
            extraction_method=method,
            timestamp=ts,
        )

    # 1. $TICKER patterns (confidence 1.0)
    for m in _DOLLAR_PATTERN.finditer(text.upper()):
        sym = m.group(1).lstrip("-")
        _add(sym, 1.0, "dollar_sign")

    # 2. Crypto bare patterns (confidence 0.9)
    for m in _CRYPTO_BARE.finditer(text):
        _add(m.group(1), 0.9, "crypto_bare")

    # 3. Exact company name (confidence 0.9) — search lower-cased text
    lower_text = text.lower()
    for name, ticker in _COMPANY_MAP.items():
        if name in lower_text:
            _add(ticker, 0.9, "company_name")

    # 4. Alias map (confidence 0.7)
    for alias, tickers in _ALIAS_MAP.items():
        if alias in lower_text:
            for t in tickers:
                _add(t, 0.7, "alias")

    # 5. Bare ALL-CAPS tickers (confidence 0.85 — in-registry, not ambiguous)
    # Use uppercase version of text to match ALL-CAPS tickers
    upper_text = text.upper()
    for m in _BARE_PATTERN.finditer(upper_text):
        sym = m.group(1)
        if sym in _AMBIGUOUS_SHORT:
            continue  # skip common words
        if sym in _REGISTRY:
            _add(sym, 0.85, "bare_ticker")

    out = sorted(results.values(), key=lambda x: x.confidence, reverse=True)
    return out


@beartype
def extract_tickers_tier2(
    channel: str,
    payload: Any,
    timestamp: float | None = None,
) -> list[ExtractedTicker]:
    """
    Tier 2 — LLM entity resolution (stub, Phase 3).

    Intended behavior (Phase 3):
    Uses an LLM (Gemini/GPT-4o) to resolve ambiguous entity references,
    identify tickers mentioned indirectly (e.g., 'the Cupertino company' → AAPL),
    extract sentiment polarity per ticker, and identify forward-looking guidance
    signals. Will be wired in Phase 3 when Finnhub/OpenAI keys are available.

    Current behavior: pass-through to Tier 1.
    """
    return extract_tickers(channel, payload, timestamp)
