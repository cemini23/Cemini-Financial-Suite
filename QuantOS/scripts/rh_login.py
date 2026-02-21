import robin_stocks.robinhood as r
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path to find .env if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def generate_session():
    # Look for .env in the project root (one level up from scripts/)
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(dotenv_path)
    
    username = os.getenv("RH_USERNAME") or os.getenv("ROBINHOOD_USERNAME")
    password = os.getenv("RH_PASSWORD") or os.getenv("ROBINHOOD_PASSWORD")
    
    if not username or not password:
        print("❌ Error: RH_USERNAME or RH_PASSWORD not found in .env file.")
        return

    print(f"📱 Logging in as {username}... Check your phone for a Robinhood code if prompted.")
    # This will pause and ask for standard input in the terminal
    try:
        login_data = r.login(username, password, store_session=True)
        
        # Check if login_data indicates success (usually contains 'access_token')
        if login_data and 'access_token' in login_data:
            print("✅ Session token saved! QuantOS can now run headlessly.")
        else:
            error_msg = login_data.get('detail', 'Unknown error') if isinstance(login_data, dict) else 'Login failed'
            print(f"❌ Login failed: {error_msg}")
            print("💡 Tip: Double-check your credentials and ensure MFA is set up correctly on Robinhood.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    generate_session()
