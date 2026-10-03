import unittest
from fii_dii_engine import FIIDIIEngine, get_institutional_flow

class TestFIIDIIEngine(unittest.TestCase):

    def test_fii_dii_flow_payload_contract(self):
        """The flow payload must carry the full provenance contract and honest dating."""
        flow = get_institutional_flow()
        for key in ("timestamp", "as_of_date", "fii_cash_net_cr", "dii_cash_net_cr",
                    "total_net_cr", "institutional_sentiment", "institutional_score",
                    "formatted_summary", "is_simulated", "simulated_components", "data_source"):
            self.assertIn(key, flow)
        self.assertIsInstance(flow["is_simulated"], bool)
        self.assertIsInstance(flow["simulated_components"], list)
        self.assertTrue(flow["data_source"])  # non-empty provenance string

    def test_total_net_is_consistent(self):
        """Total net must equal FII + DII regardless of source."""
        flow = get_institutional_flow()
        expected = round(flow["fii_cash_net_cr"] + flow["dii_cash_net_cr"], 2)
        self.assertAlmostEqual(flow["total_net_cr"], expected, places=1)

    def test_sentiment_scale(self):
        """Sentiment classification covers the full range with valid scores."""
        flow = get_institutional_flow()
        self.assertIn(flow["institutional_score"], (15, 35, 50, 75, 92))
        self.assertTrue(flow["institutional_sentiment"])  # non-empty label
        # Score direction must agree with net flow sign for the extremes
        if "EXTREMELY BULLISH" in flow["institutional_sentiment"]:
            self.assertGreater(flow["total_net_cr"], 0)
        if "EXTREMELY BEARISH" in flow["institutional_sentiment"]:
            self.assertLess(flow["total_net_cr"], 0)

    def test_live_source_beats_simulation_flag(self):
        """If a real source answered, is_simulated must be False and the
        as_of_date must be surfaced (honest dating of post-close data)."""
        flow = get_institutional_flow()
        if not flow["is_simulated"]:
            self.assertIn(flow["as_of_date"], flow["formatted_summary"])
            self.assertIn("₹", flow["formatted_summary"])

    def test_smart_money_validation(self):
        """Smart Money breakout validation reflects real flow direction."""
        val = FIIDIIEngine.validate_smart_money_breakout("RELIANCE", is_long_signal=True)
        self.assertIn("smart_money_status", val)
        self.assertIn("is_valid", val)
        # Provenance must travel with the validation verdict
        self.assertIn("is_simulated", val)
        self.assertIn("as_of_date", val)

    def test_et_date_normalization(self):
        """ET date formats like '1st Oct 2026' normalize to '01-Oct-2026'."""
        self.assertEqual(FIIDIIEngine._et_normalize_date("1st Oct 2026"), "01-Oct-2026")
        self.assertEqual(FIIDIIEngine._et_normalize_date("21st March 2026"), "21-Mar-2026")
        self.assertEqual(FIIDIIEngine._et_normalize_date("2nd Nov 2026"), "02-Nov-2026")
        self.assertIsNone(FIIDIIEngine._et_normalize_date("garbage"))

    def test_cr_parser(self):
        """NSE/ET number strings ('1,332.12', '-9,484.3', None) parse safely."""
        self.assertEqual(FIIDIIEngine._parse_cr("1,332.12"), 1332.12)
        self.assertEqual(FIIDIIEngine._parse_cr("-9,484.3"), -9484.3)
        self.assertIsNone(FIIDIIEngine._parse_cr(None))
        self.assertIsNone(FIIDIIEngine._parse_cr("-"))

if __name__ == '__main__':
    unittest.main()
