import json
import os
import threading

class SettingsManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SettingsManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'dynamic_settings.json')
        self.defaults = {
            "budget_mode": "FIXED", # FIXED or PERCENT
            "budget_fixed": 10.0,
            "budget_percent": 1.0,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.10,
            "entry_score_threshold": 2.5,
            "min_confidence_threshold": 75,
            "backtest_min_score": 60,
            "force_test_trade": True,
            "max_positions": 10,
            "environment": "PAPER",
            "active_broker": "robinhood",
            "global_router_enabled": False,
            "primary_broker": "alpaca",
            "alpaca_api_key": "",
            "alpaca_secret_key": "",
            "rh_username": "",
            "rh_password": "",
            "rh_totp_secret": "",
            "schwab_app_key": "",
            "schwab_app_secret": "",
            "sofi_username": "",
            "sofi_password": "",
            "webull_email": "",
            "webull_password": "",
            "webull_pin": "",
            "ibkr_host": "127.0.0.1",
            "ibkr_port": 7497,
            "ibkr_client_id": 1,
            "tax_bracket_pct": 30.0,
            "wash_sale_guard_enabled": True,
            "max_slippage_pct": 0.5,
            "execution_timeout": 30,
            "options_enabled": False,
            "report_recipients": os.getenv("REPORT_RECIPIENTS", ""),
            "bot_paused": False
        }
        self.settings = self.load_settings()
        self._initialized = True

    def load_settings(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return {**self.defaults, **json.load(f)}
            except Exception:
                return self.defaults
        return self.defaults

    def save_settings(self, new_settings):
        with self._lock:
            self.settings.update(new_settings)
            try:
                with open(self.config_path, 'w') as f:
                    json.dump(self.settings, f, indent=4)
                return True
            except Exception:
                return False

    def get(self, key):
        return self.settings.get(key, self.defaults.get(key))

settings_manager = SettingsManager()
