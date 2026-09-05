import unittest
import os
from trade_decision_pipeline import TradeDecisionPipeline, run_trade_decision_pipeline

class TestTradeDecisionPipeline(unittest.TestCase):

    def test_complete_5_stage_pipeline(self):
        """Verifies execution of TradeDecision ➔ AI Radar ➔ Trade Card ➔ Chart ➔ Telegram pipeline."""
        gate_res = {
            "symbol": "BHEL",
            "direction": "LONG",
            "strategy": "ORB + VWAP RETEST",
            "trade_score": 91.0,
            "grade": "A+",
            "is_gate_passed": True,
            "decision": "TRADE_LONG",
            "confirmations": ["15m Trend", "VWAP", "RVOL", "Sector Strength"]
        }
        explanation_res = {
            "why_this_stock": "Strong RS leadership",
            "fomo_risk": "LOW"
        }

        res = run_trade_decision_pipeline("BHEL", "LONG", "ORB + VWAP RETEST", gate_res, explanation_res)
        
        self.assertEqual(res["stage_1_decision"], "TRADE_LONG")
        self.assertEqual(res["stage_2_radar"], "ORB_RADAR")
        self.assertEqual(res["stage_3_trade_card"]["symbol"], "BHEL")
        self.assertTrue(os.path.exists(res["stage_4_chart_path"]))
        self.assertTrue(res["is_trade_allowed"])

if __name__ == '__main__':
    unittest.main()
