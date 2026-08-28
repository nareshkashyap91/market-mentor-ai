import unittest
from momentum_intelligence_engine import (
    PriceActionEngine,
    BreakoutQualityEngine,
    PullbackExtensionFilter,
    NextDayGapScenarioEngine
)

class TestNextDayMomentumPhase2(unittest.TestCase):

    def test_price_action_engine(self):
        """Verifies Price Action pattern detection and 52W high proximity."""
        res = PriceActionEngine.analyze_price_action(
            close=420.0, high=425.0, low=412.0, high_52w=420.0, low_52w=220.0, vwap=415.0
        )
        self.assertEqual(res["proximity_status"], "52W BREAKOUT")
        self.assertIn("52-Week High Breakout", res["pattern_name"])
        self.assertEqual(res["price_action_score"], 15)

    def test_breakout_quality_engine(self):
        """Verifies Breakout Quality Engine classification."""
        res = BreakoutQualityEngine.evaluate_breakout(rvol=2.2, close=424.0, high=425.0, low=412.0, atr=10.0, rs_score=85.0)
        self.assertEqual(res["breakout_quality"], "A+ BREAKOUT")
        self.assertEqual(res["breakout_score"], 15)
        self.assertTrue(res["atr_expansion"])

    def test_pullback_extension_filter(self):
        """Verifies extension detection and penalty calculation."""
        # Normal stock
        normal = PullbackExtensionFilter.evaluate_extension(close=420.0, ema20=415.0, vwap=416.0, atr=10.0)
        self.assertEqual(normal["extension_status"], "NORMAL")
        self.assertEqual(normal["penalty"], 0)

        # Highly extended stock
        extended = PullbackExtensionFilter.evaluate_extension(close=460.0, ema20=410.0, vwap=415.0, atr=10.0)
        self.assertEqual(extended["extension_status"], "HIGHLY EXTENDED")
        self.assertTrue(extended["penalty"] > 0)

    def test_nextday_gap_scenarios(self):
        """Verifies Next-Day Gap Up, Flat Open, and Gap Down scenario generation."""
        scenarios = NextDayGapScenarioEngine.generate_scenarios(close=420.0, breakout_level=415.0, atr=10.0, extension_status="NORMAL")
        self.assertIn("CHASE TRADE - AVOID", scenarios["scenario_gap_up"])
        self.assertIn("FLAT OPEN", scenarios["scenario_flat"])
        self.assertIn("SETUP INVALIDATED", scenarios["scenario_gap_down"])
        self.assertTrue(scenarios["chase_avoid_level"] > 420.0)

if __name__ == '__main__':
    unittest.main()
