import robin_stocks.robinhood as r
import os
from dotenv import load_dotenv

# Force reload of env
load_dotenv()
username = os.getenv("RH_USERNAME")
password = os.getenv("RH_PASSWORD")

print(f"Debug: Attempting login for {username}")
try:
    # login returns a dictionary with 'access_token', 'expires_in', 'token_type', 'scope', 'mfa_code'
    # if it fails, it might return a dict with 'detail'
    res = r.login(username, password, store_session=True)
    print(f"DEBUG RESPONSE: {res}")
except Exception as e:
    print(f"DEBUG EXCEPTION: {e}")
