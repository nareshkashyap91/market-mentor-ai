import os
import json
import unittest
from morning_momentum_validator import MorningMomentumValidatorEngine

class TestMorningMomentumValidatorSuite(unittest.TestCase):
    """Test suite for Morning Momentum Validator Engine V5.5."""

    def test_01_load_candidate_symbols(self):
        candidates = MorningMomentumValidatorEngine.load_candidate_symbols()
        self.assertGreaterEqual(len(candidates), 1)
        self.assertIn("symbol", candidates[0])

    def test_02_validate_morning_breakouts(self):
        sample_candidates = [
            {"symbol": "HOMEFIRST", "company": "Home First Finance", "prev_close": 1233.7, "rsi": 63.7},
            {"symbol": "PFOCUS", "company": "Prime Focus Ltd", "prev_close": 311.75, "rsi": 62.3}
        ]
        setups = MorningMomentumValidatorEngine.validate_morning_breakouts(sample_candidates, is_simulation=True)
        self.assertGreaterEqual(len(setups), 1)
        
        setup = setups[0]
        self.assertIn("symbol", setup)
        self.assertIn("entry_price", setup)
        self.assertIn("sl_price", setup)
        self.assertIn("target_1", setup)
        self.assertIn("target_2", setup)
        self.assertIn("star_rating", setup)
        self.assertLess(setup["sl_price"], setup["entry_price"])
        self.assertGreater(setup["target_1"], setup["entry_price"])

    def test_03_export_payload(self):
        payload = MorningMomentumValidatorEngine.export_and_broadcast_morning_signals()
        self.assertIn("high_conviction_setups", payload)
        self.assertTrue(os.path.exists(os.path.join("data", "morning_momentum_validated.json")))

if __name__ == "__main__":
    unittest.main()
