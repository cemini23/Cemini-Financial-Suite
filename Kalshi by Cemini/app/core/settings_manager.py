import json
import os
from pydantic import BaseModel
from typing import Dict, Any, List

SETTINGS_FILE = "settings.json"

class SystemSettings(BaseModel):
    trading_enabled: bool = False
    paper_mode: bool = True # Added for Phase 8.5
    risk_level: str = "CONSERVATIVE" # CONSERVATIVE, MODERATE, AGGRESSIVE
    priority_module: str = "BTC" # BTC, POWELL, SOCIAL, MUSK
    max_position_size: float = 10.0
    max_budget: float = 1000.0
    
    # Conviction Thresholds (Dialed In)
    global_min_score: int = 70 # Minimum score for ANY trade
    btc_threshold: int = 75
    social_threshold: float = 0.6
    weather_variance_threshold: float = 1.5
    
    bet_sizing_method: str = "KELLY" # KELLY, FLAT, PERCENTAGE
    auto_hedge: bool = True
    traders: List[str] = ["ShardiB2", "BigCheds", "Pentosh1"]
    
    # X / Twitter Budget Protocol (Phase 8)
    x_api_total_spend: float = 0.0
    x_api_budget_limit: float = float(os.getenv("X_API_MONTHLY_BUDGET", "25.00"))
    social_scan_frequency: int = int(os.getenv("SOCIAL_SCRAPER_INTERVAL_MINUTES", "30"))
    last_social_scan: float = 0.0

class SettingsManager:
    def __init__(self):
        self.settings_path = SETTINGS_FILE
        if not os.path.exists(self.settings_path):
            self.save_settings(SystemSettings())

    def get_settings(self) -> SystemSettings:
        with open(self.settings_path, "r") as f:
            data = json.load(f)
            return SystemSettings(**data)

    def save_settings(self, settings: SystemSettings):
        with open(self.settings_path, "w") as f:
            json.dump(settings.dict(), f, indent=4)
        # Sync spend counter to Redis so other containers can read it
        try:
            import redis as _redis
            _r = _redis.Redis(
                host=os.getenv("REDIS_HOST", "redis"),
                port=6379,
                password=os.getenv("REDIS_PASSWORD", "cemini_redis_2026"),
                decode_responses=True,
                socket_connect_timeout=2,
            )
            _r.set("x_api:monthly_spend", str(settings.x_api_total_spend))
            _r.close()
        except Exception:
            pass

settings_manager = SettingsManager()
