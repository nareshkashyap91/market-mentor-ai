import os
import sys
import json
import time
import requests
from telegram_bot_interactive import TelegramBotInteractive

# Ensure stdout handles UTF-8 on Windows
sys.stdout.reconfigure(encoding='utf-8')

from telegram_config import get_telegram_credentials

def load_telegram_credentials():
    return get_telegram_credentials()

def send_telegram_reply(bot_token, chat_id, text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload, timeout=15)
        return res.status_code == 200
    except Exception as e:
        print(f"[ERROR] Failed to send Telegram reply: {e}")
        return False

def start_telegram_listener():
    bot_token, default_chat_id = load_telegram_credentials()
    if not bot_token:
        print("[ERROR] Telegram Bot Token not found. Listener cannot start.")
        return

    print("==========================================================================")
    print("   MARKET MENTOR AI - 2-WAY INTERACTIVE TELEGRAM LISTENER DAEMON          ")
    print("==========================================================================")
    print(f"[INFO] Connected Bot Token: {bot_token[:10]}... (Active)")
    print("[INFO] Listening for incoming commands: /status, /top5, /fii, /greeks, /help")

    offset = 0
    base_url = f"https://api.telegram.org/bot{bot_token}/getUpdates"

    while True:
        try:
            params = {"offset": offset, "timeout": 20}
            resp = requests.get(base_url, params=params, timeout=25)

            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok") and data.get("result"):
                    for update in data["result"]:
                        update_id = update["update_id"]
                        offset = update_id + 1

                        message = update.get("message") or update.get("channel_post")
                        if not message:
                            continue

                        chat = message.get("chat", {})
                        chat_id = chat.get("id")
                        text = message.get("text", "").strip()

                        if text and text.startswith("/"):
                            print(f"[RECV] Command '{text}' received from Chat ID {chat_id}")
                            # Process command
                            reply_text = TelegramBotInteractive.process_command(text)
                            # Send reply back to user/group
                            send_telegram_reply(bot_token, chat_id, reply_text)
                            print(f"[SENT] Reply sent for command '{text}' to Chat ID {chat_id}")

            time.sleep(1)

        except KeyboardInterrupt:
            print("\n[INFO] Listener stopped by user.")
            break
        except Exception as e:
            print(f"[WARNING] Listener exception: {e}. Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == '__main__':
    start_telegram_listener()
