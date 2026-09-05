import unittest
from options_engine_v3 import OptionsEngineV3, get_options_v3

class TestOptionsEngineV3(unittest.TestCase):

    def test_delta_strike_selection(self):
        """Verifies Delta-based strike selection and MODEL_ESTIMATED_POP calculation."""
        res = get_options_v3(spot=24580.25, delta_band="MODERATE", regime="TRENDING_BULLISH")
        self.assertEqual(res["delta_band"], "MODERATE")
        self.assertIn("model_estimated_pop", res)
        self.assertTrue(res["buy_strike"] > 0)
        self.assertEqual(res["strategy_type"], "Bull Call Spread")

    def test_conservative_delta_band(self):
        """Verifies CONSERVATIVE delta band strike selection."""
        res = get_options_v3(spot=24580.25, delta_band="CONSERVATIVE", regime="TRENDING_BULLISH")
        self.assertEqual(res["delta_band"], "CONSERVATIVE")

if __name__ == '__main__':
    unittest.main()
