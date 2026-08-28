import unittest
from greeks_hedging_engine import GreeksHedgingEngine, get_greeks_and_hedging

class TestGreeksHedgingEngine(unittest.TestCase):

    def test_portfolio_greeks_calculation(self):
        """Verifies Portfolio Delta, Theta decay per hour, and P&L sensitivity calculation."""
        g = get_greeks_and_hedging()
        self.assertIn("net_delta", g)
        self.assertIn("theta_decay_per_hour_inr", g)
        self.assertTrue(g["theta_decay_per_hour_inr"] > 0)
        self.assertTrue(g["pnl_per_100pt_nifty_move"] > 0)

    def test_delta_hedge_recommendation(self):
        """Verifies Delta Neutral Hedge recommendation."""
        safe = GreeksHedgingEngine.recommend_delta_hedge(net_delta=0.50)
        self.assertTrue(safe["is_delta_safe"])

        overexposed = GreeksHedgingEngine.recommend_delta_hedge(net_delta=0.85)
        self.assertFalse(overexposed["is_delta_safe"])
        self.assertIn("BUY 1 LOT", overexposed["recommended_hedge_action"])

if __name__ == '__main__':
    unittest.main()
