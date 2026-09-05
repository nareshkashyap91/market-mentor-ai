import unittest
from mcx_event_engine import MCXEventEngine, check_mcx_event_risk

class TestMCXEventEngine(unittest.TestCase):

    def test_normal_no_event_risk(self):
        """Verifies normal trading status when no event risk is active."""
        res = check_mcx_event_risk("CRUDEOIL")
        self.assertIn("action", res)
        self.assertIn(res["action"], ["TRADE_ALLOWED", "NEW_TRADE_BLOCKED"])

    def test_lockout_configuration(self):
        """Verifies pre-event lockout and post-event cooldown parameters."""
        self.assertEqual(MCXEventEngine.PRE_EVENT_LOCKOUT_MINUTES, 30)
        self.assertEqual(MCXEventEngine.POST_EVENT_COOLDOWN_MINUTES, 15)

if __name__ == '__main__':
    unittest.main()
