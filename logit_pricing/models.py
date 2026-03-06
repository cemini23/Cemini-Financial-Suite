"""logit_pricing.models — Pydantic model for contract pricing assessment.

ContractAssessment is the unified output of LogitPricingEngine.assess_contract().
Also imports into cemini_contracts namespace via cemini_contracts/pricing.py.
"""
import time
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ContractAssessment(BaseModel):
    """Logit-space pricing assessment for a binary prediction market contract.

    mispricing_score:
        Negative → contract is underpriced (buy YES)
        Positive → contract is overpriced (buy NO)
        Near 0   → fairly priced
    """

    model_config = ConfigDict(extra="allow")

    ticker: str = ""
    assessed_at: float = Field(default_factory=time.time)

    # Current market state
    current_price: float = Field(default=0.5, ge=0.0, le=1.0)
    logit_current: float = 0.0

    # Fair value from logit-space EMA
    logit_fair_value: float = 0.0
    fair_value_probability: float = Field(default=0.5, ge=0.0, le=1.0)

    # Primary signal
    mispricing_score: float = Field(
        default=0.0, ge=-3.0, le=3.0,
        description="Neg=underpriced(YES), Pos=overpriced(NO). Normalized by sigma.",
    )

    # Regime
    regime: str = "diffusion"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    time_decay_factor: float = Field(
        default=1.0, ge=0.0, le=1.0,
        description="1.0=far from resolution, 0.0=at resolution",
    )

    # Jump statistics
    jump_count_window: int = Field(default=0, ge=0)
    logit_volatility: float = Field(default=0.0, ge=0.0)

    # Implied belief volatility (Shaw and Dalen 2025)
    implied_sigma_b: float = Field(default=0.0, ge=0.0)

    # TA indicators in logit space
    indicators: dict[str, Any] = Field(
        default_factory=dict,
        description="Keys: logit_ema, logit_rsi, logit_bb_upper, logit_bb_lower, logit_bb_mid",
    )

    # Data quality
    n_observations: int = Field(default=0, ge=0)
    is_sufficient: bool = False

    # Optional market data
    yes_bid: Optional[float] = None
    yes_ask: Optional[float] = None
