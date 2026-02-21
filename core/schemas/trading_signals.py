from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
from datetime import date

class TradingSignal(BaseModel):
    """
    The strictly enforced output schema for the Analyst Swarm.
    Every generated trade must conform exactly to this structure before execution.
    """
    
    # 1. Routing & Execution Environment
    target_system: Literal["QuantOS", "Kalshi By Cemini"] = Field(
        description="Must route to either the traditional quant engine or the prediction/sports engine."
    )
    target_brokerage: Literal["Robinhood", "SoFi", "Coinbase", "Kalshi", "Hard Rock Bet"] = Field(
        description="The specific API adapter that will execute the trade."
    )
    
    # 2. Asset & Contract Specifications
    asset_class: Literal["equity", "option", "crypto", "prediction_market", "sports_bet"]
    ticker_or_event: str = Field(
        description="The standardized stock ticker (e.g., AAPL), crypto pair (e.g., BTC-USD), or specific event ID (e.g., NFL Super Bowl Squares)."
    )
    action: Literal["buy", "sell", "hold", "short", "cover"]
    
    # 3. Risk & Sizing Constraints
    confidence_score: float = Field(
        ge=0.0, le=1.0, 
        description="The consensus confidence score from the agent debate (0.0 to 1.0)."
    )
    proposed_allocation_pct: float = Field(
        ge=0.0, le=0.10, 
        description="Maximum 10% of total portfolio buying power per trade to enforce strict drawdown limits."
    )
    
    # 4. Optional Fields (Strictly validated based on asset class)
    strike_price: Optional[float] = Field(
        default=None, 
        description="Required strictly if asset_class is 'option'."
    )
    expiration_date: Optional[date] = Field(
        default=None, 
        description="Required strictly if asset_class is 'option' or 'prediction_market'."
    )
    
    # 5. Telemetry / Logging
    agent_reasoning: str = Field(
        description="A concise, 1-sentence summary of the mathematical or sentiment logic used to generate this signal for the Deephaven dashboard."
    )

    # Cross-field validation to prevent hallucinated combinations
    @field_validator('strike_price', mode='after')
    @classmethod
    def validate_options_requirements(cls, v, info):
        if info.data.get('asset_class') == 'option' and v is None:
            raise ValueError("An options contract strictly requires a strike price.")
        return v

    @field_validator('expiration_date', mode='after')
    @classmethod
    def validate_expiration_requirements(cls, v, info):
        if info.data.get('asset_class') in ['option', 'prediction_market'] and v is None:
            raise ValueError(f"Asset class '{info.data.get('asset_class')}' requires an expiration_date.")
        return v
