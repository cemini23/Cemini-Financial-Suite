# Configuration (v10.1.0)
**SENSITIVE DATA WARNING**

This directory manages the bot's behavior and authentication.

* `dynamic_settings.json`: Real-time bot configuration (Budget, Stop Loss, etc.). Controlled via the Terminal UI.
* `.env`: Private API Keys and Broker credentials. **NEVER COMMIT OR SHARE THIS FILE.**
* `settings_manager.py`: Core logic for reading and writing persistent configuration.
