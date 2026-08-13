import os
import sys
import unittest

# Import all Phase test modules
from test_phase1 import TestPhase1DataQualityAndRegime
from test_phase2 import TestPhase2OptionGreeksAndChain
from test_phase3 import TestPhase3ExpectedMoveAndDTE
from test_phase4 import TestPhase4StrategyScoringAndNoTrade
from test_phase5 import TestPhase5CapitalMarginEngine
from test_phase6 import TestPhase6PositionManagerAndAuditLogs
from test_phase7 import TestPhase7PaperTradingAndJournal
from test_phase8 import TestPhase8BacktestEngine
from test_phase9 import TestPhase9ModelVersioningAndResearchAI

from broker_connector import BrokerConnector, get_broker_status

class TestPhase10BrokerAndMasterAcceptance(unittest.TestCase):

    def test_live_trading_safety_lock_default_off(self):
        """Verifies Section 46 Requirement: Live trading remains OFF by default."""
        status = get_broker_status()
        self.assertFalse(status["live_trading_active"])
        self.assertIn("LOCKED_OFF", status["safety_lock_status"])

    def test_hedge_failure_protection(self):
        """Verifies Section 46 Requirement: Hedge failure protection works."""
        # Attempt to execute unhedged short position
        res = BrokerConnector.execute_hedged_order("NIFTY Naked Short", ["SELL NIFTY 24500 CE"], 24500.0)
        self.assertFalse(res["success"])

if __name__ == '__main__':
    print("============================================================")
    print("   MASTER ACCEPTANCE SUITE - EXECUTING PHASES 1 TO 10 TESTS ")
    print("============================================================")
    unittest.main()
