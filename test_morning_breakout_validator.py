import unittest
from morning_breakout_validator import MorningBreakoutValidatorEngine, run_morning_live_breakout_validation

class TestMorningBreakoutValidatorEngine(unittest.TestCase):

    def test_validate_morning_candidates(self):
        """Verifies morning validation separates confirmed buys and rejected gap-ups."""
        res = MorningBreakoutValidatorEngine.validate_morning_candidates()
        self.assertIn("confirmed_buys", res)
        self.assertIn("rejected_stocks", res)
        self.assertTrue(len(res["confirmed_buys"]) >= 1)
        self.assertTrue(len(res["rejected_stocks"]) >= 1)
        
        # Verify HAL was rejected due to gap up > 3.0%
        rejected_syms = [r["symbol"] for r in res["rejected_stocks"]]
        self.assertIn("HAL", rejected_syms)

    def test_format_telegram_morning_alert(self):
        """Verifies Telegram morning alert Markdown formatting."""
        res = MorningBreakoutValidatorEngine.validate_morning_candidates()
        alert = MorningBreakoutValidatorEngine.format_telegram_morning_alert(res)
        self.assertIn("MORNING LIVE BREAKOUT CONFIRMATION", alert)
        self.assertIn("CONFIRMED HIGH-PROBABILITY BUYS", alert)
        self.assertIn("REJECTED / CANCELLED STOCKS", alert)

    def test_run_morning_helper(self):
        """Verifies helper function execution."""
        res = run_morning_live_breakout_validation()
        self.assertIn("confirmed_buys", res)

if __name__ == '__main__':
    unittest.main()
