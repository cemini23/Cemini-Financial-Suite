"""
QuantOS™ v11.8.0 - Broker Factory
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import os
from config.settings_manager import settings_manager

def get_broker_by_name(broker_name):
    broker_name = broker_name.lower()
    if broker_name == "alpaca":
        from core.brokers.alpaca import AlpacaAdapter
        return AlpacaAdapter()
    elif broker_name == "robinhood":
        from core.brokers.robinhood import RobinhoodAdapter
        return RobinhoodAdapter()
    elif broker_name == "ibkr":
        from core.brokers.ibkr import IBKRAdapter
        return IBKRAdapter()
    elif broker_name == "schwab":
        from core.brokers.schwab import SchwabAdapter
        return SchwabAdapter()
    elif broker_name == "sofi":
        from core.brokers.sofi import SofiAdapter
        return SofiAdapter()
    elif broker_name == "webull":
        from core.brokers.webull import WebullAdapter
        return WebullAdapter()
    elif broker_name == "kalshi":
        from core.brokers.kalshi import KalshiAdapter
        return KalshiAdapter()
    else:
        raise ValueError(f"Unknown broker: {broker_name}")

def get_broker():
    # Priority: Settings Manager (UI controlled) -> Environment Variable -> Default
    broker_name = settings_manager.get("active_broker")
    
    # If settings_manager returns None or empty, fallback to ENV, then hard default
    if not broker_name:
        broker_name = os.getenv("ACTIVE_BROKER", "ibkr")
    
    # Use lowercase for consistent comparison
    broker_name = str(broker_name).lower()

    if broker_name == "router":
        from core.brokers.router import GlobalRouter
        return GlobalRouter()
    
    return get_broker_by_name(broker_name)
