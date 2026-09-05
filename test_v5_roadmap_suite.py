import os
import json
import unittest
from ml_target_sl_optimizer import MLTargetSLOptimizer
from portfolio_rebalancer import PortfolioRebalancerEngine

class TestV5RoadmapSuite(unittest.TestCase):
    """Test suite for V5.0 Roadmap Engine Upgrades (ML Target/SL Optimizer & Portfolio Risk-Parity Rebalancer)."""

    def test_01_ml_target_sl_optimizer_levels(self):
        res = MLTargetSLOptimizer.optimize_stock_levels("NIFTY50", current_price=24500.0, atr_val=180.0, direction="LONG", confidence_score=82.0)
        self.assertEqual(res["symbol"], "NIFTY50")
        self.assertLess(res["optimized_sl"], 24500.0)
        self.assertGreater(res["target_1"], 24500.0)
        self.assertGreater(res["target_2"], res["target_1"])
        self.assertIn("1:", res["risk_reward_ratio"])
        self.assertTrue(50.0 <= res["ml_win_probability_pct"] <= 95.0)

        payload = MLTargetSLOptimizer.export_ml_optimizer_json()
        self.assertIn("candidates", payload)
        self.assertGreaterEqual(len(payload["candidates"]), 1)
        self.assertTrue(os.path.exists(os.path.join("data", "ml_target_sl_optimized.json")))

    def test_02_portfolio_rebalancer_risk_parity(self):
        analysis = PortfolioRebalancerEngine.analyze_portfolio()
        self.assertIn("total_portfolio_value", analysis)
        self.assertIn("category_analysis", analysis)
        self.assertGreater(analysis["total_portfolio_value"], 0.0)
        self.assertGreater(analysis["sharpe_ratio"], 0.0)

        categories = [item["category"] for item in analysis["category_analysis"]]
        self.assertIn("EQUITY_STOCKS", categories)
        self.assertIn("MUTUAL_FUNDS", categories)
        self.assertIn("COMMODITY_GOLD", categories)

        payload = PortfolioRebalancerEngine.export_portfolio_json()
        self.assertIn("portfolio_summary", payload)
        self.assertTrue(os.path.exists(os.path.join("data", "portfolio_rebalancing.json")))

if __name__ == "__main__":
    unittest.main()
