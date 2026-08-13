import os
import sqlite3
from datetime import datetime, timezone, timedelta

DB_PATH = os.path.join("data", "positions.db")
INITIAL_VIRTUAL_CAPITAL = 100000.0  # ₹1,00,000 Virtual Capital

from position_manager import PositionManager

class PaperTradingEngine:
    """Institutional Virtual Paper Trading Simulator Engine."""

    @staticmethod
    def get_db_connection(db_path=DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls, db_path=DB_PATH):
        """Initializes Virtual Account Portfolio table in SQLite DB."""
        PositionManager.init_db(db_path)
        conn = cls.get_db_connection(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                initial_capital REAL NOT NULL,
                current_balance REAL NOT NULL,
                allocated_margin REAL DEFAULT 0.0,
                realized_pnl REAL DEFAULT 0.0,
                unrealized_pnl REAL DEFAULT 0.0,
                total_trades INTEGER DEFAULT 0
            )
        """)

        cursor.execute("SELECT COUNT(*) FROM paper_portfolio")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO paper_portfolio (initial_capital, current_balance, allocated_margin, realized_pnl, unrealized_pnl, total_trades)
                VALUES (?, ?, 0.0, 0.0, 0.0, 0)
            """, (INITIAL_VIRTUAL_CAPITAL, INITIAL_VIRTUAL_CAPITAL))

        conn.commit()
        conn.close()

    @classmethod
    def get_account_summary(cls, db_path=DB_PATH):
        """Returns virtual account portfolio summary."""
        cls.init_db(db_path)
        conn = cls.get_db_connection(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM paper_portfolio LIMIT 1")
        row = cursor.fetchone()

        # Calculate floating unrealized P&L from active positions
        cursor.execute("SELECT SUM(unrealized_pnl) FROM positions WHERE status = 'ACTIVE_POSITION'")
        unrealized_sum = cursor.fetchone()[0] or 0.0

        conn.close()

        r = dict(row) if row else {
            "initial_capital": INITIAL_VIRTUAL_CAPITAL,
            "current_balance": INITIAL_VIRTUAL_CAPITAL,
            "allocated_margin": 0.0,
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
            "total_trades": 0
        }

        r["unrealized_pnl"] = round(float(unrealized_sum), 2)
        r["net_portfolio_value"] = round(r["current_balance"] + r["unrealized_pnl"], 2)
        r["formatted_balance"] = f"₹{r['net_portfolio_value']:,.2f}"

        return r

    @classmethod
    def place_paper_order(cls, symbol, strategy_name, action, entry_price, sl_price, target1_price, margin_req=1500.0, db_path=DB_PATH):
        """Places a paper trading virtual order with risk checks."""
        cls.init_db(db_path)
        acc = cls.get_account_summary(db_path)

        if acc["current_balance"] < margin_req:
            return {
                "success": False,
                "reason": f"Insufficient Virtual Margin (Required: ₹{margin_req:,.0f}, Available: ₹{acc['current_balance']:,.0f})"
            }

        # Update allocated margin & trade count
        conn = cls.get_db_connection(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE paper_portfolio
            SET allocated_margin = allocated_margin + ?,
                total_trades = total_trades + 1
        """, (margin_req,))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "allocated_margin": margin_req,
            "status": "PAPER_ORDER_EXECUTED"
        }
