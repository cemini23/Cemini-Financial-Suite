"""
QuantOS™ v7.0.0 - Ledger System
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
import csv
import os
import pandas as pd
from datetime import datetime
from core.logger_config import get_logger

logger = get_logger("ledger")

# FORCE CORRECT FOLDER
os.chdir(os.path.dirname(os.path.abspath(__file__)))

LEDGER_FILE = "survivor_ledger.csv"

def init_ledger():
    """
    Creates the CSV file if it doesn't exist or adds missing columns.
    """
    if not os.path.exists(LEDGER_FILE):
        logger.info("📒 Creating new ledger...")
        with open(LEDGER_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Action", "Ticker", "Price", "Quantity", "Reason", "Est_Tax_Impact", "Broker"])
    else:
        # Check if Quantity column exists, if not add it
        df = pd.read_csv(LEDGER_FILE)
        updated = False
        if "Est_Tax_Impact" not in df.columns:
            logger.info("Updating ledger format to include Est_Tax_Impact...")
            df["Est_Tax_Impact"] = 0.0
            updated = True
        if "Broker" not in df.columns:
            logger.info("Updating ledger format to include Broker...")
            df["Broker"] = "unknown"
            updated = True
            
        if updated:
            cols = ["Date", "Action", "Ticker", "Price", "Quantity", "Reason", "Est_Tax_Impact", "Broker"]
            df = df[cols]
            df.to_csv(LEDGER_FILE, index=False)

def record_trade(action, ticker, price, quantity, reason, tax_impact=0.0, broker="unknown"):
    """
    Logs a trade (BUY or SELL) into the CSV with quantity, tax impact and broker.
    """
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(LEDGER_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([date, action, ticker, price, quantity, reason, tax_impact, broker])
    
    logger.info(f"📝 Ledger Updated: {action} {quantity} {ticker} @ ${price:.2f} (Tax: ${tax_impact:.2f}, Broker: {broker})")

def get_open_positions():
    """
    Calculates current open positions using FIFO logic.
    Returns a dict: { ticker: { 'shares_held': X, 'cost_basis': Y, 'avg_price': Z } }
    """
    if not os.path.exists(LEDGER_FILE):
        return {}
        
    try:
        df = pd.read_csv(LEDGER_FILE)
        positions = {}

        for _, row in df.iterrows():
            ticker = row['Ticker']
            action = row['Action']
            price = float(row['Price'])
            qty = float(row['Quantity'])

            if ticker not in positions:
                positions[ticker] = [] # List of [qty, price] for FIFO

            if action == 'BUY':
                positions[ticker].append([qty, price])
            elif action == 'SELL':
                # FIFO logic: reduce quantity from the oldest buys
                shares_to_sell = qty
                while shares_to_sell > 0 and positions[ticker]:
                    if positions[ticker][0][0] <= shares_to_sell:
                        shares_to_sell -= positions[ticker][0][0]
                        positions[ticker].pop(0)
                    else:
                        positions[ticker][0][0] -= shares_to_sell
                        shares_to_sell = 0

        # Collapse list into summary
        summary = {}
        for ticker, lots in positions.items():
            total_shares = sum(lot[0] for lot in lots)
            if total_shares > 0.000001: # Avoid floating point dust
                total_cost = sum(lot[0] * lot[1] for lot in lots)
                summary[ticker] = {
                    'shares_held': total_shares,
                    'cost_basis': total_cost,
                    'avg_price': total_cost / total_shares
                }
        return summary
    except Exception as e:
        print(f"⚠️ Error calculating FIFO positions: {e}")
        return {}

def has_position(ticker):
    positions = get_open_positions()
    return ticker in positions

def get_average_buy_price(ticker):
    positions = get_open_positions()
    if ticker in positions:
        return positions[ticker]['avg_price']
    return None

def get_quantity_held(ticker):
    positions = get_open_positions()
    if ticker in positions:
        return positions[ticker]['shares_held']
    return 0

def get_trade_history(limit=50):
    """
    Returns the last 'limit' trades from the ledger.
    """
    if not os.path.exists(LEDGER_FILE):
        return []
    try:
        df = pd.read_csv(LEDGER_FILE)
        # Get last N trades and convert to list of dicts
        history = df.tail(limit).to_dict('records')
        # Reverse to show newest first
        return history[::-1]
    except Exception as e:
        print(f"⚠️ Error reading history: {e}")
        return []
