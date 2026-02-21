import datetime

# This dictionary lives in the server's memory 24/7
GLOBAL_STATE = {
    "highest_conviction": {
        "module": "System Initializing...",
        "signal": "Scanning...",
        "score": 0,
        "timestamp": datetime.datetime.now().isoformat(),
        "reason": "Waiting for data..."
    },
    "recent_trades": [] # Stores the last 5 executed trades
}

def update_conviction(module, score, signal, reason):
    """
    Called by modules when they find something good.
    Only updates if the new score is higher than the current king.
    """
    current_best = GLOBAL_STATE["highest_conviction"]["score"]
    
    # Logic: New high score OR the current best is stale (>1 hour old)
    is_stale = (datetime.datetime.now() - datetime.datetime.fromisoformat(GLOBAL_STATE["highest_conviction"]["timestamp"])).total_seconds() > 3600
    
    if score > current_best or is_stale:
        GLOBAL_STATE["highest_conviction"] = {
            "module": module,
            "signal": signal,
            "score": score,
            "timestamp": datetime.datetime.now().isoformat(),
            "reason": reason
        }

def log_trade(module, action, price, result="OPEN"):
    """
    Logs a trade execution for the 'History' tab.
    """
    trade = {
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "module": module,
        "action": action,
        "price": price,
        "result": result
    }
    # Keep only last 10 trades
    GLOBAL_STATE["recent_trades"].insert(0, trade)
    GLOBAL_STATE["recent_trades"] = GLOBAL_STATE["recent_trades"][:10]
