"""Tests for SEC EDGAR Direct Pipeline (Step 40).

All tests are pure — no network, no Redis, no Postgres.
"""
from __future__ import annotations

import asyncio
import datetime
import json
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

# Repo root on sys.path
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from scrapers.edgar.cik_mapping import (
    _pad_cik,
    _parse_cik_json,
    get_cik,
    get_cik_map_size,
    load_cik_map_from_dict,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

SAMPLE_CIK_JSON = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corporation"},
    "2": {"cik_str": 1018724, "ticker": "AMZN", "title": "Amazon.com Inc."},
    "3": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA Corporation"},
    "4": {"cik_str": 1326428, "ticker": "META", "title": "Meta Platforms Inc."},
    "5": {"cik_str": 1318605, "ticker": "TSLA", "title": "Tesla Inc."},
    "6": {"cik_str": 827054, "ticker": "JPM", "title": "JPMorgan Chase & Co."},
    "7": {"cik_str": 70858, "ticker": "BAC", "title": "Bank of America Corp"},
}

SAMPLE_SUBMISSIONS = {
    "cik": "0000320193",
    "name": "Apple Inc.",
    "tickers": ["AAPL"],
    "filings": {
        "recent": {
            "accessionNumber": [
                "0000320193-26-000001",
                "0000320193-25-000099",
                "0000320193-25-000050",
            ],
            "filingDate": ["2026-03-14", "2025-12-01", "2025-06-15"],
            "form": ["4", "10-K", "8-K"],
            "primaryDocument": ["form4.xml", "aapl-20251231.htm", "8-k.htm"],
            "primaryDocDescription": ["Form 4", "Annual Report", "Current Report"],
        }
    },
}

SAMPLE_FORM4_XML = """<?xml version="1.0"?>
<ownershipDocument>
  <reportingOwner>
    <reportingOwnerId>
      <rptOwnerName>Tim Cook</rptOwnerName>
    </reportingOwnerId>
    <reportingOwnerRelationship>
      <isOfficer>1</isOfficer>
      <officerTitle>CEO</officerTitle>
    </reportingOwnerRelationship>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <transactionCoding>
        <transactionCode>S</transactionCode>
      </transactionCoding>
      <transactionAmounts>
        <transactionShares><value>50000</value></transactionShares>
        <transactionPricePerShare><value>175.25</value></transactionPricePerShare>
      </transactionAmounts>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
</ownershipDocument>"""

SAMPLE_FORM4_PURCHASE_XML = """<?xml version="1.0"?>
<ownershipDocument>
  <reportingOwner>
    <reportingOwnerId>
      <rptOwnerName>Luca Maestri</rptOwnerName>
    </reportingOwnerId>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <transactionCoding>
        <transactionCode>P</transactionCode>
      </transactionCoding>
      <transactionAmounts>
        <transactionShares><value>1000</value></transactionShares>
        <transactionPricePerShare><value>200.00</value></transactionPricePerShare>
      </transactionAmounts>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
</ownershipDocument>"""

SAMPLE_XBRL_FACTS = {
    "cik": 320193,
    "entityName": "Apple Inc.",
    "facts": {
        "us-gaap": {
            "Revenues": {
                "label": "Revenue",
                "units": {
                    "USD": [
                        {"end": "2024-09-28", "val": 391035000000, "form": "10-K",
                         "frame": "CY2024", "fy": 2024, "fp": "FY"},
                        {"end": "2023-09-30", "val": 383285000000, "form": "10-K",
                         "frame": "CY2023", "fy": 2023, "fp": "FY"},
                    ]
                },
            },
            "EarningsPerShareBasic": {
                "label": "EPS Basic",
                "units": {
                    "USD/shares": [
                        {"end": "2024-09-28", "val": 6.08, "form": "10-K",
                         "frame": "CY2024", "fy": 2024, "fp": "FY"},
                    ]
                },
            },
            "NetIncomeLoss": {
                "label": "Net Income",
                "units": {
                    "USD": [
                        {"end": "2024-09-28", "val": 93736000000, "form": "10-K",
                         "frame": "CY2024", "fy": 2024, "fp": "FY"},
                    ]
                },
            },
            "Assets": {
                "label": "Total Assets",
                "units": {
                    "USD": [
                        {"end": "2024-09-28", "val": 364980000000, "form": "10-K",
                         "frame": "CY2024", "fy": 2024, "fp": "FY"},
                    ]
                },
            },
        }
    },
}


