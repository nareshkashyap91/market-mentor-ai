import os
import json
import hashlib
import time
import requests
from datetime import datetime, time as dt_time, timedelta
from zoneinfo import ZoneInfo
from atomic_io import atomic_write_json, safe_read_json

# SECURITY: Never hardcode bot tokens here — this file is tracked in git.
# Credentials resolve in this order:
#   1. Environment variables: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ADMIN_CHAT_ID
#      (set in GitHub Actions secrets for cloud runs)
#   2. Local untracked config.json (see config.example.json for template)
#   3. None -> Telegram alerts are disabled with a warning (nothing crashes)

CACHE_FILE = os.path.join("data", "telegram_broadcast_cache.json")
KOLKATA_TZ = ZoneInfo("Asia/Kolkata")
HOLIDAYS_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config", "nse_holidays.json")

def get_telegram_credentials(admin=False):
    """Returns Telegram Bot Token and Chat ID, or (None, None) if unconfigured.
    Resolution order: Environment Variables -> local config.json.
    Keep secrets in GitHub repo Secrets (cloud) and config.json (local, gitignored).
    """
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.environ.get("TELEGRAM_ADMIN_CHAT_ID") if admin else os.environ.get("TELEGRAM_CHAT_ID")
    if admin and not tg_chat_id:
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
                tg_chat_id = tg.get("admin_chat_id") if admin else tg.get("chat_id")
                if admin and not tg_chat_id:
                    tg_chat_id = tg.get("chat_id")
        except Exception:
            pass

    # Placeholder sanity check: a template value is as bad as a missing one
    if tg_token and "YOUR_TELEGRAM" in str(tg_token).upper():
        tg_token = None
    if tg_chat_id and "YOUR_TELEGRAM" in str(tg_chat_id).upper():
        tg_chat_id = None

    if not tg_token or not tg_chat_id:
        if not admin:
            print("[WARN] Telegram credentials not configured. "
                  "Set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID env vars "
                  "or fill config.json (template: config.example.json). Alerts disabled.")

    return tg_token, tg_chat_id

def get_ist_now():
    """Returns current datetime in Indian Standard Time (Asia/Kolkata)."""
    return datetime.now(KOLKATA_TZ)

def load_nse_holidays():
    """Loads NSE trading holidays list from versioned config file."""
    data = safe_read_json(HOLIDAYS_CONFIG_FILE, default={})
    holidays = set(data.get("holidays", []))
    comm_evening = set(data.get("commodity_evening_sessions", []))
    return holidays, comm_evening

def is_market_open(segment="EQ", dt=None):
    """Segment-aware Indian market hours validator.
    - EQ (Equity / F&O): 09:00 to 15:35 IST, Monday-Friday (excluding NSE trading holidays).
    - COMM (Commodity MCX): 09:00 to 23:30 IST, Monday-Friday.
      On commodity evening session holidays, evening trading is active 17:00 to 23:30 IST.
    """
    if dt is None:
        dt = get_ist_now()
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=KOLKATA_TZ)
    else:
        dt = dt.astimezone(KOLKATA_TZ)

    # Weekends (Saturday=5, Sunday=6) are always closed
    if dt.weekday() >= 5:
        return False

    holidays, comm_evening = load_nse_holidays()
    date_str = dt.strftime("%Y-%m-%d")
    is_holiday = date_str in holidays
    current_time = dt.time()

    seg = (segment or "EQ").upper().strip()

    if seg == "COMM":
        if is_holiday:
            if date_str in comm_evening:
                # Evening session on designated holidays
                return dt_time(17, 0) <= current_time <= dt_time(23, 30)
            return False
        return dt_time(9, 0) <= current_time <= dt_time(23, 30)

    # Default to Equity (EQ) segment
    if is_holiday:
        return False

    return dt_time(9, 0) <= current_time <= dt_time(15, 35)

def is_post_market_momentum_window(dt=None):
    """Returns True if current IST time is in post-market window (Mon-Fri 16:30 to 18:30 IST ~5:00 PM)."""
    if dt is None:
        dt = get_ist_now()
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=KOLKATA_TZ)
    else:
        dt = dt.astimezone(KOLKATA_TZ)

    if dt.weekday() >= 5:
        return False

    holidays, _ = load_nse_holidays()
    if dt.strftime("%Y-%m-%d") in holidays:
        return False

    return dt_time(16, 30) <= dt.time() <= dt_time(18, 30)

# Backward compatibility alias
def is_market_hours():
    return is_market_open("EQ")

