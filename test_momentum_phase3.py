import unittest
from momentum_intelligence_engine import (
    NextDayEntryEngine,
    StopLossTargetEngine,
    PositionSizingEngine,
    EventRiskEngine,
    MomentumNoTradeGuardrail
)

class TestNextDayMomentumPhase3(unittest.TestCase):

    def test_entry_plan_generation(self):
        """Verifies Entry Zone, Confirmation Condition, and Invalidation Level."""
        plan = NextDayEntryEngine.generate_entry_plan(close=420.0, breakout_level=415.0, atr=10.0)
        self.assertIn("415.00", plan["entry_zone_str"])
        self.assertIn("RVOL > 1.5", plan["confirmation_condition"])
        self.assertEqual(plan["invalidation_level"], 410.0)

    def test_stop_loss_and_target_calculation(self):
        """Verifies Stop Loss, Targets (T1, T2, T3), and RRR calculation."""
        res = StopLossTargetEngine.calculate_sl_and_targets(entry_price=420.0, low=412.0, atr=10.0, min_rr=1.5)
        self.assertTrue(res["stop_loss"] < 420.0)
        self.assertTrue(res["target1"] > 420.0)
        self.assertTrue(res["target2"] > res["target1"])
        self.assertTrue(res["rrr_acceptable"])
        self.assertEqual(res["rrr_t1"], 1.5)

    def test_position_sizing(self):
        """Verifies 1% risk position sizing on ₹1,00,000 capital."""
        pos = PositionSizingEngine.calculate_position_size(trading_capital=100000.0, risk_pct=1.0, entry_price=420.0, sl_price=410.0)
        self.assertEqual(pos["max_risk_amount"], 1000.0)
        self.assertEqual(pos["risk_per_share"], 10.0)
        self.assertEqual(pos["quantity"], 100)
        self.assertEqual(pos["capital_required"], 42000.0)
        self.assertEqual(pos["max_loss"], 1000.0)

    def test_event_risk_engine(self):
        """Verifies Event Risk Engine levels."""
        low_risk = EventRiskEngine.evaluate_event_risk(has_earnings_soon=False)
        self.assertEqual(low_risk["event_risk_level"], "LOW")

        high_risk = EventRiskEngine.evaluate_event_risk(has_earnings_soon=True)
        self.assertEqual(high_risk["event_risk_level"], "HIGH")

    def test_no_trade_guardrails(self):
        """Verifies strict NO TRADE Guardrail trigger."""
        valid_val = {"is_valid": True, "status": "PASSED"}
        rrr_ok = {"rrr_acceptable": True, "rrr_t1": 1.8}
        extension_norm = {"extension_status": "NORMAL"}
        event_low = {"event_risk_level": "LOW"}

        # Passed Guardrails
        pass_res = MomentumNoTradeGuardrail.evaluate_guardrails(rrr_ok, extension_norm, event_low, valid_val, rvol=1.8)
        self.assertFalse(pass_res["is_no_trade"])

        # Triggered Guardrails (Highly Extended)
        extension_high = {"extension_status": "HIGHLY EXTENDED"}
        fail_res = MomentumNoTradeGuardrail.evaluate_guardrails(rrr_ok, extension_high, event_low, valid_val, rvol=1.8)
        self.assertTrue(fail_res["is_no_trade"])
        self.assertIn("Highly Extended", fail_res["no_trade_summary"])

if __name__ == '__main__':
    unittest.main()
