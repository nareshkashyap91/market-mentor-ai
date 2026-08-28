import unittest
import os
from telegram_audio_engine import TelegramAudioEngine, broadcast_audio_briefing

class TestTelegramAudioEngine(unittest.TestCase):

    def test_audio_script_generation(self):
        """Verifies spoken audio briefing script generation."""
        script = TelegramAudioEngine.generate_audio_script(nifty_spot=24580.25, top_stocks=["BHEL", "SBIN"])
        self.assertIn("Market Mentor AI", script)
        self.assertIn("BHEL", script)

    def test_audio_file_creation(self):
        """Verifies MP3 audio file generation."""
        res, path = TelegramAudioEngine.create_audio_file("Test audio script for Market Mentor AI.")
        self.assertTrue(res)
        self.assertTrue(os.path.exists(path))

    def test_broadcast_helper_on_hold(self):
        """Verifies that audio broadcasting is cleanly held when disabled."""
        info = broadcast_audio_briefing()
        self.assertEqual(info["status"], "HOLD")
        self.assertEqual(info["reason"], "AUDIO_DISABLED_BY_USER")

if __name__ == '__main__':
    unittest.main()
