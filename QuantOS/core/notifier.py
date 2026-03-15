import os
import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

try:
    from core.discord_notifier import DiscordNotifier as _DiscordNotifier
    _NOTIFIER_AVAILABLE = True
except Exception:
    _NOTIFIER_AVAILABLE = False

import requests


def send_alert(message, webhook_url=None):
    """
    Sends a message to Discord.
    Routes through DiscordNotifier when available for intel enrichment.
    Falls back to raw requests.post if DiscordNotifier cannot be imported.
    """
    url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
    if not url:
        print("⚠️ Voice Error: No Webhook URL provided.")
        return

    if _NOTIFIER_AVAILABLE:
        notifier = _DiscordNotifier(webhook_url=url, username="Survivor Bot 🤖")
        notifier.send_alert("Cemini Alert", message, alert_type="INFO", enrich=False)
        return

    data = {
        "content": message,
        "Username": "Survivor Bot 🤖"
    }

    try:
        result = requests.post(url, json=data, timeout=10)
        if result.status_code == 204:
            print("✅ Discord Notification Sent.")
        else:
            print(f"⚠️ Discord Failed: {result.status_code} - {result.text}")
    except requests.exceptions.Timeout:
        print("⚠️ Discord Error: Request timed out.")
    except Exception as e:
        print(f"⚠️ Discord Error: {e}")
