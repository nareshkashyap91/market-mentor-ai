import os
import sys
import unittest

from model_versioning import ModelVersioningEngine, get_model_metadata
from research_ai import ResearchAIEngine, get_research_synthesis

class TestPhase9ModelVersioningAndResearchAI(unittest.TestCase):

    def test_model_versioning_metadata(self):
        """Verifies Model Versioning metadata."""
        meta = get_model_metadata()
        self.assertEqual(meta["model_version"], "v1.2.0-QUANT-PROD")
        self.assertEqual(len(meta["active_modules"]), 11)
        self.assertIn("Phase 1", meta["active_modules"][0])

    def test_research_ai_synthesis(self):
        """Verifies Research AI narrative synthesis."""
        dummy_nifty = {
            "regime": "🟡 SIDEWAYS_RANGEBOUND",
            "adx": 17.0,
            "confidence_score": 60.0,
            "expected_move": {"summary_str": "±350 pts (₹24000 - ₹24700)"}
        }
        dummy_strat = {
            "name": "NIFTY Bull Put Credit Spread",
            "historical_win_probability": "82%"
        }

        synth = get_research_synthesis(dummy_nifty, dummy_strat)

        self.assertIn("executive_thesis", synth)
        self.assertIn("key_insights", synth)
        self.assertEqual(len(synth["key_insights"]), 4)
        self.assertIn("SIDEWAYS_RANGEBOUND", synth["executive_thesis"])

if __name__ == '__main__':
    unittest.main()
