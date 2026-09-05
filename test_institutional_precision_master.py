import unittest

from test_relative_strength import TestRelativeStrengthEngine
from test_smc_liquidity_sweep import TestSMCLiquiditySweepEngine
from test_daily_drawdown_circuit_breaker import TestDailyDrawdownCircuitBreakerEngine
from test_smart_trader_master import TestSmartBreakoutPrecisionEngine, TestIntradayOrbVwapPrecisionEngine, TestAdaptiveRiskRegimeEngine
from test_master_acceptance import TestPhase10BrokerAndMasterAcceptance

if __name__ == '__main__':
    print("==========================================================================")
    print("   INSTITUTIONAL PRECISION SUITE — MASTER ZERO-REGRESSION TEST SUITE     ")
    print("==========================================================================")
    unittest.main()
