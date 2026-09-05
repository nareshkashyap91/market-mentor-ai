import unittest
from telegram_bot_v3 import TelegramBotV3Engine, format_trade_alert_v3

class TestTelegramBotV3Engine(unittest.TestCase):

    def test_format_pro_trade_alert(self):
        """Verifies V3 Professional Telegram A+ Trade Alert formatting."""
        gate_res = {
            "symbol": "BHEL",
            "direction": "LONG",
            "strategy": "ORB + VWAP RETEST",
            "trade_score": 91.0,
            "grade": "A+",
            "confirmations": ["15m trend", "VWAP", "ORB breakout", "RVOL"]
        }
        explanation_res = {"fomo_risk": "LOW"}

        alert = format_trade_alert_v3(gate_res, explanation_res)
        self.assertIn("MARKET MENTOR AI", alert)
        self.assertIn("A+ INTRADAY SETUP", alert)
        self.assertIn("TRADE LONG", alert)
        self.assertNotIn("100% accuracy", alert) # Verifies no certainty claims

    def test_format_why_not_trade_alert(self):
        """Verifies V3 Mandatory WHY NOT TRADE Alert formatting."""
        reasons = ["Price extended 2.8 ATR from VWAP", "RR only 1:1.1", "Volume weak"]
        alert = TelegramBotV3Engine.format_why_not_trade_alert("HAL", reasons)
        self.assertIn("NO TRADE ALERT", alert)
        self.assertIn("Price extended 2.8 ATR", alert)
        self.assertIn("NO TRADE", alert)

if __name__ == '__main__':
    unittest.main()
