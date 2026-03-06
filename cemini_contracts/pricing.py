"""Logit-space contract pricing models — Step 30.

ContractAssessment is defined in logit_pricing/models.py (the authoritative
source). This module re-exports it so it's available via cemini_contracts.
"""
from logit_pricing.models import ContractAssessment  # noqa: F401

__all__ = ["ContractAssessment"]
