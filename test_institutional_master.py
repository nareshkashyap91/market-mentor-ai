import unittest

from test_fii_dii import TestFIIDIIEngine
from test_volume_profile import TestVolumeProfileEngine
from test_iv_skew_maxpain import TestIVSkewMaxPainEngine
from test_momentum_master import TestNextDayMomentumPhase1, TestNextDayMomentumPhase2, TestNextDayMomentumPhase3, TestNextDayMomentumPhase4
from test_master_acceptance import TestPhase10BrokerAndMasterAcceptance

if __name__ == '__main__':
    print("==========================================================================")
    print("   INSTITUTIONAL QUANTITATIVE ENGINES — MASTER INTEGRATION SUITE         ")
    print("==========================================================================")
    unittest.main()
