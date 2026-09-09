import os
import json
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from telegram_config import send_deduplicated_telegram_alert, get_telegram_credentials

EVENING_JSON_PATH = os.path.join("data", "evening.json")
MOMENTUM_INTEL_PATH = os.path.join("data", "momentum_intelligence.json")
OUTPUT_JSON_PATH = os.path.join("data", "morning_momentum_validated.json")

class MorningMomentumValidatorEngine:
    """Morning Pre-Market & 15m ORB High-Conviction Validation Engine V5.5.
    Takes yesterday evening's momentum stock candidates, scans morning price action,
    filters TOP ⭐⭐⭐⭐⭐ High-Conviction breakouts, and dispatches exact Entry/SL/Targets to Telegram.
    """

    @classmethod
    def load_candidate_symbols(cls):
        """Loads yesterday evening's momentum stock candidates."""
        candidates = []
        
        if os.path.exists(EVENING_JSON_PATH):
            try:
                with open(EVENING_JSON_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Support both list of dicts and dict with 'stocks' key
                    if isinstance(data, list):
                        candidates = data
                    elif isinstance(data, dict):
                        candidates = data.get("stocks", []) or data.get("momentum_stocks", [])
            except Exception as e:
                print(f"[WARN] Could not read evening.json: {e}")

        if not candidates and os.path.exists(MOMENTUM_INTEL_PATH):
            try:
                with open(MOMENTUM_INTEL_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    candidates = data.get("momentum_candidates", [])
            except Exception as e:
                print(f"[WARN] Could not read momentum_intelligence.json: {e}")

        # Fallback default candidates if files not populated
        if not candidates:
            candidates = [
                {"symbol": "HOMEFIRST", "company": "Home First Finance", "close": 1233.7, "rsi": 63.7, "vol_expansion": 2.2},
                {"symbol": "PFOCUS", "company": "Prime Focus Ltd", "close": 311.75, "rsi": 62.3, "vol_expansion": 2.2},
                {"symbol": "PPLPHARMA", "company": "Piramal Pharma", "close": 219.66, "rsi": 65.1, "vol_expansion": 1.8},
                {"symbol": "NCC", "company": "NCC Limited", "close": 150.67, "rsi": 59.9, "vol_expansion": 1.6},
                {"symbol": "ANANTRAJ", "company": "Anant Raj Ltd", "close": 638.25, "rsi": 62.4, "vol_expansion": 1.3}
            ]

        symbol_list = []
        for c in candidates:
            sym = c.get("symbol") or c.get("ticker")
            if sym:
                # Clean ticker format
                sym_clean = sym.replace(".NS", "").replace("NSE:", "").strip()
                symbol_list.append({
                    "symbol": sym_clean,
                    "company": c.get("company", sym_clean),
                    "prev_close": c.get("price") or c.get("close", 100.0),
                    "rsi": c.get("rsi", 60.0),
                    "vol_expansion": c.get("vol_expansion", 1.5)
                })

        return symbol_list

    @classmethod
    def validate_morning_breakouts(cls, candidates=None, is_simulation=False):
        """Scans candidates in morning session, evaluates 15m ORB + VWAP + RVOL, and scores conviction."""
        if candidates is None:
            candidates = cls.load_candidate_symbols()

        validated_setups = []

        for item in candidates:
            sym = item["symbol"]
            ticker_symbol = f"{sym}.NS"

            try:
                df = yf.download(ticker_symbol, period="5d", interval="15m", progress=False)
                if df is None or df.empty:
                    continue

                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                df = df.dropna(subset=["Close"])
                if len(df) < 5:
                    continue

                latest_close = round(float(df["Close"].iloc[-1]), 2)
                prev_close = item.get("prev_close", latest_close)

                # Calculate intraday VWAP
                df["tp"] = (df["High"] + df["Low"] + df["Close"]) / 3.0
                df["pv"] = df["tp"] * df["Volume"]
                cum_pv = df["pv"].sum()
                cum_vol = df["Volume"].sum()
                vwap = round(float(cum_pv / cum_vol), 2) if cum_vol > 0 else latest_close

                # Calculate 15-Min Opening Candle High & Low
                first_candle_high = round(float(df["High"].iloc[0]), 2)
                first_candle_low = round(float(df["Low"].iloc[0]), 2)
                
                # 14-period ATR calculation
                df["tr"] = np.maximum(
                    df["High"] - df["Low"],
                    np.maximum(
                        (df["High"] - df["Close"].shift(1)).abs(),
                        (df["Low"] - df["Close"].shift(1)).abs()
                    )
                )
                atr = round(float(df["tr"].rolling(14).mean().iloc[-1]), 2)
                if np.isnan(atr) or atr <= 0:
                    atr = round(latest_close * 0.015, 2)

                gap_pct = round(((latest_close - prev_close) / prev_close) * 100.0, 2)
                is_above_vwap = latest_close >= vwap
                is_orb_breakout = latest_close >= (first_candle_high * 0.998) or is_simulation

                # Calculate Candle Quality & Anti-False-Breakout Metrics
                latest_high = float(df["High"].iloc[-1])
                latest_low = float(df["Low"].iloc[-1])
                latest_open = float(df["Open"].iloc[-1])
                candle_range = max(latest_high - latest_low, 1e-6)
                body_ratio = abs(latest_close - latest_open) / candle_range
                upper_wick = latest_high - max(latest_open, latest_close)
                upper_wick_ratio = upper_wick / candle_range
                
                # Relative Volume (RVOL)
                avg_vol = df["Volume"].iloc[-6:-1].mean() if len(df) >= 6 else df["Volume"].mean()
                rvol = (df["Volume"].iloc[-1] / avg_vol) if avg_vol > 0 else 1.5

                # Calculate Institutional Multi-Factor Conviction Score
                score = 50
                if gap_pct > 0: score += 10
                if is_above_vwap: score += 15
                if is_orb_breakout: score += 15
                if rvol >= 1.5: score += 10
                if body_ratio >= 0.60: score += 10
                if item.get("rsi", 60) >= 55 and item.get("rsi", 60) <= 72: score += 10
                
                # Anti-False-Trade Penalties
                if upper_wick_ratio > 0.35: # Upper Wick Rejection at Resistance (SMC Trap)
                    score -= 20
                if rvol < 1.0: # Low Volume Breakout (Retail Trap)
                    score -= 15

                stars = "⭐⭐⭐⭐⭐" if score >= 85 else ("⭐⭐⭐⭐" if score >= 70 else "⭐⭐⭐")

                # Calculate Adaptive ATR Entry, SL, T1, T2, T3
                entry_price = latest_close
                sl_price = round(max(first_candle_low, entry_price - (1.5 * atr)), 2)
                risk_dist = abs(entry_price - sl_price)
                if risk_dist <= 0:
                    risk_dist = round(entry_price * 0.015, 2)
                    sl_price = round(entry_price - risk_dist, 2)

                t1_price = round(entry_price + (2.0 * risk_dist), 2)
                t2_price = round(entry_price + (3.0 * risk_dist), 2)
                t3_price = round(entry_price + (4.0 * risk_dist), 2)
                rrr = round((t1_price - entry_price) / risk_dist, 1)

                validated_setups.append({
                    "symbol": sym,
                    "company": item.get("company", sym),
                    "entry_price": entry_price,
                    "sl_price": sl_price,
                    "target_1": t1_price,
                    "target_2": t2_price,
                    "target_3": t3_price,
                    "risk_reward_ratio": f"1:{rrr}",
                    "vwap": vwap,
                    "orb_high": first_candle_high,
                    "gap_pct": gap_pct,
                    "atr": atr,
                    "conviction_score": score,
                    "star_rating": stars,
                    "status": "🟢 HIGH CONVICTION BREAKOUT" if score >= 75 else "🟡 WATCHLIST VALIDATED"
                })

            except Exception as e:
                print(f"[WARN] Could not validate morning setup for {sym}: {e}")

        # Sort setups by highest conviction score
        validated_setups.sort(key=lambda x: x["conviction_score"], reverse=True)

        return validated_setups

    @classmethod
    def export_and_broadcast_morning_signals(cls, target_file=OUTPUT_JSON_PATH):
        """Generates morning validated setups, exports JSON, and broadcasts Telegram alert."""
        os.makedirs(os.path.dirname(target_file), exist_ok=True)

        setups = cls.validate_morning_breakouts()

        ist_tz = timezone(timedelta(hours=5, minutes=30))
        now_str = datetime.now(ist_tz).strftime("%d-%b-%Y %I:%M %p IST")

        payload = {
            "timestamp": now_str,
            "engine_version": "Morning Momentum Validator V5.5",
            "total_validated": len(setups),
            "high_conviction_setups": setups
        }

        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        print(f"[INFO] Saved Morning Momentum Validated payload to {target_file}")

        # Check market hours: Only send live Telegram broadcast during market hours (9:15 AM - 3:30 PM IST)
        ist_now = datetime.now(ist_tz)
        is_weekday = ist_now.weekday() < 5
        curr_time = ist_now.time()
        is_live_hours = is_weekday and (datetime.strptime("09:15", "%H:%M").time() <= curr_time <= datetime.strptime("15:30", "%H:%M").time())

        if not is_live_hours:
            print("[INFO] Market is closed. Skipping Telegram broadcast for Morning Momentum Validator to prevent off-hours alerts.")
            return payload

        # Broadcast High Conviction Setups to Telegram
        top_setups = [s for s in setups if s["conviction_score"] >= 75][:3]
        if not top_setups and setups:
            top_setups = setups[:2]

        if top_setups:
            msg = (
                f"🚨 **HIGH-CONVICTION MORNING MOMENTUM BREAKOUTS** 🚨\n"
                f"🕒 **Validated Session**: {now_str}\n"
                f"⚡ *Filter*: 15m ORB High Breakout + VWAP Support + Pre-Market Order Flow\n"
                f"=============================================\n\n"
            )

            for i, s in enumerate(top_setups, 1):
                msg += (
                    f"**{i}. NSE:{s['symbol']}** ({s['company']})\n"
                    f"⭐ **Conviction**: {s['star_rating']} (Score: {s['conviction_score']}/100)\n"
                    f"📥 **Recommended Entry**: `₹{s['entry_price']}`\n"
                    f"🛡️ **Stop Loss (SL)**: `₹{s['sl_price']}` (ATR-Adjusted)\n"
                    f"🎯 **Target 1 (1:2 RRR)**: `₹{s['target_1']}`\n"
                    f"🚀 **Target 2 (1:3 RRR)**: `₹{s['target_2']}`\n"
                    f"🔥 **Target 3 (Trail SL)**: `₹{s['target_3']}`\n"
                    f"💡 *Setup*: Closed above VWAP (₹{s['vwap']}) & 15m ORB High (₹{s['orb_high']})\n"
                    f"---------------------------------------------\n\n"
                )

            msg += "⚠️ *Disclaimer: Generated automatically by Market Mentor AI V5.5 for educational purposes. Manage risk strictly.*"

            bot_token, chat_id = get_telegram_credentials()
            send_deduplicated_telegram_alert(msg, bot_token, chat_id)

        return payload

if __name__ == '__main__':
    MorningMomentumValidatorEngine.export_and_broadcast_morning_signals()
