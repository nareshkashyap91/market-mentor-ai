import unittest
from trade_journal_ui import TradeJournalUI, get_journal_ui_analytics

class TestTradeJournalUI(unittest.TestCase):

    def test_equity_curve_generation(self):
        """Verifies Equity Growth Curve data generation."""
        eq = TradeJournalUI.generate_equity_curve_data()
        self.assertIn("current_balance", eq)
        self.assertTrue(eq["current_balance"] > 100000.0)
        self.assertTrue(eq["total_growth_pct"] > 0)
        self.assertEqual(len(eq["equity_points"]), 9)

    def test_journal_analytics_summary(self):
        """Verifies Trade Journal analytics summary."""
        res = get_journal_ui_analytics()
        self.assertIn("equity_curve", res)
        self.assertIn("performance_stats", res)

if __name__ == '__main__':
    unittest.main()
