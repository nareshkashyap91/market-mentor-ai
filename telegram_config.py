import os
import json
import hashlib
import time
import requests
from datetime import datetime, timezone, timedelta

DEFAULT_BOT_TOKEN = "8702571549:AAGRucsXGDKGHmZZ9JtgRTvttRFKq8fVHAU"
DEFAULT_CHAT_ID = "-1004347306692"
CACHE_FILE = os.path.join("data", "telegram_broadcast_cache.json")

def get_telegram_credentials():
    """Returns Telegram Bot Token and Chat ID.
    Checks Environment Variables -> config.json -> Production Fallback Defaults.
    Ensures 100% Cloud Execution compatibility even when local PC is OFF.
    """
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    config_file = "config.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as cf:
                config = json.load(cf)
            tg = config.get("telegram", {})
            if not tg_token:
                tg_token = tg.get("bot_token")
            if not tg_chat_id:
                tg_chat_id = tg.get("chat_id")
        except Exception:
            pass

    if not tg_token:
        tg_token = DEFAULT_BOT_TOKEN
    if not tg_chat_id:
        tg_chat_id = DEFAULT_CHAT_ID

    return tg_token, tg_chat_id

def send_deduplicated_telegram_alert(message, bot_token=None, chat_id=None, force=False, min_interval_seconds=600):
    """Sends Telegram message with strict Anti-Duplicate / Anti-Stale hash filtering.
    Prevents sending old, stale, or identical duplicate updates to the Telegram channel.
    """
    if not bot_token or not chat_id:
        bot_token, chat_id = get_telegram_credentials()

    if not message or not message.strip():
        return False

    # Create content hash (ignoring exact minute timestamps to compare core signals)
    normalized_msg = "\n".join([line for line in message.splitlines() if "Time:" not in line and "🕒" not in line])
    msg_hash = hashlib.sha256(normalized_msg.encode('utf-8')).hexdigest()

    now_epoch = time.time()
    cache_data = {}

    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
        except Exception:
            cache_data = {}

    last_hash = cache_data.get("last_hash")
    last_epoch = cache_data.get("last_epoch", 0)

    # Deduplication Guard: Check if identical alert was sent recently
    if not force and last_hash == msg_hash and (now_epoch - last_epoch) < min_interval_seconds:
        print("[INFO] Duplicate alert suppressed. No new price/signal change detected since last broadcast.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            print("[INFO] Telegram alert broadcasted successfully!")
            # Update cache
            cache_data["last_hash"] = msg_hash
            cache_data["last_epoch"] = now_epoch
            cache_data["last_time"] = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S IST")
            
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
            return True
        else:
            print(f"[ERROR] Telegram API Error ({res.status_code}): {res.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to dispatch Telegram broadcast: {e}")
        return False
