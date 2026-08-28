import unittest

from test_sector_rotation import TestSectorRotationEngine
from test_premarket_ai import TestPreMarketAIEngine
from test_backtest_ui import TestBacktestUIEngine
from test_institutional_master import TestFIIDIIEngine, TestVolumeProfileEngine, TestIVSkewMaxPainEngine
from test_master_acceptance import TestPhase10BrokerAndMasterAcceptance

if __name__ == '__main__':
    print("==========================================================================")
    print("   NEXT-LEVEL ENGINES — MASTER INTEGRATION TEST SUITE                    ")
    print("==========================================================================")
    unittest.main()
