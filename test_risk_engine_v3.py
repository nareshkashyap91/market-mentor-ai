import unittest
from risk_engine_v3 import RiskEngineV3, get_risk_v3

class TestRiskEngineV3(unittest.TestCase):

    def test_normal_risk_status(self):
        """Verifies normal risk evaluation."""
        res = get_risk_v3(daily_pnl_pct=1.0, consecutive_losses=0)
        self.assertFalse(res["trading_paused"])
        self.assertEqual(res["allowed_risk_pct"], 1.0)

    def test_trading_paused_on_daily_loss(self):
        """Verifies TRADING_PAUSED when daily loss limit is breached."""
        res = get_risk_v3(daily_pnl_pct=-2.5, consecutive_losses=1)
        self.assertTrue(res["trading_paused"])
        self.assertTrue(len(res["pause_reasons"]) >= 1)

if __name__ == '__main__':
    unittest.main()
