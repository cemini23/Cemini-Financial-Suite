# CEMINI FINANCIAL SUITE™
# Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
# All Rights Reserved.
from pydantic_ai import Agent
from core.schemas.trading_signals import TradingSignal
import os

# Initialize the Formatting Guardrail Agent
# This agent's sole responsibility is to take the debate consensus and force it into the schema.
format_guardrail = Agent(
    'openai:gpt-4o', # Or your preferred model
    result_type=TradingSignal,
    system_prompt=(
        "You are the Lead Formatting Engineer for a high-frequency trading suite. "
        "Your task is to take the consensus reached by the Analyst Swarm and "
        "output a valid TradingSignal. You must strictly adhere to the schema. "
        "If information is missing, you must request clarification from the Analyst Swarm."
    ),
)

async def validate_consensus(consensus_text: str):
    """
    Translates raw text consensus into a validated Pydantic model.
    """
    result = await format_guardrail.run(consensus_text)
    # Pydantic AI automatically validates 'result.data' against the TradingSignal schema
    return result.data

if __name__ == "__main__":
    # Example usage (Dry Run)
    import asyncio
    
    sample_consensus = (
        "The swarm has reached consensus. We are Bullish on AAPL due to technical breakout. "
        "Route this to QuantOS on Robinhood. Action is buy with 0.85 confidence. "
        "Allocate 5% of capital."
    )
    
    # print(asyncio.run(validate_consensus(sample_consensus)))
