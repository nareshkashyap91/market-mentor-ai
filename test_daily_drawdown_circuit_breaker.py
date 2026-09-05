import unittest
from daily_drawdown_circuit_breaker import DailyDrawdownCircuitBreakerEngine, evaluate_circuit_breaker

class TestDailyDrawdownCircuitBreakerEngine(unittest.TestCase):

    def test_normal_circuit_breaker_status(self):
        """Verifies Normal Circuit Breaker status when PnL is positive."""
        res = evaluate_circuit_breaker(daily_pnl_pct=1.2, consecutive_losses=0)
        self.assertTrue(res["trading_allowed"])
        self.assertIn("NORMAL", res["circuit_breaker_status"])

    def test_max_daily_drawdown_tripped(self):
        """Verifies Circuit Breaker trip on max daily drawdown breach (-2.5%)."""
        res = evaluate_circuit_breaker(daily_pnl_pct=-2.5, consecutive_losses=1)
        self.assertFalse(res["trading_allowed"])
        self.assertIn("MAX DAILY DRAWDOWN LIMIT BREACHED", res["circuit_breaker_status"])

    def test_consecutive_loss_halting_tripped(self):
        """Verifies Circuit Breaker trip after 3 consecutive stop-losses."""
        res = evaluate_circuit_breaker(daily_pnl_pct=-1.2, consecutive_losses=3)
        self.assertFalse(res["trading_allowed"])
        self.assertIn("CONSECUTIVE LOSSES REACHED", res["circuit_breaker_status"])

if __name__ == '__main__':
    unittest.main()
