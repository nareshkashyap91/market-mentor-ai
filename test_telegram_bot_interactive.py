import unittest
from telegram_bot_interactive import TelegramBotInteractive, process_telegram_command

class TestTelegramBotInteractive(unittest.TestCase):

    def test_status_command(self):
        """Verifies /status command output."""
        res = process_telegram_command("/status")
        self.assertIn("MARKET MENTOR AI", res)
        self.assertIn("BULLISH", res)

    def test_top5_command(self):
        """Verifies /top5 command output."""
        res = process_telegram_command("/top5")
        self.assertIn("TOP 5 NEXT-DAY MOMENTUM STOCKS", res)
        self.assertIn("BHEL", res)

    def test_fii_command(self):
        """Verifies /fii command output."""
        res = process_telegram_command("/fii")
        self.assertIn("INSTITUTIONAL FII / DII MONEY FLOW", res)
        self.assertIn("FII Cash Net", res)

    def test_greeks_command(self):
        """Verifies /greeks command output."""
        res = process_telegram_command("/greeks")
        self.assertIn("NIFTY OPTIONS GREEKS", res)
        self.assertIn("Max Pain Strike", res)

    def test_help_command(self):
        """Verifies /help command output."""
        res = process_telegram_command("/help")
        self.assertIn("TELEGRAM COMMANDS GUIDE", res)

if __name__ == '__main__':
    unittest.main()
