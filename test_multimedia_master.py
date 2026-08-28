import unittest

from test_telegram_audio import TestTelegramAudioEngine
from test_chart_plotter import TestChartPlotterEngine
from test_whatsapp_notifier import TestWhatsAppNotifier
from test_ultimate_master import TestTelegramBotInteractive, TestTradeJournalUI, TestGreeksHedgingEngine
from test_master_acceptance import TestPhase10BrokerAndMasterAcceptance

if __name__ == '__main__':
    print("==========================================================================")
    print("   MULTIMEDIA & MESSAGING ENGINES — MASTER INTEGRATION TEST SUITE        ")
    print("==========================================================================")
    unittest.main()
