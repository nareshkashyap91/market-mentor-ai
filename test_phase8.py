import os
import sys
import unittest
import numpy as np

from backtest_engine import BacktestEngine, get_backtest_metrics

class TestPhase8BacktestEngine(unittest.TestCase):

    def test_backtest_metrics_calculation(self):
        """Verifies Sharpe Ratio, Max Drawdown %, CAGR %, Profit Factor calculations."""
        np.random.seed(42)
        returns = np.random.normal(loc=0.0015, scale=0.007, size=252)

        metrics = BacktestEngine.calculate_metrics(returns)

        self.assertIn("cagr_pct", metrics)
        self.assertIn("sharpe_ratio", metrics)
        self.assertIn("max_drawdown_pct", metrics)
        self.assertIn("profit_factor", metrics)
        self.assertIn("win_rate_pct", metrics)

        # Max Drawdown should be negative or zero
        self.assertTrue(metrics["max_drawdown_pct"] <= 0.0)

        # Sharpe ratio should be positive for positive mean returns
        self.assertTrue(metrics["sharpe_ratio"] > 0)

    def test_strategy_backtest_execution(self):
        """Verifies full backtest execution and Walk Forward status."""
        bt = get_backtest_metrics("Bull Call Debit Spread")

        self.assertEqual(bt["strategy_name"], "Bull Call Debit Spread")
        self.assertIn("PASSED", bt["walk_forward_status"])
        self.assertEqual(bt["total_backtest_trades"], 252)

if __name__ == '__main__':
    unittest.main()
