import unittest
from institutional_flow_v3 import InstitutionalFlowV3Engine, get_institutional_flow_v3

class TestInstitutionalFlowV3Engine(unittest.TestCase):

    def test_bullish_positioning_proxy(self):
        """Verifies Bullish Positioning Proxy analysis."""
        res = get_institutional_flow_v3(fii_cash_cr=2100.0, dii_cash_cr=800.0, pcr=1.30)
        self.assertEqual(res["options_positioning_bias"], "BULLISH")
        self.assertTrue(res["institutional_flow_score"] >= 80.0)
        self.assertIn("Institutional cash accumulation proxy", res["positioning_proxy_summary"])

    def test_conflicted_positioning_proxy(self):
        """Verifies Conflicted positioning proxy when FII cash and PCR diverge."""
        res = get_institutional_flow_v3(fii_cash_cr=1500.0, dii_cash_cr=-1200.0, pcr=0.85)
        self.assertEqual(res["options_positioning_bias"], "CONFLICTED")

if __name__ == '__main__':
    unittest.main()
