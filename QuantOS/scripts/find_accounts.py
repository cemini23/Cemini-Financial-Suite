import robin_stocks.robinhood as rh
import os
from dotenv import load_dotenv

# Load login info
load_dotenv()
User = os.getenv("RH_UserNAME")
PASS = os.getenv("RH_PASSWORD")

# Login
def find_accounts():
    rh.login(User, PASS)

    # Get all accounts
    accounts = rh.load_account_profile()

    # If 'accounts' is just a dictionary (one account), we wrap it in a list to make the loop work
    if isinstance(accounts, dict):
        accounts = [accounts]

    print("\n--- 🕵️ FOUND ACCOUNTS ---")
    for acc in accounts:
        print(f"Name/Type: {acc.get('type', 'Unknown')} | Account Number: {acc.get('account_number')}")
        print(f"Cash Available: ${acc.get('cash', '0.00')}")
        print(f"Buying Power: ${acc.get('buying_power', '0.00')}")
        print("-------------------------")

if __name__ == '__main__':
    find_accounts()