import requests

def send_alert(message, webhook_url):
    """
    Sends a message to Discord.
    Requires the webhook_url to be passed in.
    """
    if not webhook_url:
        print("⚠️ Voice Error: No Webhook URL provided.")
        return

    data = {
        "content": message,
        "Username": "Survivor Bot 🤖"
    }

    try:
        result = requests.post(webhook_url, json=data, timeout=10)
        if result.status_code == 204:
            print("✅ Discord Notification Sent.")
        else:
            print(f"⚠️ Discord Failed: {result.status_code} - {result.text}")
    except requests.exceptions.Timeout:
        print("⚠️ Discord Error: Request timed out.")
    except Exception as e:
        print(f"⚠️ Discord Error: {e}")
