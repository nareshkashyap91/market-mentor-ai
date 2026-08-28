import unittest

from test_smart_breakout_precision import TestSmartBreakoutPrecisionEngine
from test_intraday_orb_vwap_precision import TestIntradayOrbVwapPrecisionEngine
from test_adaptive_risk_regime import TestAdaptiveRiskRegimeEngine
from test_multimedia_master import TestTelegramAudioEngine, TestChartPlotterEngine, TestWhatsAppNotifier
from test_master_acceptance import TestPhase10BrokerAndMasterAcceptance

if __name__ == '__main__':
    print("==========================================================================")
    print("   SMART TRADER PRECISION SUITE — MASTER ZERO-REGRESSION TEST SUITE      ")
    print("==========================================================================")
    unittest.main()
