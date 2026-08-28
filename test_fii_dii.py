import unittest
from fii_dii_engine import FIIDIIEngine, get_institutional_flow

class TestFIIDIIEngine(unittest.TestCase):

    def test_fii_dii_flow_calculation(self):
        """Verifies FII/DII Net Flow analytics and institutional sentiment classification."""
        flow = get_institutional_flow()
        self.assertIn("fii_cash_net_cr", flow)
        self.assertIn("dii_cash_net_cr", flow)
        self.assertTrue(flow["total_net_cr"] > 0)
        self.assertIn("ACCUMULATION", flow["institutional_sentiment"])

    def test_smart_money_validation(self):
        """Verifies Smart Money breakout confirmation."""
        val = FIIDIIEngine.validate_smart_money_breakout("RELIANCE", is_long_signal=True)
        self.assertTrue(val["is_valid"])
        self.assertIn("SMART MONEY", val["smart_money_status"])

if __name__ == '__main__':
    unittest.main()
