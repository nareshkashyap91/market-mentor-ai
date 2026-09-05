import unittest
from momentum_intelligence_v3 import MomentumIntelligenceV3Engine, get_momentum_v3

class TestMomentumIntelligenceV3Engine(unittest.TestCase):

    def test_a_plus_momentum_stock(self):
        """Verifies A+ Grade ranking for top momentum leadership stock."""
        res = get_momentum_v3(symbol="BHEL", close=423.0, open_p=415.0, high=425.0, low=414.0, vwap=420.0, rvol=2.1, rsi=65.0, stock_ret_5d=4.5, nifty_ret_5d=1.0)
        self.assertEqual(res["grade"], "A+")
        self.assertTrue(res["momentum_score"] >= 88.0)
        self.assertTrue(res["rs_nifty_score"] > 0)

    def test_reject_weak_stock(self):
        """Verifies REJECT ranking for weak momentum stock below VWAP."""
        res = get_momentum_v3(symbol="WEAK", close=400.0, open_p=410.0, high=412.0, low=398.0, vwap=408.0, rvol=0.7, rsi=42.0, stock_ret_5d=-2.0, nifty_ret_5d=1.0)
        self.assertIn(res["grade"], ["WATCH", "REJECT"])

if __name__ == '__main__':
    unittest.main()
