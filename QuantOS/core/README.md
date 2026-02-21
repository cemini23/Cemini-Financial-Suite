# Core System (v10.1.0)
**The Engine Room: Do not touch unless you know what you are doing.**

This folder contains the core execution engine, risk controls, and institutional logic.

* `execution.py`: The Gatekeeper. Handles Smart Limit orders and marketable limit logic.
* `broker_interface.py`: The Unified Adapter. Standardizes communication across all brokers.
* `tax_engine.py`: The CFO. Enforces Wash Sale Guards and tracks estimated tax impacts.
* `money_manager.py`: Calculates dynamic position sizing based on AI conviction.
* `risk_manager.py`: Global safety checks, stop-losses, and portfolio portfolio protection.
* `brain.py`: Central coordination for data flow and signal routing.
