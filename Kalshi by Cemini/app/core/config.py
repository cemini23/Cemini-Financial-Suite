import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "Kalshi by Cemini"
    
    # --- KALSHI CONFIG ---
    KALSHI_EMAIL: str = ""
    KALSHI_PASSWORD: str = ""
    KALSHI_API_KEY: str = "" 
    KALSHI_PRIVATE_KEY_PATH: str = "private_key.pem"
    PAPER_MODE: bool = True
    
    # --- WEATHER CONFIG ---
    OPENWEATHER_API_KEY: str = ""
    # NWS requires a User-Agent with contact info
    NWS_USER_AGENT: str = "(kalshi-bot-cemini, contact@cemini.dev)"
    
    # --- X / ELON CONFIG ---
    X_API_KEY: str = ""
    X_API_SECRET: str = ""
    X_ACCESS_TOKEN: str = ""
    X_ACCESS_SECRET: str = ""
    X_BEARER_TOKEN: str = "" # Used for high-fidelity velocity tracking
    
    class Config:
        env_file = ".env"
        extra = "ignore" 

settings = Settings()

# Global Log Buffer for the Dashboard UI
UI_LOGS = []

def add_ui_log(msg, level="INFO"):
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    UI_LOGS.append({"time": timestamp, "msg": msg, "level": level})
    # Keep last 50 logs
    if len(UI_LOGS) > 50:
        UI_LOGS.pop(0)
