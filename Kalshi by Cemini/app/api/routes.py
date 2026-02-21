from fastapi import APIRouter
from modules.weather_alpha.analyzer import WeatherAnalyzer
from modules.musk_monitor.predictor import MuskPredictor
from modules.satoshi_vision.analyzer import SatoshiAnalyzer
from modules.powell_protocol.analyzer import PowellAnalyzer
from modules.social_alpha.analyzer import SocialAnalyzer
from modules.geo_pulse.monitor import GeoPulseMonitor
from modules.market_rover.rover import MarketRover
from app.core.state import GLOBAL_STATE, update_conviction
from app.core.config import settings

router = APIRouter()

# Initialize Engines
weather_engine = WeatherAnalyzer()
musk_engine = MuskPredictor()
btc_engine = SatoshiAnalyzer()
powell_engine = PowellAnalyzer()
social_engine = SocialAnalyzer()
geo_engine = GeoPulseMonitor()
rover_engine = MarketRover()

@router.get("/system/status")
async def get_system_status():
    """
    The Dashboard calls this to find out who is King and system health.
    """
    import os
    import time
    import base64
    import httpx
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from dotenv import dotenv_values

    # Check Kalshi Connectivity
    kalshi_online = False
    active_key = "NONE"
    try:
        key_id = settings.KALSHI_API_KEY
        private_key_path = settings.KALSHI_PRIVATE_KEY_PATH

        if key_id and os.path.exists(private_key_path):
            active_key = f"{key_id[:8]}...{key_id[-4:]}"
            with open(private_key_path, 'rb') as f:
                private_key = serialization.load_pem_private_key(f.read(), password=None)

            method = "GET"
            path = "/trade-api/v2/portfolio/balance"
            url = f"https://api.elections.kalshi.com{path}"
            timestamp = str(int(time.time() * 1000))
            msg = timestamp + method + path
            signature = private_key.sign(msg.encode('utf-8'), padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
            sig_b64 = base64.b64encode(signature).decode('utf-8')
            headers = {"KALSHI-ACCESS-KEY": key_id, "KALSHI-ACCESS-SIGNATURE": sig_b64, "KALSHI-ACCESS-TIMESTAMP": timestamp}

            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    kalshi_online = True
    except:
        pass

    return {
        **GLOBAL_STATE,
        "health": {
            "kalshi": kalshi_online,
            "key": active_key,
            "harvester": True # Since it starts with the app in this architecture
        }
    }

@router.get("/social/analyze")
async def get_social_alpha():
    """
    Analyzes high-value traders on X for BTC sentiment.
    """
    result = await social_engine.get_target_sentiment()
    # Update Conviction
    update_conviction(
        module="Social Alpha",
        score=int(result.get('score', 0) * 100),
        signal=result.get('sentiment', 'NEUTRAL'),
        reason="X Velocity Spike"
    )
    return result

@router.get("/geo/pulse")
async def get_geo_pulse():
    """
    Module 6: Monitors geopolitical and election signals from @DeItaone and @AP_Politics.
    """
    result = await geo_engine.scan_geo_pulse()
    update_conviction(
        module="Geo-Pulse",
        score=int(result.get('aggregate_impact_score', 0)),
        signal="VOLATILE" if result.get('aggregate_impact_score', 0) > 30 else "STABLE",
        reason="War/Election Keyword Hit"
    )
    return result

@router.get("/rover/scan")
async def get_market_rover():
    """
    Module 7: Scans active Kalshi markets and cross-references S&P 500/Economic events.
    """
    result = await rover_engine.scan_markets()
    findings = result.get('findings', [])
    best_confidence = max([f.get('confidence', 0) for f in findings]) if findings else 0

    update_conviction(
        module="Market Rover",
        score=int(best_confidence * 100),
        signal="CONVERGENCE" if best_confidence > 0.6 else "SCANNING",
        reason="S&P 500 / Macro Alignment"
    )
    return result

@router.get("/weather/scan/us")
async def get_weather_full_scan():
    """
    Nationwide Weather Arbitrage Scan.
    Analyzes all supported cities in parallel.
    """
    result = await weather_engine.scan_full_us()
    if result.get("best_opportunity"):
        best = result["best_opportunity"]
        update_conviction(
            module="Weather Alpha",
            score=int(best['edge'] * 100),
            signal=best['signal'],
            reason=f"Arbitrage in {best['city']}"
        )
    return result

@router.get("/weather/{city_code}")
async def get_weather_alpha(city_code: str):
    """
    High-performance async route for Weather Arbitrage.
    """
    result = await weather_engine.analyze_market(city_code.upper())

    # Send Intelligence to the Global State
    score = 85 if result['opportunities'] else 20
    reason = result['opportunities'][0]['bracket'] if result['opportunities'] else "No Edge"

    update_conviction(
        module="Weather Alpha",
        score=score,
        signal="ARBITRAGE" if score > 50 else "WAIT",
        reason=reason
    )
    return result

@router.get("/powell/analyze")
async def get_fed_alpha():
    """
    Analyzes Fed Rate probabilities and identifies Kalshi arbitrage.
    """
    result = await powell_engine.analyze_fed_market()
    return result

@router.get("/musk/predict")
async def get_musk_prediction():
    """
    Analyzes Elon's behavioral patterns and news volatility asynchronously.
    """
    result = await musk_engine.predict_today()
    status = result.get('prediction', {}).get('current_status', 'UNKNOWN')
    score = 90 if "HYPER-ACTIVE" in status else 40

    update_conviction(
        module="Musk Monitor",
        score=score,
        signal="ACTIVATE" if score > 70 else "STANDBY",
        reason=status
    )
    return result

@router.get("/btc/analyze")
async def get_btc_confluence(horizon: str = "SCALP"):
    """
    Runs institutional technical analysis on BTC/USD.
    Supports: SCALP, SWING, MACRO
    """
    result = await btc_engine.analyze_multiframe(asset="BTC", horizon=horizon.upper())
    score_str = result.get('score', '0/100').split('/')[0]
    update_conviction(
        module="Satoshi Vision",
        score=int(score_str),
        signal=result.get('sentiment', 'NEUTRAL'),
        reason="BTC Confluence Brain"
    )
    return result

@router.get("/analytics/btc")
async def get_btc_analytics(limit: int = 50):
    """
    Retrieves historical BTC harvest data from the Vault.
    """
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.vault import BTCHarvest

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BTCHarvest).order_by(BTCHarvest.timestamp.desc()).limit(limit)
        )
        history = result.scalars().all()
        return history

