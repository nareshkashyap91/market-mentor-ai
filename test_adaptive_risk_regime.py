import unittest
from adaptive_risk_regime import AdaptiveRiskRegimeEngine, get_adaptive_risk

class TestAdaptiveRiskRegimeEngine(unittest.TestCase):

    def test_standard_risk_allocation(self):
        """Verifies Standard 1.0% Risk allocation."""
        res = get_adaptive_risk(regime="🟢 BULLISH_TRENDING", confidence_score=75.0, vix_val=14.0)
        self.assertEqual(res["adaptive_risk_pct"], 1.0)
        self.assertIn("STANDARD", res["risk_mode"])

    def test_aggressive_trend_allocation(self):
        """Verifies Aggressive 1.5% Risk allocation in high-confidence trending market."""
        res = get_adaptive_risk(regime="🟢 BULLISH_TRENDING", confidence_score=85.0, vix_val=13.0)
        self.assertEqual(res["adaptive_risk_pct"], 1.5)
        self.assertIn("AGGRESSIVE", res["risk_mode"])

    def test_capital_preservation_allocation(self):
        """Verifies Capital Preservation 0.5% Risk allocation during high VIX."""
        res = get_adaptive_risk(regime="🔴 SIDEWAYS_CHOPPY", confidence_score=45.0, vix_val=24.0)
        self.assertEqual(res["adaptive_risk_pct"], 0.5)
        self.assertIn("CAPITAL PRESERVATION", res["risk_mode"])

if __name__ == '__main__':
    unittest.main()
