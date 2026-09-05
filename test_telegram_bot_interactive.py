import unittest
from telegram_bot_interactive import TelegramBotInteractive, process_telegram_command

class TestTelegramBotInteractive(unittest.TestCase):

    def test_status_command_with_botname_tag(self):
        """Verifies slash commands with Telegram group @botname tags e.g. /status@Investor_guidebot."""
        res = process_telegram_command("/status@Investor_guidebot")
        self.assertIn("MARKET MENTOR AI", res)
        self.assertIn("LIVE MARKET STATUS", res)

    def test_top5_command_with_botname_tag(self):
        """Verifies /top5@Investor_guidebot command output."""
        res = process_telegram_command("/top5@Investor_guidebot")
        self.assertIn("TOP 5 NEXT-DAY MOMENTUM CANDIDATES", res)
        self.assertIn("Live Close", res)

    def test_morning_command(self):
        """Verifies /morning 9:30 AM live breakout confirmation command output."""
        res = process_telegram_command("/morning")
        self.assertIn("MORNING LIVE BREAKOUT CONFIRMATION", res)
        self.assertIn("Yesterday's Candidates Validation Results", res)

    def test_fii_command(self):
        """Verifies /fii command output."""
        res = process_telegram_command("/fii")
        self.assertIn("INSTITUTIONAL FII / DII MONEY FLOW", res)

    def test_greeks_command(self):
        """Verifies /greeks command output."""
        res = process_telegram_command("/greeks")
        self.assertIn("NIFTY OPTIONS GREEKS", res)

    def test_mcx_command(self):
        """Verifies /mcx late-night commodity options command output."""
        res = process_telegram_command("/mcx")
        self.assertIn("MCX COMMODITY OPTIONS QUANT MATRIX", res)
        self.assertIn("CRUDEOIL Spot", res)
        self.assertIn("Bull Call Spread", res)

    def test_help_command(self):
        """Verifies /help command output."""
        res = process_telegram_command("/help")
        self.assertIn("TELEGRAM COMMANDS GUIDE", res)

if __name__ == '__main__':
    unittest.main()
