import unittest
from intraday_orb_vwap_precision import IntradayOrbVwapPrecisionEngine, evaluate_intraday_precision

class TestIntradayOrbVwapPrecisionEngine(unittest.TestCase):

    def test_confirmed_orb_long_breakout(self):
        """Verifies Confirmed ORB Long Breakout with VWAP support."""
        res = evaluate_intraday_precision(close=24550.0, vwap=24500.0, atr=80.0, orb_high=24520.0, orb_low=24450.0)
        self.assertEqual(res["orb_status"], "CONFIRMED ORB LONG BREAKOUT (VWAP SUPPORTED)")
        self.assertTrue(res["is_trade_allowed"])
        self.assertEqual(res["intraday_bias"], "BULLISH")

    def test_chase_risk_overextension_filter(self):
        """Verifies Chase Risk rejection when overextended > 2.5x ATR above VWAP."""
        res = evaluate_intraday_precision(close=24800.0, vwap=24500.0, atr=80.0, orb_high=24520.0, orb_low=24450.0)
        self.assertEqual(res["orb_status"], "CHASE RISK (EXTENDED > 2.5x ATR ABOVE VWAP)")
        self.assertFalse(res["is_trade_allowed"])

if __name__ == '__main__':
    unittest.main()
