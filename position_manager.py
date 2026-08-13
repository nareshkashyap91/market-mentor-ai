import os
import sqlite3
from datetime import datetime, timezone, timedelta

DB_PATH = os.path.join("data", "positions.db")

class PositionManager:
    """Institutional Signal Persistence & Position Manager.
    Logs signal state changes, tracks active open positions, and computes floating P&L in SQLite DB.
    """

    @staticmethod
    def get_db_connection(db_path=DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls, db_path=DB_PATH):
        """Initializes SQLite database tables for active positions and signal audit logs."""
        conn = cls.get_db_connection(db_path)
        cursor = conn.cursor()

        # Positions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                strategy_name TEXT NOT NULL,
                action TEXT NOT NULL,
                entry_price REAL NOT NULL,
                current_price REAL NOT NULL,
                sl_price REAL NOT NULL,
                target1_price REAL NOT NULL,
                target2_price REAL NOT NULL,
                status TEXT NOT NULL,
                entry_time TEXT NOT NULL,
                exit_time TEXT,
                unrealized_pnl REAL DEFAULT 0.0,
                realized_pnl REAL DEFAULT 0.0
            )
        """)

        # Signal Audit Logs Table (Section 46 Requirement: "Signal changes are logged")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signal_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                previous_status TEXT NOT NULL,
                new_status TEXT NOT NULL,
                spot_price REAL NOT NULL,
                notes TEXT
            )
        """)

        conn.commit()
        conn.close()

    @classmethod
    def log_signal_change(cls, signal_id, prev_status, new_status, spot_price, notes="", db_path=DB_PATH):
        """Records an explicit Signal Change Audit entry into signal_logs table."""
        cls.init_db(db_path)
        conn = cls.get_db_connection(db_path)
        cursor = conn.cursor()

        ist_tz = timezone(timedelta(hours=5, minutes=30))
        now_str = datetime.now(ist_tz).strftime("%d-%b-%Y %I:%M %p")

        cursor.execute("""
            INSERT INTO signal_logs (signal_id, timestamp, previous_status, new_status, spot_price, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (signal_id, now_str, prev_status, new_status, spot_price, notes))

        conn.commit()
        conn.close()

    @classmethod
    def sync_signal(cls, signal_id, symbol, strategy_name, action, entry_price, current_price, sl_price, target1_price, target2_price=0.0, db_path=DB_PATH):
        """Syncs signal with database, evaluates price action, and manages lifecycle transitions."""
        cls.init_db(db_path)
        conn = cls.get_db_connection(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM positions WHERE id = ?", (signal_id,))
        existing = cursor.fetchone()

        ist_tz = timezone(timedelta(hours=5, minutes=30))
        now_str = datetime.now(ist_tz).strftime("%d-%b-%Y %I:%M %p")

        if existing is None:
            # New Signal Creation
            status = "ACTIVE_POSITION"
            is_buy = "BUY" in action.upper()
            pnl = (current_price - entry_price) if is_buy else (entry_price - current_price)

            cursor.execute("""
                INSERT INTO positions (id, symbol, strategy_name, action, entry_price, current_price, sl_price, target1_price, target2_price, status, entry_time, unrealized_pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (signal_id, symbol, strategy_name, action, entry_price, current_price, sl_price, target1_price, target2_price, status, now_str, round(pnl, 2)))

            conn.commit()
            conn.close()
            cls.log_signal_change(signal_id, "NEW_SIGNAL", status, current_price, f"Position initialized at ₹{entry_price:.2f}", db_path)
            return status

        # Existing Position Update
        old_status = existing["status"]
        status = old_status
        is_buy = "BUY" in action.upper()
        pnl = (current_price - entry_price) if is_buy else (entry_price - current_price)

        if old_status == "ACTIVE_POSITION":
            if is_buy:
                if current_price >= target1_price:
                    status = "TARGET1_HIT"
                elif current_price <= sl_price:
                    status = "SL_EXIT"
            else:
                if current_price <= target1_price:
                    status = "TARGET1_HIT"
                elif current_price >= sl_price:
                    status = "SL_EXIT"

        cursor.execute("""
            UPDATE positions
            SET current_price = ?, status = ?, unrealized_pnl = ?
            WHERE id = ?
        """, (current_price, status, round(pnl, 2), signal_id))

        conn.commit()
        conn.close()

        if old_status != status:
            cls.log_signal_change(signal_id, old_status, status, current_price, f"Status updated to {status}", db_path)

        return status

    @classmethod
    def get_active_positions(cls, db_path=DB_PATH):
        """Returns all open active positions from DB."""
        cls.init_db(db_path)
        conn = cls.get_db_connection(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM positions WHERE status = 'ACTIVE_POSITION' ORDER BY entry_time DESC")
        rows = cursor.fetchall()
        conn.close()

        return [dict(r) for r in rows]

    @classmethod
    def get_signal_audit_logs(cls, limit=15, db_path=DB_PATH):
        """Returns recent Signal Change Audit logs."""
        cls.init_db(db_path)
        conn = cls.get_db_connection(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM signal_logs ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()

        return [dict(r) for r in rows]
