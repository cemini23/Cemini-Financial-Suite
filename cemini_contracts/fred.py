"""FRED Macro Data contracts (Step 39).

Pydantic v2 models for Federal Reserve Economic Data intel payloads
published to Redis intel:fred_* channels.

Redis channels
--------------
intel:fred_yield_curve    FredYieldCurveIntel
intel:fred_fed_policy     FredFedPolicyIntel
intel:fred_credit_spread  FredCreditSpreadIntel
intel:fred_labor          FredLaborIntel
intel:fred_inflation      FredInflationIntel
intel:fred_sentiment      FredSentimentIntel
"""

import logging
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class FredObservation(BaseModel):
    """Single FRED observation as stored in fred_observations table."""

    model_config = ConfigDict(extra="allow")

    series_id: str
    observation_date: str  # YYYY-MM-DD
    value: Optional[float] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class FredYieldCurveIntel(BaseModel):
    """intel:fred_yield_curve — T10Y2Y and T10Y3M spreads."""

    model_config = ConfigDict(extra="allow")

    spread_10y2y: Optional[float] = None  # 10Y minus 2Y Treasury spread
    spread_10y3m: Optional[float] = None  # 10Y minus 3M Treasury spread
    observation_date: str = ""
    fetched_at: str = ""
    source: str = "fred"


class FredFedPolicyIntel(BaseModel):
    """intel:fred_fed_policy — Fed funds rate and balance sheet."""

    model_config = ConfigDict(extra="allow")

    fed_funds_rate: Optional[float] = None        # DFF — effective fed funds rate
    fed_balance_sheet_mm: Optional[float] = None  # WALCL — Fed assets in millions
    observation_date: str = ""
    fetched_at: str = ""
    source: str = "fred"


class FredCreditSpreadIntel(BaseModel):
    """intel:fred_credit_spread — High yield OAS spread."""

    model_config = ConfigDict(extra="allow")

    hy_oas_spread: Optional[float] = None  # BAMLH0A0HYM2 — HY option-adjusted spread
    observation_date: str = ""
    fetched_at: str = ""
    source: str = "fred"


class FredLaborIntel(BaseModel):
    """intel:fred_labor — Labor market indicators."""

    model_config = ConfigDict(extra="allow")

    initial_claims: Optional[float] = None      # ICSA — weekly initial jobless claims
    unemployment_rate: Optional[float] = None   # UNRATE — monthly unemployment rate
    nonfarm_payrolls_k: Optional[float] = None  # PAYEMS — nonfarm payrolls (thousands)
    observation_date: str = ""
    fetched_at: str = ""
    source: str = "fred"


class FredInflationIntel(BaseModel):
    """intel:fred_inflation — PCE and Core CPI indices."""

    model_config = ConfigDict(extra="allow")

    pce_index: Optional[float] = None      # PCEPI — PCE price index
    core_cpi_index: Optional[float] = None  # CPILFESL — core CPI (ex food/energy)
    observation_date: str = ""
    fetched_at: str = ""
    source: str = "fred"


class FredSentimentIntel(BaseModel):
    """intel:fred_sentiment — Consumer sentiment and VIX."""

    model_config = ConfigDict(extra="allow")

    michigan_sentiment: Optional[float] = None  # UMCSENT — University of Michigan
    vix_close: Optional[float] = None           # VIXCLS — CBOE VIX daily close
    observation_date: str = ""
    fetched_at: str = ""
    source: str = "fred"
