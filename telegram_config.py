import os
import json
import hashlib
import time
import requests
from datetime import datetime, timezone, timedelta

# SECURITY: Never hardcode bot tokens here — this file is tracked in git.
# Credentials resolve in this order:
#   1. Environment variables: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
#      (set in GitHub Actions secrets for cloud runs)
#   2. Local untracked config.json (see config.example.json for template)
#   3. None -> Telegram alerts are disabled with a warning (nothing crashes)

CACHE_FILE = os.path.join("data", "telegram_broadcast_cache.json")

def get_telegram_credentials():
    """Returns Telegram Bot Token and Chat ID, or (None, None) if unconfigured.
    Resolution order: Environment Variables -> local config.json.
    Keep secrets in GitHub repo Secrets (cloud) and config.json (local, gitignored).
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

    # Placeholder sanity check: a template value is as bad as a missing one
    if tg_token and "YOUR_TELEGRAM" in str(tg_token).upper():
        tg_token = None
    if tg_chat_id and "YOUR_TELEGRAM" in str(tg_chat_id).upper():
        tg_chat_id = None

    if not tg_token or not tg_chat_id:
        print("[WARN] Telegram credentials not configured. "
              "Set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID env vars "
              "or fill config.json (template: config.example.json). Alerts disabled.")

    return tg_token, tg_chat_id

def send_deduplicated_telegram_alert(message, bot_token=None, chat_id=None, force=False, min_interval_seconds=600):
    """Sends Telegram message with strict Anti-Duplicate / Anti-Stale hash filtering.
    Prevents sending old, stale, or identical duplicate updates to the Telegram channel.
    """
    if not bot_token or not chat_id:
        bot_token, chat_id = get_telegram_credentials()

    if not bot_token or not chat_id:
        print("[WARN] Telegram broadcast skipped: no credentials configured.")
        return False

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
        if res.status_code == 400:
            # Markdown formatting error (e.g. unescaped _ or *). Retry with plain text.
            payload.pop("parse_mode", None)
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
            print(f"[ERROR] Telegram API Error ({res.status_code})")
            return False
    except requests.RequestException as e:
        print(f"[ERROR] Telegram send failed: {type(e).__name__}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to dispatch Telegram broadcast: {type(e).__name__}")
        return False
