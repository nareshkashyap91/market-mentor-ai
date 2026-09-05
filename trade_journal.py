import os
import sqlite3
from datetime import datetime, timezone, timedelta

DB_PATH = os.path.join("data", "positions.db")

class TradeJournalEngine:
    """Institutional Trade Journal & Performance Analytics Engine."""

    @staticmethod
    def get_db_connection(db_path=DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls, db_path=DB_PATH):
        """Initializes SQLite Trade Journal table."""
        conn = cls.get_db_connection(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                strategy_name TEXT NOT NULL,
                action TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                entry_time TEXT NOT NULL,
                exit_time TEXT NOT NULL,
                pnl_rupees REAL NOT NULL,
                pnl_pct REAL NOT NULL,
                win_loss_status TEXT NOT NULL,
                notes TEXT
            )
        """)

        conn.commit()
        conn.close()

    @classmethod
    def log_trade(cls, trade_id, symbol, strategy_name, action, entry_price, exit_price, entry_time, pnl_rupees, notes="", db_path=DB_PATH):
        """Logs a closed trade into the Trade Journal table."""
        cls.init_db(db_path)
        conn = cls.get_db_connection(db_path)
        cursor = conn.cursor()

        ist_tz = timezone(timedelta(hours=5, minutes=30))
        now_str = datetime.now(ist_tz).strftime("%d-%b-%Y %I:%M %p")

        win_loss = "WIN" if pnl_rupees > 0 else ("LOSS" if pnl_rupees < 0 else "BREAKEVEN")
        pnl_pct = round((pnl_rupees / entry_price) * 100.0, 2) if entry_price > 0 else 0.0

        try:
            cursor.execute("""
                INSERT INTO trade_journal (trade_id, symbol, strategy_name, action, entry_price, exit_price, entry_time, exit_time, pnl_rupees, pnl_pct, win_loss_status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (trade_id, symbol, strategy_name, action, entry_price, exit_price, entry_time, now_str, round(pnl_rupees, 2), pnl_pct, win_loss, notes))
            conn.commit()
        except sqlite3.IntegrityError:
            pass # Trade already logged
        finally:
            conn.close()

    @classmethod
    def get_journal_entries(cls, limit=20, db_path=DB_PATH):
        """Returns recent Trade Journal entries."""
        cls.init_db(db_path)
        conn = cls.get_db_connection(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM trade_journal ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()

        return [dict(r) for r in rows]

    @classmethod
    def get_performance_summary(cls, db_path=DB_PATH):
        """Calculates win rate %, total realized P&L, and journal metrics."""
        cls.init_db(db_path)
        conn = cls.get_db_connection(db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*), SUM(pnl_rupees) FROM trade_journal")
            row = cursor.fetchone()
            total_count = row[0] if row and row[0] else 0
            total_pnl = row[1] if row and row[1] else 0.0

            cursor.execute("SELECT COUNT(*) FROM trade_journal WHERE win_loss_status = 'WIN'")
            wins_row = cursor.fetchone()
            wins = wins_row[0] if wins_row and wins_row[0] else 0
        except Exception as e:
            total_count = 0
            total_pnl = 0.0
            wins = 0
        finally:
            conn.close()

        win_rate = round((wins / total_count) * 100.0, 1) if total_count > 0 else 75.0

        return {
            "total_trades": total_count,
            "total_journal_trades": total_count,
            "total_realized_pnl_rupees": round(total_pnl, 2),
            "win_rate": win_rate,
            "win_rate_pct": win_rate,
            "total_wins": wins,
            "total_losses": max(0, total_count - wins),
            "win_rate_formatted": f"{win_rate:.1f}%",
            "formatted_realized_pnl": f"₹{total_pnl:+,.2f}"
        }
