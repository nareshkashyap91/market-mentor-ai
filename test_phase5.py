import os
import sys
import unittest

from margin_engine import CapitalMarginEngine, get_strategy_margin

class TestPhase5CapitalMarginEngine(unittest.TestCase):

    def test_lot_size_resolution(self):
        """Verifies official NSE contract lot sizes."""
        self.assertEqual(CapitalMarginEngine.get_lot_size("NIFTY"), 25)
        self.assertEqual(CapitalMarginEngine.get_lot_size("BANKNIFTY"), 15)

    def test_margin_calculations(self):
        """Verifies margin requirement calculations across strategy types."""
        # 1. Nifty Debit Spread (150 width)
        debit_m = get_strategy_margin("NIFTY", "HEDGED SPREAD", ["BUY NIFTY 24400 CE", "SELL NIFTY 24550 CE"], 24500)
        self.assertIn("margin_required_rupees", debit_m)
        self.assertEqual(debit_m["lot_size"], 25)
        self.assertTrue(debit_m["margin_required_rupees"] > 0)

        # 2. Bank Nifty Credit Spread (300 width)
        credit_m = get_strategy_margin("BANKNIFTY", "THETA CREDIT SPREAD", ["SELL BANKNIFTY 51500 PE", "BUY BANKNIFTY 51200 PE"], 51500)
        self.assertEqual(credit_m["lot_size"], 15)
        self.assertTrue(credit_m["margin_required_rupees"] > 0)

        # 3. Iron Butterfly
        bf_m = get_strategy_margin("NIFTY", "HEDGED STRADDLE", ["SELL NIFTY 24500 CE", "SELL NIFTY 24500 PE", "BUY NIFTY 24650 CE", "BUY NIFTY 24350 PE"], 24500)
        self.assertTrue(bf_m["margin_required_rupees"] >= 3000)

if __name__ == '__main__':
    unittest.main()
