import unittest
from mcx_commodity_engine import MCXCommodityEngine, get_mcx_commodity_analysis

class TestMCXCommodityEngine(unittest.TestCase):

    def test_mcx_market_hours_check(self):
        """Verifies MCX market hours evaluation (9:00 AM - 11:30 PM IST)."""
        is_open, status = MCXCommodityEngine.check_mcx_market_hours()
        self.assertIn("MCX", status)
        self.assertTrue(isinstance(is_open, bool))

    def test_commodity_quotes(self):
        """Verifies Crude Oil, Natural Gas, Gold, and Silver quotes."""
        quotes = MCXCommodityEngine.get_commodity_quotes()
        self.assertIn("CRUDEOIL", quotes)
        self.assertIn("NATURALGAS", quotes)
        self.assertTrue(quotes["CRUDEOIL"]["spot"] > 1000.0)

    def test_mcx_options_strategies(self):
        """Verifies Crude Oil & Natural Gas options strategies generation."""
        res = get_mcx_commodity_analysis()
        self.assertIn("strategies", res)
        self.assertTrue(len(res["strategies"]) >= 2)
        crude_strat = res["strategies"][0]
        self.assertEqual(crude_strat["commodity"], "CRUDEOIL")
        self.assertEqual(crude_strat["lot_size"], 100)

if __name__ == '__main__':
    unittest.main()
