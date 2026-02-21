"""
QuantOS™ v13.0.10 - Golden Master Server
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import os
import sys
import time
from fastapi import APIRouter, Request, Body, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from core.version import __version__, __build__

# Router for all UI and API logic
router = APIRouter()

# Simple Cache for Portfolio and Balances
PORTFOLIO_CACHE = {"data": [], "last_update": 0}
BALANCE_CACHE = {"data": {}, "global": 0.0, "last_update": 0}

# Routes
@router.get("/health")
async def health_check():
    return {"status": "online", "version": __version__, "build": __build__}

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return request.app.state.templates.TemplateResponse("index.html", {
        "request": request, 
        "page": "dashboard",
        "version": __version__,
        "build": __build__
    })

@router.get("/welcome", response_class=HTMLResponse)
async def welcome_page(request: Request):
    return request.app.state.templates.TemplateResponse("welcome.html", {"request": request})

@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    return request.app.state.templates.TemplateResponse("analytics.html", {
        "request": request, 
        "page": "analytics",
        "version": __version__,
        "build": __build__
    })

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    return request.app.state.templates.TemplateResponse("settings.html", {
        "request": request, 
        "page": "settings",
        "version": __version__,
        "build": __build__
    })

@router.get("/backtester", response_class=HTMLResponse)
async def backtester_page(request: Request):
    return request.app.state.templates.TemplateResponse("backtester.html", {
        "request": request, 
        "page": "backtester",
        "version": __version__,
        "build": __build__
    })

@router.get("/api/settings")
async def get_settings():
    from config.settings_manager import settings_manager
    return settings_manager.settings

@router.get("/api/system_status")
async def get_system_status():
    """Returns the connectivity status of all brokers and harvester."""
    from core.brokers.factory import get_broker
    from core.harvester import harvester
    broker = get_broker()
    
    status = {"brokers": {}, "harvester": harvester.get_status()}
    if hasattr(broker, 'check_health'):
        status["brokers"] = broker.check_health()
    else:
        # Single broker fallback
        try:
            broker.get_buying_power()
            status["brokers"][broker.name] = True
        except Exception:
            status["brokers"][broker.name] = False
    
    return status

@router.get("/api/sentiment")
async def get_sentiment():
    """Returns the current market sentiment from QuantOS analytics."""
    from strategies import analytics
    stats = analytics.get_performance_stats()
    wr = stats.get('win_rate', 50)
    
    bias = "NEUTRAL"
    if wr > 60: bias = "BULLISH"
    elif wr < 40: bias = "BEARISH"
    
    volatility = "HIGH" if stats.get('today_activity', 0) > 20 else "NORMAL"
    
    return {
        "bias": bias,
        "volatility": volatility,
        "confidence": round(wr / 100, 2),
        "regime": "ACCUMULATION" if bias == "BULLISH" else "DISTRIBUTION" if bias == "BEARISH" else "CONSOLIDATION"
    }

@router.post("/api/settings")
async def update_settings(new_settings: dict = Body(...)):
    from config.settings_manager import settings_manager
    current = settings_manager.settings
    for key, val in new_settings.items():
        if key in current:
            current[key] = val
    settings_manager.save_settings(current)
    return {"status": "success"}

@router.get("/api/run_simulation")
async def run_simulation():
    """Triggers a historical simulation using the BacktestEngine."""
    try:
        from strategies.backtester import BacktestEngine
        engine = BacktestEngine()
        results = engine.run_historical_simulation()
        return results
    except Exception as e:
        return {"error": str(e)}

@router.get("/api/dashboard")
async def get_dashboard():
    from strategies import analytics
    from config.settings_manager import settings_manager
    from core.brokers.factory import get_broker
    from core.logger_config import UI_LOGS

    # 1. Performance Stats (Simulated/Historical)
    stats = analytics.get_performance_stats()

    # 2. Live Account Balances (with 30s Cache)
    global BALANCE_CACHE
    main_broker = get_broker()
    
    if time.time() - BALANCE_CACHE["last_update"] > 30:
        try:
            balances = {}
            # SILENT SYNC
            val = main_broker.get_buying_power()
            if val > 0:
                balances[main_broker.name] = val
                BALANCE_CACHE["data"] = balances
                BALANCE_CACHE["global"] = val
                BALANCE_CACHE["last_update"] = time.time()
        except Exception:
            pass

    broker_balances = BALANCE_CACHE["data"]
    global_balance = BALANCE_CACHE["global"]

    # 3. Fetch Live Positions from Broker (with 5s Cache)
    global PORTFOLIO_CACHE
    if time.time() - PORTFOLIO_CACHE["last_update"] > 5:
        portfolio = []
        try:
            positions = main_broker.get_positions()
            if positions:
                for p in positions:
                    portfolio.append({
                        "ticker": p["symbol"],
                        "shares_held": p["quantity"],
                        "average_buy_price": p["average_buy_price"],
                        "pnl_pct": 0.0,
                        "market_value": p["market_value"]
                    })
                PORTFOLIO_CACHE["data"] = portfolio
                PORTFOLIO_CACHE["last_update"] = time.time()
        except Exception:
            pass
    
    portfolio = PORTFOLIO_CACHE["data"]

    return {
        "version": __version__,
        "build": __build__,
        "equity": stats.get("total_equity", 0.0),
        "today_pnl": stats.get("total_profit", 0.0),
        "win_rate": stats.get("win_rate", 0),
        "global_balance": global_balance,
        "global_pnl_pct": stats.get("pnl_percentage", 0.0),
        "broker_balances": broker_balances,
        "portfolio": portfolio,
        "logs": list(reversed(UI_LOGS)),
        "bot_paused": settings_manager.get("bot_paused")
    }
