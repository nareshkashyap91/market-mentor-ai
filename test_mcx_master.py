import unittest

from test_mcx_commodity import TestMCXCommodityEngine
from test_smart_trader_master import TestSmartBreakoutPrecisionEngine, TestIntradayOrbVwapPrecisionEngine, TestAdaptiveRiskRegimeEngine
from test_multimedia_master import TestTelegramAudioEngine, TestChartPlotterEngine, TestWhatsAppNotifier
from test_master_acceptance import TestPhase10BrokerAndMasterAcceptance

if __name__ == '__main__':
    print("==========================================================================")
    print("   MCX COMMODITY OPTIONS ENGINE — MASTER INTEGRATION TEST SUITE           ")
    print("==========================================================================")
    unittest.main()
