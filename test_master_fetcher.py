import unittest
import os
import json
from nse_option_chain_fetcher import NSEOptionChainFetcher
from master_data_fetcher import MasterDataFetcher

class TestMasterFetcherSuite(unittest.TestCase):
    """Test suite for NSE Option Chain Fetcher & Master Unified Pipeline Data Engine."""

    def test_01_live_nse_option_chain_fetcher(self):
        chain = NSEOptionChainFetcher.fetch_live_chain("NIFTY")
        self.assertIn("spot", chain)
        self.assertIn("pcr", chain)
        self.assertIn("max_call_oi_strike", chain)
        self.assertIn("max_put_oi_strike", chain)
        self.assertGreaterEqual(len(chain["strikes"]), 5)

        payload = NSEOptionChainFetcher.export_live_option_chain()
        self.assertIn("nifty", payload)
        self.assertTrue(os.path.exists(os.path.join("data", "option_chain_live.json")))

    def test_02_master_data_fetcher_single_pass(self):
        # Run master pipeline without auto git push
        MasterDataFetcher.run_master_pipeline(auto_git_push=False)

        # Check required JSON files exist and are populated
        required_json_files = [
            "option_chain_live.json",
            "ai_quant.json",
            "intraday.json",
            "evening.json",
            "sector_rotation.json",
            "trade_journal.json",
            "options_max_pain.json",
            "ml_target_sl_optimized.json",
            "portfolio_rebalancing.json",
            "morning_momentum_validated.json"
        ]

        for fname in required_json_files:
            fpath = os.path.join("data", fname)
            self.assertTrue(os.path.exists(fpath), f"Missing data JSON payload: {fname}")
            with open(fpath, "r") as f:
                content = json.load(f)
                self.assertIsNotNone(content)

if __name__ == "__main__":
    unittest.main()
