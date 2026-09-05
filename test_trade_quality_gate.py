import unittest
from trade_quality_gate import TradeQualityGateEngine, evaluate_gate

class TestTradeQualityGateEngine(unittest.TestCase):

    def test_gate_passed(self):
        """Verifies trade gate pass when all criteria are satisfied."""
        data_res = {"is_trade_ready": True}
        regime_res = {"is_trade_allowed": True, "regime": "TRENDING_BULLISH"}
        risk_res = {"trading_paused": False}
        confirmations = ["15m trend", "VWAP", "ORB breakout", "RVOL", "Sector strength"]

        res = evaluate_gate("BHEL", "LONG", "ORB + VWAP RETEST", data_res, regime_res, risk_res, confirmations, trade_score=91.0)
        self.assertTrue(res["is_gate_passed"])
        self.assertEqual(res["decision"], "TRADE_LONG")
        self.assertEqual(res["grade"], "A+")

    def test_gate_blocked_insufficient_confirmations(self):
        """Verifies trade gate block when independent confirmations < 4."""
        data_res = {"is_trade_ready": True}
        regime_res = {"is_trade_allowed": True, "regime": "TRENDING_BULLISH"}
        risk_res = {"trading_paused": False}
        confirmations = ["15m trend", "VWAP"] # Only 2

        res = evaluate_gate("BHEL", "LONG", "ORB + VWAP RETEST", data_res, regime_res, risk_res, confirmations, trade_score=85.0)
        self.assertFalse(res["is_gate_passed"])
        self.assertEqual(res["decision"], "NO_TRADE")

if __name__ == '__main__':
    unittest.main()
