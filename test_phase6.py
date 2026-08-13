import os
import sys
import unittest

from position_manager import PositionManager

TEST_DB_PATH = os.path.join("data", "test_positions.db")

class TestPhase6PositionManagerAndAuditLogs(unittest.TestCase):

    def setUp(self):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        PositionManager.init_db(TEST_DB_PATH)

    def tearDown(self):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def test_position_creation_and_audit_logging(self):
        """Verifies position creation and signal change audit logging."""
        status = PositionManager.sync_signal(
            signal_id="SIG_001",
            symbol="NIFTY",
            strategy_name="Bull Call Debit Spread",
            action="BUY",
            entry_price=24500.0,
            current_price=24500.0,
            sl_price=24400.0,
            target1_price=24650.0,
            db_path=TEST_DB_PATH
        )

        self.assertEqual(status, "ACTIVE_POSITION")

        # Verify active position retrieval
        active_pos = PositionManager.get_active_positions(TEST_DB_PATH)
        self.assertEqual(len(active_pos), 1)
        self.assertEqual(active_pos[0]["symbol"], "NIFTY")

        # Verify signal audit log insertion
        logs = PositionManager.get_signal_audit_logs(limit=10, db_path=TEST_DB_PATH)
        self.assertTrue(len(logs) >= 1)
        self.assertEqual(logs[0]["new_status"], "ACTIVE_POSITION")

    def test_target_hit_state_transition(self):
        """Verifies automatic state transition to TARGET1_HIT when price hits target."""
        # 1. Create Position
        PositionManager.sync_signal(
            signal_id="SIG_002",
            symbol="RELIANCE",
            strategy_name="Intraday Long",
            action="BUY",
            entry_price=2500.0,
            current_price=2500.0,
            sl_price=2480.0,
            target1_price=2530.0,
            db_path=TEST_DB_PATH
        )

        # 2. Update price to target (2535 > 2530)
        new_status = PositionManager.sync_signal(
            signal_id="SIG_002",
            symbol="RELIANCE",
            strategy_name="Intraday Long",
            action="BUY",
            entry_price=2500.0,
            current_price=2535.0,
            sl_price=2480.0,
            target1_price=2530.0,
            db_path=TEST_DB_PATH
        )

        self.assertEqual(new_status, "TARGET1_HIT")

        # Verify state change logged in audit trail
        logs = PositionManager.get_signal_audit_logs(limit=10, db_path=TEST_DB_PATH)
        self.assertTrue(any(l["new_status"] == "TARGET1_HIT" for l in logs))

if __name__ == '__main__':
    unittest.main()
