import robin_stocks.robinhood as r
import sys

def manual_login():
    print("--- 🔐 Robinhood Manual Authentication ---")
    print("This script will help you authorize your session manually.")
    
    try:
        username = input("Enter Robinhood Email: ")
        password = input("Enter Robinhood Password: ")
        
        print(f"\n🚀 Attempting login for {username}...")
        # r.login will handle the MFA prompt (SMS/Email) automatically in the terminal
        login_data = r.login(username, password, store_session=True)
        
        if login_data and 'access_token' in login_data:
            print("\n✅ SUCCESS: Login successful!")
            print("The session token has been saved to '.tokens.pickle'.")
            print("QuantOS can now use this session to run headlessly.")
        else:
            print(f"\n❌ FAILED: Login response was unexpected.")
            print(f"Response: {login_data}")
            print("\n💡 Tip: If you get 'Challenge Required', wait for the SMS/Email and type it when prompted.")
            
    except EOFError:
        print("\n\n⚠️ Input interrupted. Please run the script in a normal terminal.")
    except Exception as e:
        print(f"\n❌ ERROR: An unexpected error occurred: {e}")

if __name__ == "__main__":
    manual_login()
