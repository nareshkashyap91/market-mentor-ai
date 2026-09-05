import unittest
from intraday_precision_v3 import IntradayPrecisionV3Engine, evaluate_intraday_v3_helper

class TestIntradayPrecisionV3Engine(unittest.TestCase):

    def test_genuine_breakout_quality(self):
        """Verifies GENUINE breakout classification."""
        res = IntradayPrecisionV3Engine.evaluate_intraday_v3(close=24550.0, open_p=24500.0, high=24560.0, low=24490.0, vwap=24520.0, atr=80.0, rvol=2.0)
        self.assertEqual(res["breakout_quality"], "GENUINE")
        self.assertTrue(res["is_valid_trade"])
        self.assertIn("BOS_BULLISH", res["market_structure"])

    def test_extended_breakout_quality(self):
        """Verifies EXTENDED breakout classification when extended > 2.5x ATR from VWAP."""
        res = IntradayPrecisionV3Engine.evaluate_intraday_v3(close=24800.0, open_p=24700.0, high=24810.0, low=24690.0, vwap=24520.0, atr=80.0)
        self.assertEqual(res["breakout_quality"], "EXTENDED")
        self.assertFalse(res["is_valid_trade"])

if __name__ == '__main__':
    unittest.main()
