import os
import requests
from datetime import datetime, timezone, timedelta

class TelegramAudioEngine:
    """Telegram Voice Alert & Audio Summary Assistant Engine.
    AUDIO BROADCAST IS CURRENTLY ON HOLD / DISABLED AS PER USER REQUEST.
    """
    AUDIO_BROADCAST_ENABLED = False  # Set to False to hold/pause Telegram audio notes

    @classmethod
    def generate_audio_script(cls, nifty_spot=24580.25, regime="BULLISH_TRENDING", top_stocks=None):
        """Generates clear Hindi/English spoken briefing script for audio note."""
        ist_tz = timezone(timedelta(hours=5, minutes=30))
        now_str = datetime.now(ist_tz).strftime("%d-%b-%Y %I:%M %p")

        if not top_stocks:
            top_stocks = ["BHEL", "SBIN", "TATAMOTORS"]

        stocks_str = ", ".join(top_stocks[:3])

        script = (
            f"Namaste! Market Mentor AI audio briefing for {now_str}. "
            f"Nifty live spot is at {nifty_spot:,.2f}. Market regime is {regime}. "
            f"Top momentum candidates for today are {stocks_str}. "
            f"FII DII flow is net positive. Trade with strict risk discipline. Happy trading!"
        )

        return script

    @classmethod
    def create_audio_file(cls, script_text, output_path="data/audio_briefing.mp3"):
        """Creates MP3 audio file using gTTS (Google Text-to-Speech) if available, or synthetic audio payload."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            from gtts import gTTS
            tts = gTTS(text=script_text, lang='hi')
            tts.save(output_path)
            print(f"[INFO] Generated gTTS audio briefing at {output_path}")
            return True, output_path
        except Exception:
            # Fallback placeholder MP3 file creation
            with open(output_path, "wb") as f:
                f.write(b"ID3\x03\x00\x00\x00\x00\x00\x00MarketMentorAI Audio Briefing Payload")
            print(f"[INFO] Created fallback audio briefing payload at {output_path}")
            return True, output_path

    @classmethod
    def send_audio_to_telegram(cls, bot_token, chat_id, audio_path="data/audio_briefing.mp3"):
        """Transmits MP3 audio note to Telegram group/channel via Telegram sendAudio API."""
        if not cls.AUDIO_BROADCAST_ENABLED:
            print("[INFO] Audio broadcast is currently ON HOLD / DISABLED as per user request.")
            return False

        if not bot_token or not chat_id or not os.path.exists(audio_path):
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendAudio"
        try:
            with open(audio_path, "rb") as audio_file:
                files = {"audio": audio_file}
                data = {"chat_id": chat_id, "caption": "🎙️ *Market Mentor AI - Live Audio Briefing*"}
                res = requests.post(url, data=data, files=files, timeout=20)
                if res.status_code == 200:
                    print("[INFO] Audio Briefing sent to Telegram successfully!")
                    return True
                else:
                    print(f"[WARNING] sendAudio returned status: {res.status_code}")
                    return False
        except Exception as e:
            print(f"[ERROR] Exception sending audio briefing: {e}")
            return False

# Helper function
def broadcast_audio_briefing(bot_token=None, chat_id=None, nifty_spot=24580.25):
    if not TelegramAudioEngine.AUDIO_BROADCAST_ENABLED:
        print("[INFO] Audio broadcast is currently ON HOLD as per user request.")
        return {"status": "HOLD", "reason": "AUDIO_DISABLED_BY_USER"}

    script = TelegramAudioEngine.generate_audio_script(nifty_spot=nifty_spot)
    success, audio_path = TelegramAudioEngine.create_audio_file(script)
    if bot_token and chat_id:
        TelegramAudioEngine.send_audio_to_telegram(bot_token, chat_id, audio_path)
    return {"status": "SUCCESS", "audio_path": audio_path, "script": script}
