import unittest
from iv_skew_maxpain_engine import IVSkewMaxPainEngine, get_iv_skew_and_max_pain

class TestIVSkewMaxPainEngine(unittest.TestCase):

    def test_max_pain_calculation(self):
        """Verifies Max Pain Strike Price resolution."""
        res = IVSkewMaxPainEngine.calculate_max_pain()
        self.assertIn("max_pain_strike", res)
        self.assertTrue(res["max_pain_strike"] >= 23800)

    def test_iv_skew_calculation(self):
        """Verifies IV Skew calculation and Gamma Blast Squeeze risk detection."""
        skew = IVSkewMaxPainEngine.calculate_iv_skew(call_iv=12.0, put_iv=16.0)
        self.assertEqual(skew["iv_skew_pct"], 4.0)
        self.assertIn("HIGH PUT SKEW", skew["skew_status"])

    def test_combined_helper(self):
        """Verifies combined IV Skew & Max Pain output."""
        combined = get_iv_skew_and_max_pain()
        self.assertIn("max_pain_strike", combined)
        self.assertIn("iv_skew_pct", combined)

if __name__ == '__main__':
    unittest.main()