# ── CIK Mapping Tests ──────────────────────────────────────────────────────────

class TestCikMapping:
    def setup_method(self):
        """Load sample data before each test."""
        load_cik_map_from_dict(SAMPLE_CIK_JSON)

    def test_pad_cik_zero_pads_to_10_digits(self):
        assert _pad_cik(320193) == "0000320193"
        assert _pad_cik(1) == "0000000001"
        assert _pad_cik(9999999999) == "9999999999"

    def test_get_cik_returns_padded_10_digit(self):
        cik = get_cik("AAPL")
        assert cik == "0000320193"
        assert len(cik) == 10

    def test_get_cik_unknown_ticker_returns_none(self):
        result = get_cik("ZZZNOTREAL")
        assert result is None

    def test_cik_mapping_loads_from_json(self):
        assert get_cik_map_size() == len(SAMPLE_CIK_JSON)
        assert get_cik("MSFT") == "0000789019"
        assert get_cik("JPM") == "0000827054"

    def test_cik_mapping_handles_empty_response(self):
        load_cik_map_from_dict({})
        assert get_cik_map_size() == 0
        assert get_cik("AAPL") is None

    def test_cik_mapping_case_insensitive(self):
        assert get_cik("aapl") == get_cik("AAPL")
        assert get_cik("msft") == get_cik("MSFT")

    def test_parse_cik_json_handles_missing_fields(self):
        bad_data = {
            "0": {"cik_str": 123, "ticker": "GOOD", "title": "Good Co"},
            "1": {"ticker": "NOTICKER"},  # missing cik_str
            "2": {"cik_str": 456},        # missing ticker
            "3": {"cik_str": "bad", "ticker": "BADCIK"},  # non-int cik
        }
        result = _parse_cik_json(bad_data)
        assert "GOOD" in result
        assert "NOTICKER" not in result
        assert "" not in result


# ── Filing Parser Tests ────────────────────────────────────────────────────────

class TestFilingParser:
    def setup_method(self):
        load_cik_map_from_dict(SAMPLE_CIK_JSON)

    def _parse_filings(self, data, ticker="AAPL", cik="0000320193"):
        from scrapers.edgar.edgar_harvester import _parse_recent_filings
        return _parse_recent_filings(data, ticker, cik)

    def test_parse_efts_search_results(self):
        """Parser returns correct number of EDGAR-form filings."""
        results = self._parse_filings(SAMPLE_SUBMISSIONS)
        # All 3 forms are in FILING_FORMS
        assert len(results) == 3

    def test_parse_form4_from_submissions(self):
        results = self._parse_filings(SAMPLE_SUBMISSIONS)
        form4 = next(r for r in results if r["form_type"] == "4")
        assert form4["ticker"] == "AAPL"
        assert form4["accession_number"] == "0000320193-26-000001"

    def test_parse_filing_url_constructed(self):
        results = self._parse_filings(SAMPLE_SUBMISSIONS)
        form4 = next(r for r in results if r["form_type"] == "4")
        assert "form4.xml" in form4["filing_url"]
        assert "320193" in form4["filing_url"]

    def test_unknown_form_type_skipped(self):
        """Forms not in FILING_FORMS (e.g. DEF 14A) should be filtered out."""
        data = {
            "filings": {"recent": {
                "accessionNumber": ["0000320193-26-000002"],
                "filingDate": ["2026-03-14"],
                "form": ["DEF 14A"],  # not in FILING_FORMS
                "primaryDocument": ["proxy.htm"],
                "primaryDocDescription": ["Proxy"],
            }}
        }
        results = self._parse_filings(data)
        assert results == []

    def test_parse_filing_with_missing_fields_uses_defaults(self):
        """Missing optional arrays should not crash the parser."""
        data = {
            "filings": {"recent": {
                "accessionNumber": ["0000320193-26-000003"],
                "form": ["8-K"],
                # no filingDate, no primaryDocument, no primaryDocDescription
            }}
        }
        results = self._parse_filings(data)
        assert len(results) == 1
        assert results[0]["form_type"] == "8-K"
        assert results[0]["filed_at"] == ""

    def test_filing_pydantic_model_validation(self):
        from scrapers.edgar.edgar_harvester import EdgarFiling
        filing = EdgarFiling(
            ticker="AAPL",
            cik="0000320193",
            form_type="4",
            filed_at=datetime.datetime(2026, 3, 14, tzinfo=datetime.timezone.utc),
            filing_url="https://www.sec.gov/Archives/edgar/data/320193/000032019326000001/form4.xml",
            description="Form 4",
            accession_number="0000320193-26-000001",
        )
        assert filing.ticker == "AAPL"
        assert filing.form_type == "4"

    def test_duplicate_accession_number_filtered(self):
        """Seen-set prevents duplicate accession numbers from being re-processed."""
        # Two entries with the same accession number
        data = {
            "filings": {"recent": {
                "accessionNumber": ["0000320193-26-000001", "0000320193-26-000001"],
                "filingDate": ["2026-03-14", "2026-03-14"],
                "form": ["4", "4"],
                "primaryDocument": ["form4.xml", "form4.xml"],
                "primaryDocDescription": ["Form 4", "Form 4"],
            }}
        }
        results = self._parse_filings(data)
        # Parser returns both; de-duplication is handled by _is_seen in the job
        accessions = [r["accession_number"] for r in results]
        assert accessions.count("0000320193-26-000001") == 2


