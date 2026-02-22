# CHANGELOG - QuantOS v15.0.0 (2026-02-22)

## [15.0.0] - 2026-02-22

### Added
- **Intel Bus (Shared Intelligence Layer)**: New `core/intel_bus.py` — a Redis-backed cross-system signal bus enabling real-time intelligence sharing between QuantOS and Kalshi by Cemini without HTTP calls. Publishes and reads 8 shared keys (`intel:btc_sentiment`, `intel:fed_bias`, `intel:btc_volume_spike`, `intel:social_score`, `intel:weather_edge`, `intel:vix_level`, `intel:spy_trend`, `intel:portfolio_heat`) with 300-second TTL and fail-silent error handling.
- **Portfolio Heat Guard**: `CeminiAutopilot` reads `intel:portfolio_heat` from the bus. If combined active positions exceed 80% of capacity, new Kalshi trades are automatically paused for 30 seconds.
- **Confluence Score Bonuses**: `TradingEngine` applies a +5% confidence bonus when Fed bias is dovish and +3% when social sentiment score exceeds 0.3, both sourced from the Intel Bus.
- **Paper Mode (Kill Switch)**: All execution paths locked to simulation. Controlled via `QuantOS/config/dynamic_settings.json` (`environment: PAPER`) and `Kalshi by Cemini/settings.json` (`paper_mode: true`, `trading_enabled: false`).
- **CI/CD Docker Restart**: GitHub Actions deploy workflow now runs `docker compose down && docker compose up --build -d` after code sync, ensuring changes take effect automatically without manual VM intervention.
- **CLOUDFLARE_TUNNEL_TOKEN**: Added to `.env.example` with documentation pointer for Cloudflare Zero Trust tunnel configuration.

### Changed
- **QuantOSBridge HTTP → Intel Bus**: `PowellAnalyzer` and `MarketRover` no longer make HTTP calls to `localhost:8001` (which always fails in Docker). Both now read sentiment directly via `IntelReader` — same Redis instance, no network hop.
- **Redis Authentication**: All services now pass `REDIS_PASSWORD` env var when connecting to Redis. Affected files: `ems/main.py`, `logger_service.py`, `panic_button.py`, `agents/orchestrator.py`, `QuantOS/core/engine.py`.
- **BigQuery Table Name**: `QuantOS/core/harvester.py` default table corrected from `market_data` to `market_ticks`, matching `bq_signals.py`.

### Fixed
- Fixed `QuantOSBridge` failing silently in Docker due to `127.0.0.1` localhost assumption in a containerized network.
- Fixed BigQuery table name mismatch between harvester and signal engine causing missing data.
- Fixed missing Redis password in multiple service connection strings (Redis auth was enforced in docker-compose but not in client code).
- Resolved pre-commit hook violations (trailing whitespace, missing end-of-file newline) across 8 files.

---

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
