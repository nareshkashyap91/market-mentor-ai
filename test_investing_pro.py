import unittest
import os
from investing_pro_engine import InvestingProEngine

class TestInvestingProEngine(unittest.TestCase):

    def setUp(self):
        self.mock_info = {
            "currentPrice": 1000.0,
            "regularMarketPrice": 1000.0,
            "sharesOutstanding": 10000000,
            "freeCashflow": 500000000,
            "operatingCashflow": 600000000,
            "totalCash": 1000000000,
            "totalDebt": 200000000,
            "revenueGrowth": 0.12,
            "earningsGrowth": 0.15,
            "trailingEps": 50.0,
            "forwardEps": 58.0,
            "trailingPE": 20.0,
            "returnOnEquity": 0.20,
            "profitMargins": 0.15,
            "debtToEquity": 20.0,
            "dividendYield": 0.02,
            "52WeekHigh": 1200.0,
            "52WeekLow": 800.0,
            "marketCap": 10000000000,
            "longName": "Test Tech Limited"
        }

    def test_calculate_dcf_fair_value(self):
        """Verifies DCF Intrinsic Fair Value calculation."""
        dcf_val = InvestingProEngine.calculate_dcf_fair_value(self.mock_info)
        self.assertIsNotNone(dcf_val)
        self.assertGreater(dcf_val, 0)

    def test_calculate_graham_intrinsic_value(self):
        """Verifies Benjamin Graham Intrinsic Formula calculation."""
        graham_val = InvestingProEngine.calculate_graham_intrinsic_value(self.mock_info)
        self.assertIsNotNone(graham_val)
        self.assertGreater(graham_val, 0)

    def test_evaluate_financial_health_score(self):
        """Verifies 5-Pillar Financial Health Score calculation."""
        health = InvestingProEngine.evaluate_financial_health_score(self.mock_info)
        self.assertIn("overall_score", health)
        self.assertIn("pillars", health)
        self.assertGreaterEqual(health["overall_score"], 1.0)
        self.assertLessEqual(health["overall_score"], 5.0)

    def test_export_investing_pro_json(self):
        """Verifies JSON payload exporter runs cleanly."""
        payload = InvestingProEngine.export_investing_pro_json()
        self.assertIn("summary", payload)
        self.assertIn("stocks", payload)
        self.assertIn("propicks", payload)
        self.assertGreater(len(payload["stocks"]), 0)

if __name__ == '__main__':
    unittest.main()
