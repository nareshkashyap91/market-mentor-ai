import unittest
from ai_explanation_engine import AIExplanationEngine, get_ai_explanation

class TestAIExplanationEngine(unittest.TestCase):

    def test_generate_trade_explanation(self):
        """Verifies generation of 7 mandatory AI trade explanation questions including 'what_would_make_ai_change_mind'."""
        res = get_ai_explanation("BHEL", "LONG", "ORB + VWAP RETEST", 91.0)
        self.assertEqual(res["fomo_risk"], "LOW")
        self.assertIn("what_would_make_ai_change_mind", res)
        self.assertIn("VIX > 22", res["what_would_make_ai_change_mind"])
        self.assertIn("why_this_stock", res)

    def test_fomo_risk_high(self):
        """Verifies HIGH FOMO Risk evaluation when price is extended."""
        res = AIExplanationEngine.generate_trade_explanation("BHEL", "LONG", "ORB", 80.0, dist_vwap_atr=2.6, rr_ratio=1.2)
        self.assertEqual(res["fomo_risk"], "HIGH")

if __name__ == '__main__':
    unittest.main()
