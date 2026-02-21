# CHANGELOG - QuantOS v11.0.0
- **Async Core Engine**: Implemented `AsyncScanner` for high-speed, non-blocking market data fetching.
- **Suite Protocol Bridge**: Added `/api/status` and `/api/hedge` endpoints to enable tandem operation with Kalshi by Cemini.
- **Fixed Port Mapping**: Standardized on Port 8001 to prevent conflicts and ensure stable inter-project communication.
- **Performance**: Capable of scanning 200+ tickers in under 1 second.

# CHANGELOG - QuantOS v10.2.0
- **Live UI Bridge**: Connected engine scan logs and real-time Robinhood positions to the Dashboard.
- **UI Resilience**: Added safety checks to prevent dashboard crashes when encountering null or incomplete market data.
- **Harvester 2.0**: Implemented a non-blocking background writer thread for high-frequency data recording.
- **Bug Fixes**: Corrected Robinhood login case-sensitivity issues and stabilized port binding.

# CHANGELOG - QuantOS v6.0

## [4.0.0] - 2026-02-16

### Added
- **Dynamic Settings Manager**: Refactored config system to `SettingsManager`. Settings are now loaded from `config/dynamic_settings.json` and can be updated at runtime without restarting the bot.
- **Professional Command Center UI**: New Bootstrap 5 dashboard in `static/index.html`.
- **Config Panel**: Web interface to adjust Budget, Stop Loss, Take Profit, and Entry Thresholds.
- **Historical Simulation**: Upgraded `BacktestEngine` with a `run_historical_simulation` method that uses current UI settings to project performance (2014-Present).
- **Security Sanitizer**: New script `scripts/sanitize_project.py` to prevent accidental credential leaks.
- **Tri-Sync Deployment**: Master script `scripts/deploy_v4.sh` for multi-location synchronization and safety checks.

### Changed
- Moved `main.py` and `core/risk_manager.py` to use dynamic settings.
- Optimized `interface/server.py` for v4.0 API endpoints.
- Updated `.gitignore` to strictly exclude sensitive and temporary files.

### Fixed
- Fixed `asyncio` nested loop error in Alpaca stream processor.
- Fixed `market_value` KeyError in Risk Manager.
- Enforced `PAPER` mode check in all execution paths.
