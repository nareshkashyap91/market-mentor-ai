import unittest
from smart_breakout_precision import SmartBreakoutPrecisionEngine, get_breakout_precision

class TestSmartBreakoutPrecisionEngine(unittest.TestCase):

    def test_smart_money_confirmed_breakout(self):
        """Verifies Smart Money Confirmed Breakout classification (High Volume + Strong Body + Tight Consolidation)."""
        res = get_breakout_precision(close=423.0, open_p=415.0, high=425.0, low=414.0, breakout_level=418.0, rvol=2.1)
        self.assertEqual(res["breakout_classification"], "SMART MONEY CONFIRMED BREAKOUT")
        self.assertTrue(res["is_valid_breakout"])
        self.assertTrue(res["quality_score"] >= 90)

    def test_false_breakout_trap_detection(self):
        """Verifies False Breakout Trap detection on weak volume."""
        res = get_breakout_precision(close=420.0, open_p=418.0, high=425.0, low=412.0, breakout_level=418.0, rvol=0.7)
        self.assertEqual(res["breakout_classification"], "FALSE BREAKOUT TRAP (RETAIL BAIT)")
        self.assertFalse(res["is_valid_breakout"])

if __name__ == '__main__':
    unittest.main()