def send_deduplicated_telegram_alert(message, bot_token=None, chat_id=None, force=False, min_interval_seconds=600, segment="EQ", alert_type="AUTO"):
    """Sends Telegram message with strict Anti-Duplicate / Anti-Stale hash filtering and Segment-Aware Gating.
    - EQ alerts: Sent ONLY during equity market hours (Mon-Fri 09:00 - 15:35 IST, non-holiday).
    - COMM alerts: Sent ONLY during commodity market hours (Mon-Fri 09:00 - 23:30 IST).
    - EOD alerts (Daily Momentum Stocks / Market Wrap): Broadcasted at ~5:00 PM IST (16:30 - 18:30 IST) once per trading day.
    - ADMIN alerts / force=True: Bypasses market hours timing checks.
    """
    if not bot_token or not chat_id:
        bot_token, chat_id = get_telegram_credentials(admin=(segment == "ADMIN"))

    if not bot_token or not chat_id:
        print("[WARN] Telegram broadcast skipped: no credentials configured.")
        return False

    if not message or not message.strip():
        return False

    now = get_ist_now()
    today_str = now.strftime("%Y-%m-%d")
    is_eod_momentum = (
        alert_type == "EOD_MOMENTUM" or
        segment == "EOD" or
        "DAILY STOCK MOMENTUM" in message.upper() or
        "MARKET WRAP" in message.upper() or
        "MOMENTUM STOCKS" in message.upper()
    )

    # Segment and Market Hours Timing Gate (bypassed if force=True or ADMIN alert)
    if not force and segment != "ADMIN":
        if is_eod_momentum:
            if not is_post_market_momentum_window(now):
                print(f"[INFO] Daily Momentum List scheduled for post-market closing window (~5:00 PM IST). Current: {now.strftime('%I:%M %p')}. Broadcast deferred.")
                return False
        else:
            target_segment = "COMM" if segment == "COMM" else "EQ"
            if not is_market_open(target_segment, now):
                print(f"[INFO] Market is closed for {target_segment} ({now.strftime('%A %I:%M %p')} IST). Suppressing alert to prevent off-hours spam.")
                return False

    cache_data = safe_read_json(CACHE_FILE, default={})
    now_epoch = time.time()

    # Daily EOD Deduplication: Ensure Momentum List is sent at most ONCE per trading day
    if is_eod_momentum and not force:
        if cache_data.get("last_eod_date") == today_str:
            print(f"[INFO] Daily Momentum Stock List already broadcasted for {today_str}. Suppressing duplicate.")
            return False

    # Create content hash (ignoring exact minute timestamps to compare core signals)
    normalized_msg = "\n".join([line for line in message.splitlines() if "Time:" not in line and "🕒" not in line])
    msg_hash = hashlib.sha256(normalized_msg.encode('utf-8')).hexdigest()

    last_hash = cache_data.get("last_hash")
    last_epoch = cache_data.get("last_epoch", 0)

    # Rolling Interval Deduplication Guard: Check if identical alert was sent recently
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
            # Update cache atomically
            cache_data["last_hash"] = msg_hash
            cache_data["last_epoch"] = now_epoch
            cache_data["last_time"] = now.strftime("%Y-%m-%d %H:%M:%S IST")
            if is_eod_momentum:
                cache_data["last_eod_date"] = today_str

            atomic_write_json(CACHE_FILE, cache_data)
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

def send_admin_pipeline_alert(subject, details=None, is_failure=True):
    """Dispatches operational alert or failure notification to private admin chat.
    Uses segment='ADMIN' and force=True so it never gets blocked by market hour gates.
    """
    bot_token, admin_chat_id = get_telegram_credentials(admin=True)
    if not bot_token or not admin_chat_id:
        return False

    icon = "🚨" if is_failure else "ℹ️"
    now_str = get_ist_now().strftime("%d-%b-%Y %I:%M:%S %p IST")
    msg = f"{icon} *Market Mentor AI System Notice*\n\n"
    msg += f"*Event*: {subject}\n"
    msg += f"*Time*: `{now_str}`\n"
    if details:
        msg += f"\n*Details*:\n```{details[:1000]}```\n"

    return send_deduplicated_telegram_alert(
        message=msg,
        bot_token=bot_token,
        chat_id=admin_chat_id,
        force=True,
        segment="ADMIN",
        min_interval_seconds=60
    )

def send_admin_pipeline_heartbeat(status_summary="ALL_STEPS_HEALTHY"):
    """Sends lightweight heartbeat ping to private admin chat."""
    return send_admin_pipeline_alert(
        subject="Pipeline Heartbeat Online",
        details=f"Status: {status_summary}",
        is_failure=False
    )
