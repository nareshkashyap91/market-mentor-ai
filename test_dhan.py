import os
import json
import requests

def test_dhan_connection():
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
            
        print("Connecting to Dhan API...")
        url = "https://api.dhan.co/v2/profile"
        headers = {
            "client-id": client_id,
            "access-token": access_token,
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print("\n=========================================")
            print("  DHAN API CONNECTION SUCCESSFUL!  ")
            print("=========================================")
            # Dhan profile API returns details like clientName, email, etc.
            client_name = data.get("clientName", "User")
            print(f"Client Name : {client_name}")
            print(f"Status      : Authorized and Active")
            print("=========================================\n")
        else:
            print(f"\n[ERROR] Dhan API Authentication Failed (Status {response.status_code})")
            print(f"Response: {response.text}\n")
            
    except Exception as e:
        print(f"[ERROR] Exception during API test: {e}")

if __name__ == "__main__":
    test_dhan_connection()
