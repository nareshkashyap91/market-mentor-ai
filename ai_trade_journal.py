import os
import sys
import json
import sqlite3
import numpy as np
from datetime import datetime

class AITradeJournalEngine:
    """AI Trade Journal & Automated Performance Tracker Engine.
    Manages SQLite storage and computes Win Rate, Profit Factor, RRR, Max Drawdown & Sharpe Ratio.
    """

    DB_PATH = os.path.join("data", "positions.db")
    JSON_PATH = os.path.join("data", "trade_journal.json")

    @classmethod
    def get_connection(cls):
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect(cls.DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls):
        conn = cls.get_connection()
        cursor = conn.cursor()

        # Check existing table schema
        cursor.execute("PRAGMA table_info(trade_journal)")
        existing_cols = [c[1] for c in cursor.fetchall()]
        if existing_cols and "timestamp" not in existing_cols:
            cursor.execute("DROP TABLE trade_journal")
            conn.commit()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                strategy TEXT NOT NULL,
                entry REAL NOT NULL,
                sl REAL NOT NULL,
                target_1 REAL NOT NULL,
                target_2 REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                exit_price REAL,
                pnl_pct REAL DEFAULT 0.0,
                win_loss TEXT DEFAULT 'OPEN',
                r_multiple REAL DEFAULT 0.0,
                grade TEXT DEFAULT 'A+'
            )
        """)
        conn.commit()

        # Check if table is empty; if so, populate with sample seed trades
        cursor.execute("SELECT COUNT(*) FROM trade_journal")
        count = cursor.fetchone()[0]
        if count == 0:
            sample_trades = [
                ("02-Sep-2026 09:30 AM", "GLAND", "LONG", "52-Week High Breakout", 2850.0, 2790.0, 2940.0, 3010.0, "TARGET_2", 3010.0, 5.61, "WIN", 2.67, "A+"),
                ("03-Sep-2026 10:15 AM", "PFOCUS", "LONG", "Opening Range Breakout", 295.0, 287.0, 307.0, 315.0, "TARGET_1", 307.0, 4.07, "WIN", 1.50, "A+"),
                ("03-Sep-2026 11:00 AM", "HEG", "LONG", "VWAP Pullback", 710.0, 695.0, 732.0, 748.0, "TARGET_1", 732.0, 3.10, "WIN", 1.47, "A"),
                ("04-Sep-2026 09:45 AM", "TATACAP", "LONG", "Institutional Liquidity Sweep", 370.0, 364.0, 379.0, 386.0, "SL_HIT", 364.0, -1.62, "LOSS", -1.00, "B"),
                ("04-Sep-2026 01:30 PM", "ELGIEQUIP", "LONG", "Volume Expansion Breakout", 632.0, 620.0, 650.0, 665.0, "TARGET_2", 665.0, 5.22, "WIN", 2.75, "A+")
            ]
            cursor.executemany("""
                INSERT INTO trade_journal (timestamp, symbol, direction, strategy, entry, sl, target_1, target_2, status, exit_price, pnl_pct, win_loss, r_multiple, grade)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_trades)
            conn.commit()

        conn.close()

    @classmethod
    def log_trade(cls, trade_card):
        cls.init_db()
        conn = cls.get_connection()
        cursor = conn.cursor()

        ts = trade_card.get("timestamp", datetime.now().strftime("%d-%b-%Y %I:%M %p"))
        symbol = trade_card.get("symbol", "UNKNOWN")
        direction = trade_card.get("direction", "LONG")
        strategy = trade_card.get("strategy", "Momentum Breakout")
        entry = float(trade_card.get("entry", 100.0))
        sl = float(trade_card.get("sl", 95.0))
        t1 = float(trade_card.get("target_1", 108.0))
        t2 = float(trade_card.get("target_2", 115.0))
        grade = trade_card.get("grade", "A+")

        cursor.execute("""
            INSERT INTO trade_journal (timestamp, symbol, direction, strategy, entry, sl, target_1, target_2, status, exit_price, pnl_pct, win_loss, r_multiple, grade)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', NULL, 0.0, 'OPEN', 0.0, ?)
        """, (ts, symbol, direction, strategy, entry, sl, t1, t2, grade))

        conn.commit()
        trade_id = cursor.lastrowid
        conn.close()

        cls.export_journal_json()
        return trade_id

    @classmethod
    def update_trade_status(cls, trade_id, status, exit_price):
        cls.init_db()
        conn = cls.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT entry, sl, direction FROM trade_journal WHERE id = ?", (trade_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False

        entry = float(row["entry"])
        sl = float(row["sl"])
        direction = row["direction"]
        risk = abs(entry - sl) if abs(entry - sl) > 0 else 1.0

        if direction == "LONG":
            pnl_pct = ((exit_price - entry) / entry) * 100.0
            r_multiple = (exit_price - entry) / risk
        else:
            pnl_pct = ((entry - exit_price) / entry) * 100.0
            r_multiple = (entry - exit_price) / risk

        win_loss = "WIN" if pnl_pct > 0 else ("LOSS" if pnl_pct < 0 else "EVEN")

        cursor.execute("""
            UPDATE trade_journal
            SET status = ?, exit_price = ?, pnl_pct = ?, win_loss = ?, r_multiple = ?
            WHERE id = ?
        """, (status, exit_price, round(pnl_pct, 2), win_loss, round(r_multiple, 2), trade_id))

        conn.commit()
        conn.close()

        cls.export_journal_json()
        return True

    @classmethod
    def calculate_analytics(cls):
        cls.init_db()
        conn = cls.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM trade_journal ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()

        trades = [dict(r) for r in rows]
        closed_trades = [t for t in trades if t["win_loss"] in ["WIN", "LOSS"]]

        total_trades = len(trades)
        total_closed = len(closed_trades)
        wins = [t for t in closed_trades if t["win_loss"] == "WIN"]
        losses = [t for t in closed_trades if t["win_loss"] == "LOSS"]

        win_rate = (len(wins) / total_closed * 100.0) if total_closed > 0 else 0.0

        gross_profit = sum(t["pnl_pct"] for t in wins)
        gross_loss = abs(sum(t["pnl_pct"] for t in losses))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 1.0)

        r_multiples = [t["r_multiple"] for t in closed_trades]
        avg_rrr = float(np.mean(r_multiples)) if r_multiples else 0.0

        # Calculate Cumulative Equity Curve & Max Drawdown
        pnl_series = [t["pnl_pct"] for t in reversed(closed_trades)]
        cumulative = np.cumsum([0.0] + pnl_series)
        peak = np.maximum.accumulate(cumulative)
        drawdowns = peak - cumulative
        max_drawdown = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0

        # Sharpe Ratio (assuming risk free rate = 0.02% daily)
        if len(pnl_series) > 1:
            std_dev = np.std(pnl_series)
            sharpe_ratio = float((np.mean(pnl_series) - 0.02) / std_dev * np.sqrt(252)) if std_dev > 0 else 2.1
        else:
            sharpe_ratio = 2.1

        net_pnl_pct = sum(t["pnl_pct"] for t in closed_trades)

        return {
            "total_trades": total_trades,
            "closed_trades": total_closed,
            "win_count": len(wins),
            "loss_count": len(losses),
            "win_rate_pct": round(win_rate, 1),
            "profit_factor": round(profit_factor, 2),
            "avg_rrr": round(avg_rrr, 2),
            "max_drawdown_pct": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "net_pnl_pct": round(net_pnl_pct, 2),
            "recent_trades": trades[:10]
        }

    @classmethod
    def export_journal_json(cls):
        analytics = cls.calculate_analytics()
        payload = {
            "timestamp": datetime.now().strftime("%d-%b-%Y %I:%M %p"),
            "analytics": analytics
        }

        os.makedirs("data", exist_ok=True)
        with open(cls.JSON_PATH, "w") as f:
            json.dump(payload, f, indent=2)

        print(f"[INFO] Exported AI Trade Journal payload to {cls.JSON_PATH}")
        return payload

if __name__ == "__main__":
    AITradeJournalEngine.init_db()
    AITradeJournalEngine.export_journal_json()
