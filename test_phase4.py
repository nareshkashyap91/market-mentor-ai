import os
import sys
import unittest

from strategy_scoring import StrategyScoringEngine, evaluate_strategies

class TestPhase4StrategyScoringAndNoTrade(unittest.TestCase):

    def test_no_trade_triggers(self):
        """Verifies NO TRADE guardrail triggers."""
        # Low Confidence (<35%) -> NO TRADE
        eval_low_conf = StrategyScoringEngine.evaluate_no_trade_conditions(regime_confidence=30.0, vix_val=14.0)
        self.assertTrue(eval_low_conf["is_no_trade"])
        self.assertIn("LOW REGIME CONFIDENCE", eval_low_conf["summary"])

        # High VIX (>25.0) -> NO TRADE
        eval_high_vix = StrategyScoringEngine.evaluate_no_trade_conditions(regime_confidence=60.0, vix_val=28.0)
        self.assertTrue(eval_high_vix["is_no_trade"])
        self.assertIn("EXTREME VOLATILITY", eval_high_vix["summary"])

        # Optimal Conditions -> ACTIVE
        eval_optimal = StrategyScoringEngine.evaluate_no_trade_conditions(regime_confidence=75.0, vix_val=13.5)
        self.assertFalse(eval_optimal["is_no_trade"])

    def test_strategy_enrichment_and_separation(self):
        """Verifies Historical Win Rate vs AI Confidence separation."""
        dummy_strat = {
            "name": "NIFTY Bull Call Debit Spread",
            "win_prob": "78%",
            "entry_spot": 24500.0,
            "sl_spot": 24400.0,
            "target1_spot": 24650.0
        }

        enriched = StrategyScoringEngine.score_and_enrich_strategy(dummy_strat, regime_confidence=65.0, vix_val=13.5)

        self.assertEqual(enriched["historical_win_probability"], "78%")
        self.assertEqual(enriched["ai_confidence_score"], "65%")
        self.assertIn("risk_reward_ratio", enriched)
        self.assertIn("composite_score", enriched)
        
        # Risk-Reward: (24650 - 24500) / (24500 - 24400) = 150 / 100 = 1.5
        self.assertEqual(enriched["risk_reward_ratio"], "1:1.5")

if __name__ == '__main__':
    unittest.main()
