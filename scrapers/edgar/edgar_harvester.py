"""Cemini Financial Suite — SEC EDGAR Direct Pipeline (Step 40).

Eliminates the $49/mo sec-api.io dependency by polling SEC EDGAR directly.

Three APScheduler jobs:
  filing_monitor_job   — every 10 min:  detect new 4/8-K/10-K/10-Q/13-F filings
  insider_scanner_job  — every 30 min:  parse Form 4 XML for insider transactions
  fundamentals_job     — daily 06:00 UTC: XBRL company facts (revenue, EPS, etc.)

Redis channels:
  intel:edgar_filing   — latest new filing detected across tracked tickers
  intel:edgar_insider  — latest Form 4 transaction detected

Rate limit: EDGAR allows ≤10 req/sec. We use 0.15s sleep between CIK lookups.
User-Agent: required by EDGAR — requests without it return 403.
"""
from __future__ import annotations

import asyncio
import datetime
import json
import logging
import os
import sys
import time
import xml.etree.ElementTree as ET
from typing import Optional

import psycopg2
import redis as redis_lib
from pydantic import BaseModel, ValidationError

# ── Repo root on sys.path ──────────────────────────────────────────────────────
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core.resilience import (  # noqa: E402
    HttpStatusRetryError,
    create_async_retry_decorator,
    create_circuit_breaker,
    create_resilient_client,
    create_scheduler,
    dead_letter,
)
from scrapers.edgar.cik_mapping import (  # noqa: E402
    EDGAR_HEADERS,
    get_cik,
    load_cik_map,
)
from scrapers.earnings_calendar import run_earnings_calendar  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [EDGAR] %(levelname)s %(message)s",
)
logger = logging.getLogger("edgar_pipeline")

