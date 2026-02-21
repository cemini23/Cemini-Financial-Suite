import robin_stocks.robinhood as rh
import os
import sys
from dotenv import load_dotenv
from core import notifier
from core.logger_config import get_logger

logger = get_logger("report")

# --- FORCE CORRECT FOLDER ---
os.chdir(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

UserNAME = os.getenv("RH_UserNAME")
PASSWORD = os.getenv("RH_PASSWORD")
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def login():
    try:
        rh.login(Username=UserNAME, password=PASSWORD, store_session=True)
    except:
        rh.login(Username=UserNAME, password=PASSWORD)

def generate_daily_report():
    logger.info("📊 Generating End-of-Day Report...")
    login()
    
    # 1. Get Cash & Profile Data
    profile = rh.profiles.load_account_profile()
    cash = float(profile.get('portfolio_cash', 0))
    
    # 2. Get the "Real Truth" (Holdings)
    holdings = rh.build_holdings()
    
    # 3. Calculate Totals
    invested_value = 0.0
    total_cost = 0.0
    total_pnl = 0.0
    
    report_lines = []
    
    if holdings:
        for symbol, data in holdings.items():
            # SAFELY GET DATA
            price = float(data.get('price', 0))
            quantity = float(data.get('quantity', 0))
            avg_buy_price = float(data.get('average_buy_price', 0))
            equity = float(data.get('equity', 0))
            
            # CALCULATE COST MANUALLY
            cost_basis = avg_buy_price * quantity
            
            # Calculate P&L
            pnl_dollar = equity - cost_basis
            pnl_percent = (pnl_dollar / cost_basis) * 100 if cost_basis > 0 else 0
            
            invested_value += equity
            total_cost += cost_basis
            total_pnl += pnl_dollar
    
            # Format Line
            icon = "🟢" if pnl_dollar >= 0 else "🔴"
            report_lines.append(f"{icon} **{symbol}**: ${equity:.2f} ({pnl_percent:+.2f}%)")

    # 4. Portfolio Summary
    net_worth = cash + invested_value
    total_return_pct = (total_pnl / total_cost) * 100 if total_cost > 0 else 0
    emoji = "🚀" if total_pnl >= 0 else "🔻"
    
    # Check if list is empty
    if not report_lines:
        positions_text = "(No positions held)"
    else:
        positions_text = "\n".join(report_lines)

    summary = (
        f"🌙 **END OF DAY REPORT** 🌙\n"
        f"----------------------------\n"
        f"🏆 **Net Worth:** ${net_worth:,.2f}\n"
        f"💵 **Cash:** ${cash:,.2f}\n"
        f"📈 **Invested:** ${invested_value:,.2f}\n"
        f"{emoji} **Total P&L:** ${total_pnl:+.2f} ({total_return_pct:+.2f}%)\n"
        f"----------------------------\n"
        f"**Positions:**\n" + positions_text
    )
    
    # 5. Send to Discord
    logger.info(summary)
    notifier.send_alert(summary, WEBHOOK_URL)

if __name__ == "__main__":
    try:
        generate_daily_report()
    except Exception as e:
        logger.error(f"❌ Report Failed: {e}")
        notifier.send_alert(f"⚠️ Report Failed: {e}", WEBHOOK_URL)