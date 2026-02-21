import pandas as pd
import numpy as np
import os
from config.settings_manager import settings_manager

# FORCE CORRECT FOLDER
os.chdir(os.path.dirname(os.path.abspath(__file__)))

LEDGER_FILE = "survivor_ledger.csv"

def get_performance_stats():
    """
    Reads the ledger, calculates detailed metrics including Sharpe and Tax Efficiency.
    Now also returns 'activity_count' to track buys/sells even if PnL isn't realized.
    """
    if not os.path.exists(LEDGER_FILE):
        return {"win_rate": 0, "status": "No Data", "activity_count": 0}

    try:
        df = pd.read_csv(LEDGER_FILE)
    except Exception:
        return {"win_rate": 0, "status": "Empty Ledger", "activity_count": 0}

    if df.empty:
        return {"win_rate": 0, "status": "Empty Ledger", "activity_count": 0}

    # Track completed trades (FIFO matching)
    completed_profits = []
    daily_pnl = {}
    broker_daily_pnl = {} # {date: {broker: pnl}}
    total_tax_impact = 0.0
    positions = {} # ticker: [[qty, price], ...]
    
    # NEW: Track total activity for today
    import datetime
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    today_activity = 0

    for _, row in df.iterrows():
        ticker = row['Ticker']
        action = row['Action']
        price = float(row['Price'])
        qty = float(row['Quantity'])
        date_full = str(row['Date'])
        date_str = date_full.split(' ')[0]
        tax_impact = float(row.get('Est_Tax_Impact', 0.0))
        broker = row.get('Broker', 'unknown')
        
        # Track activity for today
        if date_str == today_str:
            today_activity += 1

        total_tax_impact += tax_impact

        if ticker not in positions:
            positions[ticker] = []

        if action == 'BUY':
            positions[ticker].append([qty, price])
        elif action == 'SELL':
            shares_to_sell = qty
            trade_profit = 0
            while shares_to_sell > 0 and positions[ticker]:
                buy_qty, buy_price = positions[ticker][0]
                
                if buy_qty <= shares_to_sell:
                    trade_profit += buy_qty * (price - buy_price)
                    shares_to_sell -= buy_qty
                    positions[ticker].pop(0)
                else:
                    trade_profit += shares_to_sell * (price - buy_price)
                    positions[ticker][0][0] -= shares_to_sell
                    shares_to_sell = 0
            
            completed_profits.append(trade_profit)
            daily_pnl[date_str] = daily_pnl.get(date_str, 0.0) + trade_profit
            
            if date_str not in broker_daily_pnl:
                broker_daily_pnl[date_str] = {}
            broker_daily_pnl[date_str][broker] = broker_daily_pnl[date_str].get(broker, 0.0) + trade_profit

    # Base Metrics
    stats = {
        "win_rate": 0,
        "total_profit": 0,
        "net_profit": 0,
        "tax_efficiency": 0,
        "profit_factor": 0,
        "sharpe_ratio": 0,
        "total_trades": len(completed_profits),
        "daily_pnl": daily_pnl,
        "broker_daily_pnl": broker_daily_pnl,
        "status": "Active",
        "today_activity": today_activity
    }

    if completed_profits:
        wins = [p for p in completed_profits if p > 0]
        losses = [p for p in completed_profits if p < 0]
        
        stats["win_rate"] = (len(wins) / len(completed_profits)) * 100
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        stats["profit_factor"] = gross_profit / gross_loss if gross_loss > 0 else gross_profit
        
        stats["total_profit"] = sum(completed_profits)
        stats["net_profit"] = stats["total_profit"] - total_tax_impact
        stats["tax_efficiency"] = (stats["net_profit"] / stats["total_profit"] * 100) if stats["total_profit"] > 0 else 0
        
        # Sharpe Ratio (Simplified Daily)
        if len(daily_pnl) > 1:
            returns = pd.Series(list(daily_pnl.values()))
            stats["sharpe_ratio"] = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0

    return stats

def get_coaching_advice(stats):
    """
    Returns a 'Mode' for the Brain based on performance.
    """
    if stats['status'] != "Active":
        return "NORMAL", "Not enough data yet. Stick to the plan."
        
    wr = stats['win_rate']
    
    if wr < 40:
        return "DEFENSIVE", "⚠️ We are losing too much. Tightening RSI to < 25."
    elif wr > 70:
        return "AGGRESSIVE", "🔥 We are on fire! Loosening RSI to < 35."
    else:
        return "NORMAL", "✅ Steady performance. Keeping RSI at 30."

if __name__ == "__main__":
    stats = get_performance_stats()
    mode, advice = get_coaching_advice(stats)
    print(f"📊 Win Rate: {stats['win_rate']:.1f}%")
    print(f"💰 Total Profit: ${stats['total_profit']:.2f}")
    print(f"🧠 Coach Says: {advice}")