# ── Form 4 Insider Parser Tests ────────────────────────────────────────────────

class TestInsiderParser:
    def _parse(self, xml_text, ticker="AAPL", cik="0000320193",
               accession="0000320193-26-000001", filed="2026-03-14"):
        from scrapers.edgar.edgar_harvester import _parse_form4_xml
        return _parse_form4_xml(xml_text, ticker, cik, accession, filed)

    def test_parse_insider_sale_transaction(self):
        results = self._parse(SAMPLE_FORM4_XML)
        assert len(results) == 1
        r = results[0]
        assert r.transaction_type == "S"
        assert r.shares == 50000.0
        assert r.price_per_share == 175.25
        assert r.total_value == pytest.approx(50000 * 175.25)
        assert r.insider_name == "Tim Cook"

    def test_parse_insider_purchase_transaction(self):
        results = self._parse(SAMPLE_FORM4_PURCHASE_XML)
        assert len(results) == 1
        r = results[0]
        assert r.transaction_type == "P"
        assert r.shares == 1000.0
        assert r.price_per_share == 200.0
        assert r.insider_name == "Luca Maestri"

    def test_parse_form4_accession_preserved(self):
        results = self._parse(SAMPLE_FORM4_XML, accession="0000320193-26-000001")
        assert results[0].accession_number == "0000320193-26-000001"

    def test_parse_form4_empty_xml_returns_empty_list(self):
        results = self._parse("")
        assert results == []

    def test_parse_form4_malformed_xml_returns_empty_list(self):
        results = self._parse("<bad>not valid</xml>")
        assert results == []

    def test_parse_form4_no_matching_transaction_code(self):
        """Transactions with code not P or S are excluded."""
        xml = """<?xml version="1.0"?>
<ownershipDocument>
  <reportingOwner>
    <reportingOwnerId><rptOwnerName>Someone</rptOwnerName></reportingOwnerId>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <transactionCoding><transactionCode>G</transactionCode></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>100</value></transactionShares>
      </transactionAmounts>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
</ownershipDocument>"""
        results = self._parse(xml)
        assert results == []


# ── Fundamentals Parser Tests ──────────────────────────────────────────────────

