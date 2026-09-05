import unittest

from test_morning_breakout_validator import TestMorningBreakoutValidatorEngine
from test_institutional_precision_master import TestRelativeStrengthEngine, TestSMCLiquiditySweepEngine, TestDailyDrawdownCircuitBreakerEngine
from test_master_acceptance import TestPhase10BrokerAndMasterAcceptance

if __name__ == '__main__':
    print("==========================================================================")
    print("   MORNING LIVE BREAKOUT VALIDATOR — MASTER ZERO-REGRESSION TEST SUITE   ")
    print("==========================================================================")
    unittest.main()
