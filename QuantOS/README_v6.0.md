# QuantOS v11.0.0 - The Institutional CFO Update

## New Features
- **Redesigned Dashboard**: High-contrast dark theme (#06090f) for better readability.
- **Strategy Lab (Route: `/backtester`)**: Dedicated page for historical simulations.
- **Portfolio Manager**: Dual budget modes (Fixed Amount vs % of Equity).
- **Bot Control**: Added "Pause/Resume" functionality and immediate "Panic Sell" from the UI.
- **Optimized Layout**: Compact grid design for information density.

## Technical Changes
- Split routes in `server.py` using Jinja2 templates.
- Updated `SettingsManager` to support budget modes and pause state.
- Refactored `main.py` to calculate dynamic order sizes based on real-time equity when in % mode.
