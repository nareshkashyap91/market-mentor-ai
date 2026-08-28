import unittest
from premarket_ai_engine import PreMarketAIEngine, get_premarket_cues

class TestPreMarketAIEngine(unittest.TestCase):

    def test_premarket_cues(self):
        """Verifies Pre-Market Global Cues & Gap Expectation analysis."""
        cues = get_premarket_cues()
        self.assertIn("gift_nifty_pts", cues)
        self.assertIn("gap_expectation", cues)
        self.assertIn("GAP UP", cues["gap_expectation"])
        self.assertTrue(cues["prediction_confidence"] >= 70.0)

if __name__ == '__main__':
    unittest.main()
