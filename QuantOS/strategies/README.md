# Strategies
**This is where the alpha is generated.**
Add new betting or trading logic here.
* `analysis.py`: New 0-100 confidence scoring logic (Supports pre-calculated indicators).
* `backtester.py`: Robust historical replay engine with JIT indicators and extreme debugging.
* Focus on signal generation (when to buy/sell).
* Do not put execution code here; just return the signal to Core.
