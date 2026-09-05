import unittest
import time
from data_quality_engine import DataQualityEngine, wrap_data

class TestDataQualityEngine(unittest.TestCase):

    def test_wrap_live_data(self):
        """Verifies wrapping of live data points."""
        dp = wrap_data(24580.25, source="NSE_YFinance", raw_timestamp=time.time())
        self.assertEqual(dp["status"], "LIVE")
        self.assertTrue(dp["is_reliable"])
        self.assertEqual(dp["confidence"], 100.0)

    def test_wrap_missing_data(self):
        """Verifies handling of missing/unavailable data."""
        dp = wrap_data(None, source="NSE")
        self.assertEqual(dp["status"], "MISSING")
        self.assertFalse(dp["is_reliable"])
        self.assertEqual(dp["value"], "DATA_UNAVAILABLE")

    def test_validate_dataset(self):
        """Verifies dataset validation for trade readiness."""
        ds = {
            "nifty_spot": wrap_data(24580.25, raw_timestamp=time.time()),
            "vix": wrap_data(13.20, raw_timestamp=time.time())
        }
        res = DataQualityEngine.validate_dataset(ds)
        self.assertTrue(res["is_trade_ready"])
        self.assertEqual(res["overall_confidence"], 100.0)

if __name__ == '__main__':
    unittest.main()
