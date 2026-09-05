import unittest
from relative_strength_engine import RelativeStrengthEngine, get_relative_strength

class TestRelativeStrengthEngine(unittest.TestCase):

    def test_strong_outperformer(self):
        """Verifies Strong Outperformer classification when stock outperforms Nifty 50."""
        res = get_relative_strength(stock_change_pct=3.5, nifty_change_pct=0.5)
        self.assertEqual(res["outperformance_status"], "STRONG OUTPERFORMER (RS > +1.0%)")
        self.assertTrue(res["is_outperforming"])
        self.assertEqual(res["relative_strength_score"], 3.0)

    def test_underperformer(self):
        """Verifies Underperformer classification when stock lags Nifty 50."""
        res = get_relative_strength(stock_change_pct=-1.2, nifty_change_pct=0.5)
        self.assertEqual(res["outperformance_status"], "UNDERPERFORMER (RS < 0.0%)")
        self.assertFalse(res["is_outperforming"])

if __name__ == '__main__':
    unittest.main()
