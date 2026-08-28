import os
import json
import urllib.parse
import requests

class WhatsAppNotifier:
    """WhatsApp Instant Alert Gateway Engine (CallMeBot / Twilio Integration)."""

    @classmethod
    def load_whatsapp_credentials(cls):
        phone = os.environ.get("WHATSAPP_PHONE")
        api_key = os.environ.get("WHATSAPP_API_KEY")
        config_file = "config.json"

        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as cf:
                    config = json.load(cf)
                wa = config.get("whatsapp_callmebot", {})
                if wa.get("enabled"):
                    if not phone and wa.get("phone_number") and not wa.get("phone_number").startswith("YOUR_PHONE"):
                        phone = wa.get("phone_number")
                    if not api_key and wa.get("api_key") and not wa.get("api_key").startswith("YOUR_CALLMEBOT"):
                        api_key = wa.get("api_key")
            except Exception:
                pass

        return phone, api_key

    @classmethod
    def send_whatsapp_alert(cls, message_text, phone=None, api_key=None):
        """Transmits instant WhatsApp alert via CallMeBot API."""
        if not phone or not api_key:
            loaded_phone, loaded_key = cls.load_whatsapp_credentials()
            phone = phone or loaded_phone
            api_key = api_key or loaded_key

        if not phone or not api_key:
            print("[INFO] WhatsApp credentials not configured. Skipping WhatsApp alert.")
            return {"status": "SKIPPED", "reason": "UNCONFIGURED"}

        encoded_msg = urllib.parse.quote_plus(message_text)
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_msg}&apikey={api_key}"

        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                print(f"[INFO] WhatsApp Alert sent successfully to {phone}!")
                return {"status": "SUCCESS", "phone": phone}
            else:
                print(f"[WARNING] CallMeBot returned status {res.status_code}: {res.text}")
                return {"status": "FAILED", "status_code": res.status_code}
        except Exception as e:
            print(f"[ERROR] Exception sending WhatsApp alert: {e}")
            return {"status": "ERROR", "error": str(e)}

# Helper function
def send_whatsapp_alert(message_text):
    return WhatsAppNotifier.send_whatsapp_alert(message_text)
