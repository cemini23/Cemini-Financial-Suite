"""logit_pricing — Logit-Space Contract Pricing Library.

Shaw & Dalen (2025) Logit Jump-Diffusion framework for Kalshi binary contracts.

Public API:
    from logit_pricing import LogitPricingEngine, ContractAssessment
    engine = LogitPricingEngine()
    assessment = engine.assess_contract(prices, timestamps)
"""
from logit_pricing.pricing_engine import LogitPricingEngine
from logit_pricing.models import ContractAssessment
from logit_pricing.transforms import logit, inv_logit, logit_array, inv_logit_array

__version__ = "1.0.0"
__all__ = [
    "LogitPricingEngine",
    "ContractAssessment",
    "logit",
    "inv_logit",
    "logit_array",
    "inv_logit_array",
]