@router.get("/settings")
async def get_settings():
    """
    Retrieves current system settings.
    """
    from app.core.settings_manager import settings_manager
    return settings_manager.get_settings()

@router.post("/settings")
async def update_settings(updates: dict):
    """
    Updates system settings (Mode, Thresholds, Traders).
    """
    from app.core.settings_manager import settings_manager
    current = settings_manager.get_settings()

    # Update only provided fields
    for key, value in updates.items():
        if hasattr(current, key):
            setattr(current, key, value)

    settings_manager.save_settings(current)
    return {"status": "success"}

@router.get("/portfolio")
async def get_portfolio():
    """
    Fetches live Kalshi positions using direct RSA signing.
    """
    import os
    import time
    import base64
    import httpx
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from dotenv import dotenv_values

    try:
        key_id = settings.KALSHI_API_KEY
        private_key_path = settings.KALSHI_PRIVATE_KEY_PATH

        with open(private_key_path, 'rb') as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)

        method = "GET"
        path = "/trade-api/v2/portfolio/positions"
        url = f"https://api.elections.kalshi.com{path}"

        timestamp = str(int(time.time() * 1000))
        msg = timestamp + method + path
        signature = private_key.sign(
            msg.encode('utf-8'),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
            hashes.SHA256()
        )
        sig_b64 = base64.b64encode(signature).decode('utf-8')

        headers = {
            "KALSHI-ACCESS-KEY": key_id,
            "KALSHI-ACCESS-SIGNATURE": sig_b64,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                # Correct key is 'market_positions' in v2
                positions = data.get('market_positions', [])

                result = []
                for p in positions:
                    if p.get('position', 0) != 0:
                        result.append({
                            "ticker": p['ticker'],
                            "position": p['position'],
                            "market_value_cents": p.get('market_exposure', 0),
                            "side": "yes" # Default for most our trades
                        })
                return result
            else:
                return []
    except Exception as e:
        return {"error": str(e)}

@router.get("/logs")
async def get_logs():
    """
    Returns the last 50 system/trade logs.
    """
    from app.core.config import UI_LOGS
    return list(reversed(UI_LOGS))

@router.get("/health")
async def health_check():
    return {"status": "online", "engine": "Kalshi by Cemini v2.0.10 (Social Alpha Scanner Active)"}
