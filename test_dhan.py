import os
import json
import requests
from datetime import datetime, timedelta

def test_dhan_historical():
    config_file = "config.json"
    if not os.path.exists(config_file):
        print("[ERROR] config.json file not found!")
        return

    try:
        with open(config_file, "r") as cf:
            config = json.load(cf)
        
        dhan = config.get("dhan", {})
        client_id = dhan.get("client_id")
        access_token = dhan.get("access_token")
        
        if not client_id or "YOUR_DHAN" in client_id or not access_token or "YOUR_DHAN" in access_token:
            print("[ERROR] Please update your actual client_id and access_token in config.json!")
            return
            
        print("Connecting to Dhan Profile API...")
        profile_url = "https://api.dhan.co/v2/profile"
        headers = {
            "client-id": client_id,
            "access-token": access_token,
            "Content-Type": "application/json"
        }
        
        profile_res = requests.get(profile_url, headers=headers, timeout=15)
        if profile_res.status_code != 200:
            print(f"[ERROR] Dhan Profile Authentication Failed: {profile_res.text}")
            return
            
        client_name = profile_res.json().get("clientName", "User")
        print(f"Authenticated as: {client_name}")
        
        print("\nTesting Dhan Intraday Chart API for RELIANCE (ID: 2885)...")
        chart_url = "https://api.dhan.co/v2/charts/intraday"
        
        # Request past 3 days of 15m data
        today = datetime.now()
        from_date = (today - timedelta(days=3)).strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")
        
        payload = {
            "securityId": "2885",
            "exchangeSegment": "NSE_EQ",
            "instrument": "EQUITY",
            "fromDate": from_date,
            "toDate": to_date,
            "interval": "15"
        }
        
        chart_res = requests.post(chart_url, json=payload, headers=headers, timeout=15)
        
        if chart_res.status_code == 200:
            res_json = chart_res.json()
            status = res_json.get("status")
            chart_data = res_json.get("data", {})
            
            if "t" in chart_data and len(chart_data["t"]) > 0:
                print("=========================================")
                print("🎉 DHAN INTRADAY CHART API WORKS! 🎉")
                print("=========================================")
                print(f"Total 15m Candles Fetched: {len(chart_data['t'])}")
                print(f"Latest Close Price       : Rs {chart_data['c'][-1]}")
                print("=========================================\n")
            else:
                print(f"[ERROR] API returned success status but no chart data: {res_json}")
        else:
            print(f"[ERROR] Chart API Request Failed with status {chart_res.status_code}")
            print(f"Response: {chart_res.text}")
            
    except Exception as e:
        print(f"[ERROR] Exception during chart test: {e}")

if __name__ == "__main__":
    test_dhan_historical()
