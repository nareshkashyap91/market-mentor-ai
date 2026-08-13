import os
import sys
import unittest
import numpy as np

from option_greeks import BlackScholesGreeksEngine, get_greeks, get_iv
from option_chain_analyzer import OptionChainAnalyzer

class TestPhase2OptionGreeksAndChain(unittest.TestCase):

    def test_black_scholes_call_price(self):
        """Verifies Black-Scholes Call pricing against benchmark."""
        # Spot: 24500, Strike: 24500, DTE: 7, IV: 15%
        price = BlackScholesGreeksEngine.calculate_option_price("CE", 24500, 24500, 7, 0.15)
        self.assertTrue(price > 50.0)

    def test_greeks_values(self):
        """Verifies Delta, Gamma, Theta, Vega calculations."""
        greeks = get_greeks("CE", 24500, 24500, 7, 0.15)
        self.assertIn("delta", greeks)
        self.assertIn("gamma", greeks)
        self.assertIn("theta", greeks)
        self.assertIn("vega", greeks)
        self.assertIn("iv", greeks)
        
        # ATM Call Delta should be approximately 0.50
        self.assertTrue(0.45 <= greeks["delta"] <= 0.55)

    def test_iv_solver(self):
        """Verifies Implied Volatility solver convergence."""
        target_iv = 0.18
        market_price = BlackScholesGreeksEngine.calculate_option_price("CE", 24500, 24500, 7, target_iv)
        
        solved_iv = get_iv(market_price, "CE", 24500, 24500, 7)
        self.assertAlmostEqual(target_iv, solved_iv, delta=0.01)

    def test_net_strategy_greeks(self):
        """Verifies multi-leg strategy Net Greeks aggregation."""
        legs = ["BUY NIFTY 24500 CE", "SELL NIFTY 24600 CE (Hedge)"]
        net_greeks = OptionChainAnalyzer.calculate_strategy_net_greeks(legs, 24500, 7, default_iv=0.15)
        
        self.assertIn("net_delta", net_greeks)
        self.assertIn("net_theta", net_greeks)
        self.assertTrue(net_greeks["net_delta"] > 0) # Bull Call Spread has positive Net Delta

if __name__ == '__main__':
    unittest.main()
