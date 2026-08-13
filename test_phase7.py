import os
import sys
import unittest

from paper_trading import PaperTradingEngine
from trade_journal import TradeJournalEngine

TEST_DB_PATH = os.path.join("data", "test_phase7_positions.db")

class TestPhase7PaperTradingAndJournal(unittest.TestCase):

    def setUp(self):
        try:
            if os.path.exists(TEST_DB_PATH):
                os.remove(TEST_DB_PATH)
        except Exception:
            pass
        PaperTradingEngine.init_db(TEST_DB_PATH)
        TradeJournalEngine.init_db(TEST_DB_PATH)

    def tearDown(self):
        try:
            if os.path.exists(TEST_DB_PATH):
                os.remove(TEST_DB_PATH)
        except Exception:
            pass

    def test_paper_account_initialization(self):
        """Verifies virtual account initialization with ₹1,00,000 capital."""
        summary = PaperTradingEngine.get_account_summary(TEST_DB_PATH)
        self.assertEqual(summary["initial_capital"], 100000.0)
        self.assertTrue(summary["net_portfolio_value"] >= 100000.0)

    def test_paper_order_execution(self):
        """Verifies paper order placement with virtual margin deduction."""
        order_res = PaperTradingEngine.place_paper_order(
            symbol="NIFTY",
            strategy_name="Bull Call Debit Spread",
            action="BUY",
            entry_price=24500.0,
            sl_price=24400.0,
            target1_price=24650.0,
            margin_req=1500.0,
            db_path=TEST_DB_PATH
        )
        self.assertTrue(order_res["success"])
        self.assertEqual(order_res["allocated_margin"], 1500.0)

    def test_trade_journal_logging_and_win_rate(self):
        """Verifies Trade Journal logging and Win Rate calculation."""
        # Log a winning trade
        TradeJournalEngine.log_trade("TJ_001", "NIFTY", "Bull Call Spread", "BUY", 24500.0, 24650.0, "14-Aug-2026 10:00 AM", 3750.0, "Target Hit", TEST_DB_PATH)
        
        # Log a losing trade
        TradeJournalEngine.log_trade("TJ_002", "RELIANCE", "Intraday Short", "SELL", 2500.0, 2520.0, "14-Aug-2026 11:00 AM", -1000.0, "SL Hit", TEST_DB_PATH)

        journal = TradeJournalEngine.get_journal_entries(limit=10, db_path=TEST_DB_PATH)
        self.assertEqual(len(journal), 2)

        perf = TradeJournalEngine.get_performance_summary(TEST_DB_PATH)
        self.assertEqual(perf["total_journal_trades"], 2)
        self.assertEqual(perf["total_wins"], 1)
        self.assertEqual(perf["win_rate_pct"], 50.0)
        self.assertEqual(perf["total_realized_pnl_rupees"], 2750.0)

if __name__ == '__main__':
    unittest.main()