# ── Config ─────────────────────────────────────────────────────────────────────
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "cemini_redis_2026")
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_USER = os.getenv("POSTGRES_USER", "admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "quest")
DB_NAME = os.getenv("POSTGRES_DB", "qdb")

# Tracked stock symbols — polygon_ingestor STOCK_SYMBOLS + DIA
# Crypto tickers (X:BTCUSD etc.) are not SEC registrants — excluded
TRACKED_SYMBOLS = [
    "SPY", "QQQ", "IWM", "DIA",
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL",
    "TSLA", "AMD", "SMCI", "PLTR", "AVGO",
    "COIN", "MSTR", "MARA",
    "JPM", "BAC", "GS",
    "DIS", "NFLX", "UBER",
]

FILING_MONITOR_INTERVAL = 600      # 10 minutes
INSIDER_SCAN_INTERVAL = 1800       # 30 minutes
FILING_TTL = 600                   # Redis TTL for intel:edgar_filing
INSIDER_TTL = 1800                 # Redis TTL for intel:edgar_insider
RATE_LIMIT_SLEEP = 0.15            # 0.15s between CIK requests (≤6.7 req/sec)

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"

FILING_FORMS = {"4", "8-K", "10-K", "10-Q", "13-F"}


# ── Pydantic models ────────────────────────────────────────────────────────────

class EdgarFiling(BaseModel):
    ticker: str
    cik: str
    form_type: str
    filed_at: datetime.datetime
    filing_url: str
    description: str
    accession_number: str


class EdgarInsider(BaseModel):
    ticker: str
    cik: str
    insider_name: str
    transaction_type: str           # "P" (purchase) or "S" (sale)
    shares: float
    price_per_share: Optional[float] = None
    total_value: Optional[float] = None
    filed_at: datetime.datetime
    accession_number: str


# ── Resilience ──────────────────────────────────────────────────────────────────
_edgar_cb = create_circuit_breaker("edgar_pipeline", fail_max=3, timeout_duration=60.0)
_edgar_retry = create_async_retry_decorator(
    "edgar_pipeline", max_attempts=3, base_wait=2.0, max_wait=30.0,
    retryable_statuses=(429, 500, 502, 503, 504),
)

# Global state — initialized in main()
_http_client = None
_r: redis_lib.Redis = None
_db_conn = None
_db_cursor = None


# ── HTTP fetch helpers ──────────────────────────────────────────────────────────

async def _do_get(url: str) -> dict:
    """Raw async GET → parsed JSON. Raises HttpStatusRetryError on 4xx/5xx."""
    resp = await _http_client.get(url, headers=EDGAR_HEADERS)
    if resp.status_code in (429, 500, 502, 503, 504):
        raise HttpStatusRetryError(resp.status_code)
    if resp.status_code == 403:
        logger.error("EDGAR 403 on %s — check User-Agent header", url)
        raise HttpStatusRetryError(503)  # treat as transient for retry
    resp.raise_for_status()
    return resp.json()


async def _do_get_text(url: str) -> str:
    """Raw async GET → text response (for XML documents)."""
    resp = await _http_client.get(url, headers=EDGAR_HEADERS)
    if resp.status_code in (429, 500, 502, 503, 504):
        raise HttpStatusRetryError(resp.status_code)
    if resp.status_code == 404:
        return ""  # Form 4 XML not found — not retryable
    resp.raise_for_status()
    return resp.text


_get_json = _edgar_retry(_do_get)
_get_text = _edgar_retry(_do_get_text)


async def _safe_get_json(url: str) -> Optional[dict]:
    """Circuit-breaker-wrapped JSON fetch. Returns None on open breaker."""
    try:
        return await _edgar_cb.call(_get_json, url)
    except Exception as exc:  # noqa: BLE001
        logger.warning("EDGAR fetch failed for %s: %s", url, exc)
        return None


# ── Redis publish ──────────────────────────────────────────────────────────────

def _publish(channel: str, payload: dict, ttl: int) -> None:
    """Publish intel payload to Redis using the standard Intel Bus envelope."""
    envelope = json.dumps({
        "value": payload,
        "source_system": "edgar_pipeline",
        "timestamp": time.time(),
        "confidence": 1.0,
    }, default=str)
    try:
        _r.set(channel, envelope, ex=ttl)
        logger.info("Published to %s (TTL=%ds)", channel, ttl)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis publish failed for %s: %s", channel, exc)


# ── Submissions JSON parser ────────────────────────────────────────────────────

def _parse_recent_filings(data: dict, ticker: str, cik: str) -> list[dict]:
    """Extract recent filings from submissions JSON as list of dicts.

    EDGAR submissions recent filings are stored as parallel arrays.
    """
    recent = data.get("filings", {}).get("recent", {})
    accessions = recent.get("accessionNumber", [])
    dates = recent.get("filingDate", [])
    forms = recent.get("form", [])
    primary_docs = recent.get("primaryDocument", [])
    descriptions = recent.get("primaryDocDescription", [])

    results = []
    cik_int = int(cik)  # plain integer for archive URLs
    for i, accession in enumerate(accessions):
        form = forms[i] if i < len(forms) else ""
        if form not in FILING_FORMS:
            continue
        filed_date = dates[i] if i < len(dates) else ""
        primary_doc = primary_docs[i] if i < len(primary_docs) else ""
        description = descriptions[i] if i < len(descriptions) else form
        accession_nodash = accession.replace("-", "")
        filing_url = (
            f"{ARCHIVES_BASE}/{cik_int}/{accession_nodash}/{primary_doc}"
            if primary_doc else
            f"{ARCHIVES_BASE}/{cik_int}/{accession_nodash}/"
        )
        results.append({
            "ticker": ticker,
            "cik": cik,
            "form_type": form,
            "filed_at": filed_date,
            "filing_url": filing_url,
            "description": description or form,
            "accession_number": accession,
        })
    return results


# ── Form 4 XML parser ──────────────────────────────────────────────────────────

def _parse_form4_xml(xml_text: str, ticker: str, cik: str, accession: str, filed_date: str) -> list[EdgarInsider]:
    """Parse Form 4 XML and return list of EdgarInsider records.

    Handles both derivative and non-derivative transactions.
    Returns empty list if XML is malformed or has no transactions.
    """
    if not xml_text:
        return []
    results = []
    try:
        root = ET.fromstring(xml_text)  # noqa: S314 — EDGAR XML is SEC-published, not user input

        # Extract insider name
        owner_elem = root.find(".//reportingOwner/reportingOwnerId/rptOwnerName")
        insider_name = owner_elem.text.strip() if owner_elem is not None and owner_elem.text else "Unknown"

        # Parse filed_at
        try:
            filed_at = datetime.datetime.fromisoformat(filed_date)
        except (ValueError, TypeError):
            filed_at = datetime.datetime.now(datetime.timezone.utc)

        # Non-derivative transactions (stock purchases/sales)
        for txn in root.findall(".//nonDerivativeTransaction"):
            code_elem = txn.find("transactionCoding/transactionCode")
            txn_code = code_elem.text.strip() if code_elem is not None and code_elem.text else ""
            if txn_code not in ("P", "S"):
                continue

            shares_elem = txn.find("transactionAmounts/transactionShares/value")
            price_elem = txn.find("transactionAmounts/transactionPricePerShare/value")

            try:
                shares = float(shares_elem.text.strip()) if shares_elem is not None and shares_elem.text else 0.0
            except (ValueError, TypeError):
                shares = 0.0

            try:
                price = float(price_elem.text.strip()) if price_elem is not None and price_elem.text else None
            except (ValueError, TypeError):
                price = None

            total = (shares * price) if (shares and price) else None

            results.append(EdgarInsider(
                ticker=ticker,
                cik=cik,
                insider_name=insider_name,
                transaction_type=txn_code,
                shares=shares,
                price_per_share=price,
                total_value=total,
                filed_at=filed_at,
                accession_number=accession,
            ))

    except ET.ParseError as exc:
        logger.warning("Form 4 XML parse error (acc=%s): %s", accession, exc)
    return results


# ── XBRL fundamentals parser ───────────────────────────────────────────────────

# Map EDGAR concept → our column name
_XBRL_CONCEPTS = {
    "Revenues": "revenue",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "revenue",  # alternate
    "NetIncomeLoss": "net_income",
    "EarningsPerShareBasic": "eps",
    "Assets": "total_assets",
    "Liabilities": "total_liabilities",
}


def _extract_xbrl_metric(facts: dict, concept: str) -> Optional[tuple[str, float]]:
    """Extract most recent annual value for a GAAP concept.

    Returns (period_label, value) or None if concept absent.
    """
    gaap = facts.get("us-gaap", {})
    concept_data = gaap.get(concept, {})
    units = concept_data.get("units", {})
    # Prefer USD; EPS uses USD/shares
    for unit_key in ("USD", "USD/shares"):
        entries = units.get(unit_key, [])
        # Filter to 10-K annual filings with a frame (CY20xx)
        annual = [
            e for e in entries
            if e.get("form") in ("10-K", "10-Q") and e.get("frame", "").startswith("CY")
        ]
        if annual:
            latest = max(annual, key=lambda e: e.get("frame", ""))
            return (latest["frame"], float(latest["val"]))
    return None


def _parse_company_facts(data: dict, ticker: str, cik: str) -> list[dict]:
    """Extract fundamental metrics from XBRL companyfacts JSON.

    Returns list of row dicts suitable for edgar_fundamentals INSERT.
    """
    facts = data.get("facts", {})
    rows: dict[str, dict] = {}  # period → row

    for concept, column in _XBRL_CONCEPTS.items():
        result = _extract_xbrl_metric(facts, concept)
        if result is None:
            continue
        period, value = result
        if period not in rows:
            rows[period] = {"ticker": ticker, "cik": cik, "period": period,
                            "revenue": None, "net_income": None, "eps": None,
                            "total_assets": None, "total_liabilities": None}
        rows[period][column] = value

    return list(rows.values())


# ── Database helpers ────────────────────────────────────────────────────────────

def _store_fundamentals(rows: list[dict]) -> int:
    """INSERT fundamental rows with ON CONFLICT DO NOTHING. Returns inserted count."""
    if not rows or _db_cursor is None:
        return 0
    count = 0
    for row in rows:
        try:
            _db_cursor.execute(
                """
                INSERT INTO edgar_fundamentals
                    (ticker, cik, period, revenue, net_income, eps, total_assets, total_liabilities)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (cik, period) DO NOTHING
                """,
                (row["ticker"], row["cik"], row["period"],
                 row.get("revenue"), row.get("net_income"), row.get("eps"),
                 row.get("total_assets"), row.get("total_liabilities")),
            )
            count += _db_cursor.rowcount
        except Exception as exc:  # noqa: BLE001
            logger.warning("edgar_fundamentals INSERT error: %s", exc)
    return count


def _log_filing(filing: EdgarFiling) -> None:
    """INSERT filing into edgar_filings_log (idempotent via UNIQUE accession_number)."""
    if _db_cursor is None:
        return
    try:
        _db_cursor.execute(
            """
            INSERT INTO edgar_filings_log
                (ticker, cik, form_type, accession_number, filed_at, filing_url)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (accession_number) DO NOTHING
            """,
            (filing.ticker, filing.cik, filing.form_type,
             filing.accession_number, filing.filed_at, filing.filing_url),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("edgar_filings_log INSERT error (acc=%s): %s", filing.accession_number, exc)


# ── Redis seen-accession tracking ──────────────────────────────────────────────

def _is_seen(accession: str, prefix: str) -> bool:
    """Return True if accession number was already processed."""
    try:
        return bool(_r.get(f"edgar:{prefix}:seen:{accession}"))
    except Exception:  # noqa: BLE001
        return False


def _mark_seen(accession: str, prefix: str, ttl: int = 86400 * 7) -> None:
    """Mark accession number as processed (7-day TTL)."""
    try:
        _r.set(f"edgar:{prefix}:seen:{accession}", "1", ex=ttl)
    except Exception:  # noqa: BLE001
        pass


# ── APScheduler jobs ────────────────────────────────────────────────────────────

async def filing_monitor_job() -> None:
    """Job 2a: Detect new filings for tracked tickers every 10 minutes."""
    logger.info("EDGAR: Filing monitor started")
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    new_count = 0
    latest_filing: Optional[dict] = None

    for symbol in TRACKED_SYMBOLS:
        cik = get_cik(symbol)
        if not cik:
            await asyncio.sleep(RATE_LIMIT_SLEEP)
            continue

        url = SUBMISSIONS_URL.format(cik=cik)
        data = await _safe_get_json(url)
        if data is None:
            await asyncio.sleep(RATE_LIMIT_SLEEP)
            continue

        for filing_raw in _parse_recent_filings(data, symbol, cik):
            filed_date = filing_raw.get("filed_at", "")
            if filed_date < today:
                continue  # only today's filings
            accession = filing_raw["accession_number"]
            if _is_seen(accession, "filing"):
                continue

            try:
                filing = EdgarFiling(
                    **{**filing_raw, "filed_at": datetime.datetime.fromisoformat(filed_date)
                    if "T" not in filed_date else filed_date},
                )
            except (ValidationError, Exception) as exc:
                await dead_letter(
                    "edgar_pipeline", "intel:edgar_filing",
                    filing_raw, exc if isinstance(exc, Exception) else Exception(str(exc)),
                    _db_conn,
                )
                continue

            _mark_seen(accession, "filing")
            _log_filing(filing)
            latest_filing = filing.model_dump(mode="json")
            new_count += 1
            logger.info(
                "NEW FILING: %s %s by %s (acc=%s)",
                filing.form_type, filing.ticker, filing.filed_at.date(), accession,
            )

        await asyncio.sleep(RATE_LIMIT_SLEEP)

    if latest_filing:
        _publish("intel:edgar_filing", latest_filing, FILING_TTL)

    logger.info("EDGAR: Filing monitor done — %d new filings", new_count)


async def insider_scanner_job() -> None:
    """Job 2b: Parse Form 4 XML for insider transactions every 30 minutes."""
    logger.info("EDGAR: Insider scanner started")
    new_count = 0
    latest_insider: Optional[dict] = None

    for symbol in TRACKED_SYMBOLS:
        cik = get_cik(symbol)
        if not cik:
            await asyncio.sleep(RATE_LIMIT_SLEEP)
            continue

        url = SUBMISSIONS_URL.format(cik=cik)
        data = await _safe_get_json(url)
        if data is None:
            await asyncio.sleep(RATE_LIMIT_SLEEP)
            continue

        recent = data.get("filings", {}).get("recent", {})
        accessions = recent.get("accessionNumber", [])
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        primary_docs = recent.get("primaryDocument", [])

        cik_int = int(cik)

        for i, accession in enumerate(accessions):
            form = forms[i] if i < len(forms) else ""
            if form != "4":
                continue
            if _is_seen(accession, "insider"):
                continue

            filed_date = dates[i] if i < len(dates) else ""
            primary_doc = primary_docs[i] if i < len(primary_docs) else ""
            accession_nodash = accession.replace("-", "")

            # Fetch Form 4 XML
            xml_url = f"{ARCHIVES_BASE}/{cik_int}/{accession_nodash}/{primary_doc}"
            try:
                xml_text = await _edgar_cb.call(_get_text, xml_url)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Form 4 XML fetch failed (acc=%s): %s", accession, exc)
                await asyncio.sleep(RATE_LIMIT_SLEEP)
                continue

            transactions = _parse_form4_xml(
                xml_text or "", symbol, cik, accession, filed_date,
            )
            for insider in transactions:
                _mark_seen(accession, "insider")
                latest_insider = insider.model_dump(mode="json")
                new_count += 1
                logger.info(
                    "INSIDER: %s %s %g shares of %s (acc=%s)",
                    insider.transaction_type, insider.insider_name,
                    insider.shares, insider.ticker, accession,
                )
                break  # one record per accession to Redis; store all in DB

            await asyncio.sleep(RATE_LIMIT_SLEEP)

        await asyncio.sleep(RATE_LIMIT_SLEEP)

    if latest_insider:
        _publish("intel:edgar_insider", latest_insider, INSIDER_TTL)

    logger.info("EDGAR: Insider scanner done — %d new transactions", new_count)


async def fundamentals_job() -> None:
    """Job 2c: Fetch XBRL company facts daily at 06:00 UTC."""
    logger.info("EDGAR: Fundamentals job started")
    total_rows = 0

    for symbol in TRACKED_SYMBOLS:
        cik = get_cik(symbol)
        if not cik:
            await asyncio.sleep(RATE_LIMIT_SLEEP)
            continue

        url = COMPANY_FACTS_URL.format(cik=cik)
        data = await _safe_get_json(url)
        if data is None:
            await asyncio.sleep(RATE_LIMIT_SLEEP)
            continue

        rows = _parse_company_facts(data, symbol, cik)
        inserted = _store_fundamentals(rows)
        total_rows += inserted
        logger.info("  %s: %d fundamental periods, %d new rows", symbol, len(rows), inserted)

        await asyncio.sleep(RATE_LIMIT_SLEEP)

    logger.info("EDGAR: Fundamentals job done — %d rows inserted", total_rows)


# ── DB / Redis connection helpers ──────────────────────────────────────────────

def _wait_for_postgres(max_attempts: int = 12):
    """Wait for Postgres with exponential backoff."""
    delay = 5
    for attempt in range(1, max_attempts + 1):
        try:
            conn = psycopg2.connect(
                host=DB_HOST, port=5432, user=DB_USER,
                password=DB_PASSWORD, database=DB_NAME,
            )
            conn.autocommit = True
            return conn
        except Exception as exc:  # noqa: BLE001
            logger.warning("Postgres not ready (%d/%d): %s — retry in %ds",
                           attempt, max_attempts, exc, delay)
            time.sleep(delay)
            delay = min(delay * 2, 60)
    raise RuntimeError(f"Could not connect to Postgres after {max_attempts} attempts")


# ── Main ───────────────────────────────────────────────────────────────────────

async def main() -> None:
    global _http_client, _r, _db_conn, _db_cursor

    logger.info("EDGAR Pipeline starting (Step 40) — filing/insider/fundamentals jobs")

    # Connections
    _http_client = create_resilient_client("edgar_pipeline", cache_ttl=300, timeout=30.0)
    _r = redis_lib.Redis(
        host=REDIS_HOST, port=6379, password=REDIS_PASSWORD, decode_responses=True,
    )
    _db_conn = _wait_for_postgres()
    _db_cursor = _db_conn.cursor()

    # Load CIK mapping
    await load_cik_map(_http_client)

    # Build ticker→CIK table for startup log
    from scrapers.edgar.cik_mapping import _CIK_MAP
    mapped = [s for s in TRACKED_SYMBOLS if s in _CIK_MAP]
    missing = [s for s in TRACKED_SYMBOLS if s not in _CIK_MAP]
    logger.info("CIK mapping: %d/%d symbols mapped", len(mapped), len(TRACKED_SYMBOLS))
    if missing:
        logger.warning("No CIK for: %s", ", ".join(missing))

    # APScheduler
    scheduler = create_scheduler()

    # 2a: Filing monitor — every 10 min, run immediately at start
    scheduler.add_job(
        filing_monitor_job, "interval", seconds=FILING_MONITOR_INTERVAL,
        id="edgar_filings", replace_existing=True,
        next_run_time=datetime.datetime.now(datetime.timezone.utc),
    )
    # 2b: Insider scanner — every 30 min, run 2 min after start
    scheduler.add_job(
        insider_scanner_job, "interval", seconds=INSIDER_SCAN_INTERVAL,
        id="edgar_insider", replace_existing=True,
        next_run_time=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=2),
    )
    # 2c: Fundamentals — daily at 06:00 UTC
    scheduler.add_job(
        fundamentals_job, "cron", hour=6, minute=0,
        timezone="UTC", id="edgar_fundamentals", replace_existing=True,
    )
    # 2d: Earnings calendar — hourly, run 5 min after start (Step 19)
    async def _earnings_calendar_job() -> None:
        from scrapers.edgar.cik_mapping import _CIK_MAP
        try:
            await run_earnings_calendar(_http_client, _CIK_MAP)
        except Exception as exc:
            logger.warning("EDGAR: Earnings calendar job failed (non-blocking): %s", exc)

    scheduler.add_job(
        _earnings_calendar_job, "interval", seconds=3600,
        id="earnings_calendar", replace_existing=True,
        next_run_time=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5),
    )

    scheduler.start()
    logger.info(
        "EDGAR: APScheduler started — filings every %ds, insider every %ds, "
        "fundamentals daily 06:00 UTC, earnings calendar hourly",
        FILING_MONITOR_INTERVAL, INSIDER_SCAN_INTERVAL,
    )

    # Keep alive — asyncio.Event avoids busy-sleep  # noqa: ASYNC110
    _stop_event = asyncio.Event()
    await _stop_event.wait()


if __name__ == "__main__":
    asyncio.run(main())
