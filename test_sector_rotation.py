import unittest
from sector_rotation_engine import SectorRotationEngine, get_sector_rotation

class TestSectorRotationEngine(unittest.TestCase):

    def test_sector_rotation_analysis(self):
        """Verifies sector rotation ranking and leading/lagging classification."""
        sec = get_sector_rotation()
        self.assertIn("top_leading_sector", sec)
        self.assertIn("leading_sectors", sec)
        self.assertTrue(len(sec["leading_sectors"]) > 0)
        self.assertIn("NIFTY IT", sec["leading_sectors"])

    def test_stock_sector_bias(self):
        """Verifies score boost calculation for stocks in leading sectors."""
        bias_leading = SectorRotationEngine.get_stock_sector_bias("NIFTY IT")
        self.assertEqual(bias_leading["status"], "LEADING")
        self.assertEqual(bias_leading["score_boost"], 10)

        bias_lagging = SectorRotationEngine.get_stock_sector_bias("NIFTY FMCG")
        self.assertEqual(bias_lagging["status"], "LAGGING")
        self.assertEqual(bias_lagging["score_boost"], -10)

if __name__ == '__main__':
    unittest.main()
