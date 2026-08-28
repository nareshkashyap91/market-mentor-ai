import unittest

from test_telegram_bot_interactive import TestTelegramBotInteractive
from test_trade_journal_ui import TestTradeJournalUI
from test_greeks_hedging import TestGreeksHedgingEngine
from test_next_level_master import TestSectorRotationEngine, TestPreMarketAIEngine, TestBacktestUIEngine
from test_institutional_master import TestFIIDIIEngine, TestVolumeProfileEngine, TestIVSkewMaxPainEngine
from test_master_acceptance import TestPhase10BrokerAndMasterAcceptance

if __name__ == '__main__':
    print("==========================================================================")
    print("   ULTIMATE SYSTEM MODULES — MASTER INTEGRATION TEST SUITE               ")
    print("==========================================================================")
    unittest.main()