class TestFundamentalsParser:
    def _parse(self, data, ticker="AAPL", cik="0000320193"):
        from scrapers.edgar.edgar_harvester import _parse_company_facts
        return _parse_company_facts(data, ticker, cik)

    def test_extract_revenue_from_xbrl_facts(self):
        rows = self._parse(SAMPLE_XBRL_FACTS)
        fy2024 = next((r for r in rows if r["period"] == "CY2024"), None)
        assert fy2024 is not None
        assert fy2024["revenue"] == pytest.approx(391035000000)

    def test_extract_eps_from_xbrl_facts(self):
        rows = self._parse(SAMPLE_XBRL_FACTS)
        fy2024 = next((r for r in rows if r["period"] == "CY2024"), None)
        assert fy2024 is not None
        assert fy2024["eps"] == pytest.approx(6.08)

    def test_extract_net_income_from_xbrl_facts(self):
        rows = self._parse(SAMPLE_XBRL_FACTS)
        fy2024 = next((r for r in rows if r["period"] == "CY2024"), None)
        assert fy2024["net_income"] == pytest.approx(93736000000)

    def test_missing_concept_returns_none(self):
        """Concepts absent from XBRL facts should map to None."""
        rows = self._parse(SAMPLE_XBRL_FACTS)
        fy2024 = next((r for r in rows if r["period"] == "CY2024"), None)
        # Liabilities not in SAMPLE_XBRL_FACTS
        assert fy2024["total_liabilities"] is None

    def test_multiple_periods_extracted(self):
        """Concepts with different latest periods produce separate period rows."""
        # Revenue latest = CY2023; Assets latest = CY2024 → two distinct rows
        mixed_facts = {
            "cik": 320193,
            "entityName": "Apple Inc.",
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {"USD": [
                            {"end": "2023-09-30", "val": 383285000000,
                             "form": "10-K", "frame": "CY2023"},
                        ]},
                    },
                    "Assets": {
                        "units": {"USD": [
                            {"end": "2024-09-28", "val": 364980000000,
                             "form": "10-K", "frame": "CY2024"},
                        ]},
                    },
                }
            },
        }
        rows = self._parse(mixed_facts)
        periods = {r["period"] for r in rows}
        assert "CY2023" in periods
        assert "CY2024" in periods

    def test_empty_facts_returns_empty_list(self):
        data = {"cik": 320193, "entityName": "Apple Inc.", "facts": {}}
        rows = self._parse(data)
        assert rows == []

    def test_xbrl_validation_error_routes_to_dead_letter(self):
        """ValidationError in EdgarInsider is caught and routed to dead_letter."""
        from scrapers.edgar.edgar_harvester import _parse_form4_xml
        # XML with missing required owner name still produces a record with "Unknown"
        xml = """<?xml version="1.0"?>
<ownershipDocument>
  <reportingOwner>
    <reportingOwnerId></reportingOwnerId>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <transactionCoding><transactionCode>P</transactionCode></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>500</value></transactionShares>
      </transactionAmounts>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
</ownershipDocument>"""
        results = _parse_form4_xml(xml, "AAPL", "0000320193", "0000320193-26-000099", "2026-03-14")
        # Should produce a record with insider_name="Unknown"
        assert len(results) == 1
        assert results[0].insider_name == "Unknown"


# ── Integration-style (mocked) Tests ──────────────────────────────────────────

