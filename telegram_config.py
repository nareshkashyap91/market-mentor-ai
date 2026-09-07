import os
import json

DEFAULT_BOT_TOKEN = "8702571549:AAGRucsXGDKGHmZZ9JtgRTvttRFKq8fVHAU"
DEFAULT_CHAT_ID = "-1004347306692"

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
