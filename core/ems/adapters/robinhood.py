import asyncio
import os
import robin_stocks.robinhood as r
from typing import Dict, Any
from core.ems.base import BaseExecutionAdapter
from core.schemas.trading_signals import TradingSignal

class RobinhoodAdapter(BaseExecutionAdapter):
    def __init__(self, username: str, password: str):
        # Initial login - in production, this uses the cached session token logic we built earlier
        r.login(username, password, store_session=True)

    async def get_buying_power(self) -> float:
        profile = await asyncio.to_thread(r.profiles.load_account_profile)
        # Handle cases where margin might not be enabled
        try:
            return float(profile['margin_balances']['unallocated_margin_cash'])
        except (KeyError, TypeError):
            return float(profile.get('portfolio_cash', 0.0))

    async def execute_order(self, signal: TradingSignal) -> Dict[str, Any]:
        # --- CRITICAL SAFETY GUARDRAIL ---
        # Hardcoded to never use real money during current debug session.
        print(f"⚠️ SAFETY: Paper Mode Active. Simulating {signal.action} for {signal.ticker_or_event}")
        
        if os.getenv("PAPER_MODE", "True") == "True":
            return {
                "status": "simulated_success", 
                "message": "TRADE NOT PLACED (PAPER MODE)",
                "ticker": signal.ticker_or_event
            }

        if signal.asset_class == "option":
            response = await asyncio.to_thread(
                r.orders.order_buy_option_limit,
                positionEffect="Open",
                creditOrDebit="Debit",
                price=getattr(signal, "limit_price", 0.01),
                symbol=signal.ticker_or_event,
                quantity=1,
                expirationDate=signal.expiration_date.strftime("%Y-%m-%d") if signal.expiration_date else None,
                strike=signal.strike_price,
                optionType="call"
            )
            return response
        
        elif signal.asset_class == "equity":
            if signal.action == "buy":
                return await asyncio.to_thread(r.orders.order_buy_market, signal.ticker_or_event, 1) # Example qty 1
                
        return {"status": "unsupported_asset_class_or_action"}