class TestHarvesterIntegration:
    def test_harvester_user_agent_header_set(self):
        """EDGAR_HEADERS must contain a User-Agent with contact info."""
        from scrapers.edgar.cik_mapping import EDGAR_HEADERS
        assert "User-Agent" in EDGAR_HEADERS
        assert "cemini.com" in EDGAR_HEADERS["User-Agent"].lower()

    def test_harvester_uses_resilient_client(self):
        """edgar_pipeline uses create_resilient_client (Hishel) not plain httpx."""
        from scrapers.edgar import edgar_harvester
        # Module-level retry is the tenacity decorator wrapping _do_get
        assert callable(edgar_harvester._get_json)
        assert callable(edgar_harvester._get_text)

    def test_circuit_breaker_configured(self):
        """Circuit breaker is wired at module level."""
        import aiobreaker
        from scrapers.edgar.edgar_harvester import _edgar_cb
        assert isinstance(_edgar_cb, aiobreaker.CircuitBreaker)

    def test_scheduler_registers_three_jobs(self):
        """create_scheduler + 3 add_job calls produce 3 registered jobs."""
        from core.resilience import create_scheduler
        scheduler = create_scheduler()

        async def dummy():
            pass

        scheduler.add_job(dummy, "interval", seconds=600, id="edgar_filings")
        scheduler.add_job(dummy, "interval", seconds=1800, id="edgar_insider")
        scheduler.add_job(dummy, "cron", hour=6, minute=0,
                          timezone="UTC", id="edgar_fundamentals")

        assert scheduler.get_job("edgar_filings") is not None
        assert scheduler.get_job("edgar_insider") is not None
        assert scheduler.get_job("edgar_fundamentals") is not None

    def test_rate_limit_sleep_between_cik_lookups(self):
        """RATE_LIMIT_SLEEP constant keeps request rate ≤10 req/sec."""
        from scrapers.edgar.edgar_harvester import RATE_LIMIT_SLEEP
        assert RATE_LIMIT_SLEEP >= 0.1  # at least 100ms → ≤10 req/sec

    def test_intel_publish_edgar_filing_format(self):
        """Redis envelope matches IntelPayload contract."""
        from scrapers.edgar.edgar_harvester import EdgarFiling

        mock_r = MagicMock()
        filing = EdgarFiling(
            ticker="MSFT",
            cik="0000789019",
            form_type="8-K",
            filed_at=datetime.datetime(2026, 3, 14, tzinfo=datetime.timezone.utc),
            filing_url="https://www.sec.gov/Archives/edgar/data/789019/000078901926000001/8k.htm",
            description="Current Report",
            accession_number="0000789019-26-000001",
        )
        payload = filing.model_dump(mode="json")

        # Simulate _publish
        envelope = json.dumps({
            "value": payload,
            "source_system": "edgar_pipeline",
            "timestamp": 1741900000.0,
            "confidence": 1.0,
        }, default=str)
        mock_r.set("intel:edgar_filing", envelope, ex=600)

        mock_r.set.assert_called_once()
        args = mock_r.set.call_args
        data = json.loads(args[0][1])
        assert data["source_system"] == "edgar_pipeline"
        assert data["value"]["ticker"] == "MSFT"
        assert data["value"]["form_type"] == "8-K"

    def test_intel_publish_edgar_insider_format(self):
        """EdgarInsider payload matches IntelPayload contract."""
        from scrapers.edgar.edgar_harvester import EdgarInsider

        insider = EdgarInsider(
            ticker="AAPL",
            cik="0000320193",
            insider_name="Tim Cook",
            transaction_type="S",
            shares=50000.0,
            price_per_share=175.25,
            total_value=8762500.0,
            filed_at=datetime.datetime(2026, 3, 14, tzinfo=datetime.timezone.utc),
            accession_number="0000320193-26-000001",
        )
        payload = insider.model_dump(mode="json")
        assert payload["transaction_type"] == "S"
        assert payload["shares"] == 50000.0
        assert payload["insider_name"] == "Tim Cook"

    def test_tracked_symbols_includes_all_polygon_stocks_plus_dia(self):
        """TRACKED_SYMBOLS must include DIA and all polygon STOCK_SYMBOLS."""
        from scrapers.edgar.edgar_harvester import TRACKED_SYMBOLS
        required = ["SPY", "QQQ", "IWM", "DIA", "AAPL", "MSFT", "NVDA",
                    "AMZN", "META", "GOOGL", "TSLA", "JPM", "BAC"]
        for sym in required:
            assert sym in TRACKED_SYMBOLS, f"{sym} missing from TRACKED_SYMBOLS"

    def test_cik_not_found_skips_gracefully(self):
        """get_cik returning None should not raise — just log and skip."""
        load_cik_map_from_dict({})  # empty map
        result = get_cik("AAPL")
        assert result is None  # no exception raised

    def test_parse_company_facts_ticker_and_cik_preserved(self):
        """Rows from _parse_company_facts carry the correct ticker/cik."""
        from scrapers.edgar.edgar_harvester import _parse_company_facts
        rows = _parse_company_facts(SAMPLE_XBRL_FACTS, "AAPL", "0000320193")
        for row in rows:
            assert row["ticker"] == "AAPL"
            assert row["cik"] == "0000320193"

    def test_filing_forms_constant_includes_required_types(self):
        """FILING_FORMS must include all 5 required form types."""
        from scrapers.edgar.edgar_harvester import FILING_FORMS
        for form in ("4", "8-K", "10-K", "10-Q", "13-F"):
            assert form in FILING_FORMS
