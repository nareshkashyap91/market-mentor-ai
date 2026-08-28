import unittest

# Import all Momentum Phase tests
from test_momentum_phase1 import TestNextDayMomentumPhase1
from test_momentum_phase2 import TestNextDayMomentumPhase2
from test_momentum_phase3 import TestNextDayMomentumPhase3
from test_momentum_phase4 import TestNextDayMomentumPhase4

# Import System Master Acceptance Test
from test_master_acceptance import TestPhase10BrokerAndMasterAcceptance

if __name__ == '__main__':
    print("==========================================================================")
    print("   NEXT-DAY MOMENTUM STOCK INTELLIGENCE ENGINE - MASTER TEST SUITE v2.0   ")
    print("==========================================================================")
    unittest.main()
