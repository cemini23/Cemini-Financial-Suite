import requests
import json
import os

GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
GRAFANA_USER = os.getenv("GRAFANA_USER", "admin")
GRAFANA_PASS = os.getenv("GRAFANA_PASS", "admin")

def export_dashboard():
    print("🚀 Exporting Grafana Dashboard...")
    try:
        # 1. Get all dashboards
        search_resp = requests.get(
            f"{GRAFANA_URL}/api/search",
            auth=(GRAFANA_USER, GRAFANA_PASS)
        )
        dashboards = search_resp.json()

        if not dashboards:
            print("⚠️ No dashboards found to export.")
            return

        # 2. Export the first one found (typically our main one)
        uid = dashboards[0]['uid']
        title = dashboards[0]['title']

        db_resp = requests.get(
            f"{GRAFANA_URL}/api/dashboards/uid/{uid}",
            auth=(GRAFANA_USER, GRAFANA_PASS)
        )
        db_json = db_resp.json()['dashboard']

        # Strip ID to make it portable for provisioning
        db_json['id'] = None

        filename = "trading_dashboard.json"
        with open(filename, "w") as f:
            json.dump(db_json, f, indent=2)

        print(f"✅ Exported '{title}' to {filename}")

    except Exception as e:
        print(f"❌ Export Failed: {e}")

if __name__ == "__main__":
    export_dashboard()
