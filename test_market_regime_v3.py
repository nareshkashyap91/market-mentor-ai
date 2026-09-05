import unittest
from market_regime_v3 import MarketRegimeV3Engine, get_regime_v3

class TestMarketRegimeV3Engine(unittest.TestCase):

    def test_trending_bullish_regime(self):
        """Verifies TRENDING_BULLISH regime detection."""
        res = get_regime_v3(nifty_spot=24580.25, vwap=24550.0, ema20=24500.0, ema50=24400.0, ema200=24000.0, adx=28.4, vix_val=13.20)
        self.assertEqual(res["regime"], "TRENDING_BULLISH")
        self.assertTrue(res["regime_confidence"] >= 80.0)
        self.assertIn("15m structure bullish", res["regime_reason"])

    def test_event_risk_regime(self):
        """Verifies EVENT_RISK regime detection."""
        res = MarketRegimeV3Engine.detect_regime(is_event_day=True)
        self.assertEqual(res["regime"], "EVENT_RISK")
        self.assertFalse(res["is_trade_allowed"])

    def test_unsafe_regime(self):
        """Verifies UNSAFE regime detection when VIX >= 25.0."""
        res = get_regime_v3(vix_val=26.5)
        self.assertEqual(res["regime"], "UNSAFE")
        self.assertFalse(res["is_trade_allowed"])

if __name__ == '__main__':
    unittest.main()
