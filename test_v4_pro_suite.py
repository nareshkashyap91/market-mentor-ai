import unittest
import os
import json
import sqlite3
from ai_trade_journal import AITradeJournalEngine
from sector_rotation_engine import SectorRotationEngine
from options_engine_v3 import OptionsEngineV3
from intraday_precision_v3 import IntradayPrecisionV3Engine

class TestV4ProSuite(unittest.TestCase):
    """V4.0 Pro Suite Unit Tests.
    Tests AI Trade Journal, Sector Rotation, Options Max Pain, and Multi-Timeframe Confluence.
    """

    def setUp(self):
        AITradeJournalEngine.init_db()

    def test_01_trade_journal_init_and_export(self):
        payload = AITradeJournalEngine.export_journal_json()
        self.assertIn("analytics", payload)
        analytics = payload["analytics"]
        self.assertGreaterEqual(analytics["total_trades"], 1)
        self.assertIn("win_rate_pct", analytics)
        self.assertIn("profit_factor", analytics)

    def test_02_trade_journal_logging_and_update(self):
        card = {
            "symbol": "TEST_STOCK",
            "direction": "LONG",
            "strategy": "V4 Test Strategy",
            "entry": 500.0,
            "sl": 480.0,
            "target_1": 530.0,
            "target_2": 550.0,
            "grade": "A+"
        }
        trade_id = AITradeJournalEngine.log_trade(card)
        self.assertIsNotNone(trade_id)

        success = AITradeJournalEngine.update_trade_status(trade_id, "TARGET_1", 530.0)
        self.assertTrue(success)

        analytics = AITradeJournalEngine.calculate_analytics()
        self.assertGreaterEqual(analytics["total_trades"], 2)

    def test_03_sector_rotation_engine(self):
        sectors = SectorRotationEngine.fetch_sector_data()
        self.assertGreaterEqual(len(sectors), 5)
        top_sector = sectors[0]
        self.assertIn("rs_score", top_sector)
        self.assertIn("fund_flow", top_sector)
        self.assertIn("status", top_sector)

        payload = SectorRotationEngine.export_sector_json()
        self.assertIn("sectors", payload)
        self.assertTrue(os.path.exists(SectorRotationEngine.JSON_PATH))

    def test_04_options_max_pain_and_gamma_squeeze(self):
        max_pain = OptionsEngineV3.calculate_max_pain(24580.25)
        self.assertIsInstance(max_pain, int)

        squeeze_info = OptionsEngineV3.detect_gamma_squeeze(spot=24610.0, max_call_oi=24600, pcr=1.35, vol_expansion=2.5)
        self.assertTrue(squeeze_info["is_gamma_squeeze"])
        self.assertIn("ALERT: GAMMA SQUEEZE", squeeze_info["status"])

        payload = OptionsEngineV3.export_max_pain_json(24580.25)
        self.assertIn("max_pain_strike", payload)
        self.assertTrue(os.path.exists(os.path.join("data", "options_max_pain.json")))

    def test_05_multi_timeframe_confluence_radar(self):
        res = IntradayPrecisionV3Engine.evaluate_mtf_confluence(tf_5m=True, tf_15m=True, tf_1h=True, tf_daily=True)
        self.assertEqual(res["confluence_stars"], "⭐⭐⭐⭐⭐")
        self.assertEqual(res["confluence_rating"], "5-STAR CONFLUENCE SETUP")
        self.assertEqual(res["confluence_score"], 5.0)

        res_partial = IntradayPrecisionV3Engine.evaluate_mtf_confluence(tf_5m=True, tf_15m=True, tf_1h=False, tf_daily=True)
        self.assertEqual(res_partial["confluence_stars"], "⭐⭐⭐⭐")

if __name__ == "__main__":
    unittest.main()
