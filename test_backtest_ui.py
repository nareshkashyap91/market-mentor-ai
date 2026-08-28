import unittest
from backtest_ui_engine import BacktestUIEngine, get_1click_backtest

class TestBacktestUIEngine(unittest.TestCase):

    def test_1click_backtest_simulation(self):
        """Verifies 1-Click Backtest Analytics output."""
        bt = get_1click_backtest()
        self.assertIn("win_rate_pct", bt)
        self.assertIn("net_profit_inr", bt)
        self.assertTrue(bt["win_rate_pct"] > 70.0)
        self.assertTrue(bt["net_profit_inr"] > 0)
        self.assertTrue(bt["profit_factor"] > 2.0)
        self.assertTrue(bt["sharpe_ratio"] > 2.0)

if __name__ == '__main__':
    unittest.main()
