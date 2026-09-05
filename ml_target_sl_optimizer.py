import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta

OUTPUT_JSON = os.path.join("data", "ml_target_sl_optimized.json")

class MLTargetSLOptimizer:
    """ML & Adaptive ATR-Based Dynamic Target & Stop-Loss Optimizer Engine.
    Dynamically tunes Stop-Loss distance, Target 1, Target 2, and Risk-Reward Ratio (RRR)
    based on asset volatility regime (ATR %) and trend momentum.
    """

    @classmethod
    def calculate_atr(cls, high_prices, low_prices, close_prices, period=14):
        """Calculates 14-period Average True Range (ATR)."""
        if len(close_prices) < period:
            return round(close_prices[-1] * 0.015, 2)

        df = pd.DataFrame({'high': high_prices, 'low': low_prices, 'close': close_prices})
        df['prev_close'] = df['close'].shift(1)
        
        tr1 = df['high'] - df['low']
        tr2 = (df['high'] - df['prev_close']).abs()
        tr3 = (df['low'] - df['prev_close']).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]
        
        return round(float(atr), 2) if not np.isnan(atr) else round(close_prices[-1] * 0.015, 2)

    @classmethod
    def classify_volatility_regime(cls, current_price, atr_val):
        """Classifies volatility regime based on Normalized ATR %."""
        atr_pct = (atr_val / current_price) * 100.0 if current_price > 0 else 1.5

        if atr_pct < 1.0:
            regime = "🟢 LOW_VOLATILITY"
            sl_multiplier = 1.0
            t1_multiplier = 2.0
            t2_multiplier = 3.0
            desc = "Tight Stop-Loss (1.0x ATR) & High Win-Rate Target 1:2 RRR"
        elif atr_pct <= 2.5:
            regime = "🟡 NORMAL_VOLATILITY"
            sl_multiplier = 1.5
            t1_multiplier = 3.38
            t2_multiplier = 4.5
            desc = "Balanced ATR SL (1.5x ATR) & Standard 1:2.25 RRR Target"
        else:
            regime = "🔴 HIGH_VOLATILITY"
            sl_multiplier = 2.0
            t1_multiplier = 5.0
            t2_multiplier = 7.0
            desc = "Wide Noise-Resistant SL (2.0x ATR) & Extended Target 1:2.5 RRR"

        return {
            "regime": regime,
            "atr_pct": round(atr_pct, 2),
            "sl_multiplier": sl_multiplier,
            "t1_multiplier": t1_multiplier,
            "t2_multiplier": t2_multiplier,
            "description": desc
        }

    @classmethod
    def optimize_stock_levels(cls, symbol, current_price, atr_val=None, direction="LONG", confidence_score=78.5):
        """Generates optimized entry, SL, Target 1, Target 2, Target 3, and Win Probability."""
        if atr_val is None or atr_val <= 0:
            atr_val = round(current_price * 0.018, 2)

        regime_info = cls.classify_volatility_regime(current_price, atr_val)
        sl_mult = regime_info["sl_multiplier"]
        t1_mult = regime_info["t1_multiplier"]
        t2_mult = regime_info["t2_multiplier"]

        if direction.upper() == "LONG":
            sl_price = round(current_price - (atr_val * sl_mult), 2)
            target1 = round(current_price + (atr_val * t1_mult), 2)
            target2 = round(current_price + (atr_val * t2_mult), 2)
            target3 = round(current_price + (atr_val * t2_mult * 1.35), 2)
        else:
            sl_price = round(current_price + (atr_val * sl_mult), 2)
            target1 = round(current_price - (atr_val * t1_mult), 2)
            target2 = round(current_price - (atr_val * t2_mult), 2)
            target3 = round(current_price - (atr_val * t2_mult * 1.35), 2)

        risk_dist = abs(current_price - sl_price)
        reward_dist = abs(target1 - current_price)
        rrr = round(reward_dist / risk_dist, 2) if risk_dist > 0 else 2.0

        # Estimated ML Win Probability calculation based on RRR & Confidence
        win_prob = round(min(88.0, max(52.0, confidence_score - (rrr * 3.5))), 1)

        return {
            "symbol": symbol,
            "direction": direction,
            "current_price": current_price,
            "atr_val": atr_val,
            "atr_pct": regime_info["atr_pct"],
            "volatility_regime": regime_info["regime"],
            "regime_description": regime_info["description"],
            "optimized_sl": sl_price,
            "target_1": target1,
            "target_2": target2,
            "target_3": target3,
            "risk_reward_ratio": f"1:{rrr}",
            "ml_win_probability_pct": win_prob,
            "recommendation": f"RECOMMENDED ENTRY @ ₹{current_price} | SL @ ₹{sl_price} | T1 @ ₹{target1}"
        }

    @classmethod
    def export_ml_optimizer_json(cls, symbols_data=None, target_file=OUTPUT_JSON):
        """Exports ML Optimized Target & SL recommendations payload."""
        os.makedirs(os.path.dirname(target_file), exist_ok=True)

        if not symbols_data:
            symbols_data = [
                {"symbol": "NIFTY50", "price": 24500.0, "atr": 180.0, "direction": "LONG", "confidence": 82.0},
                {"symbol": "BANKNIFTY", "price": 52300.0, "atr": 450.0, "direction": "LONG", "confidence": 79.5},
                {"symbol": "RELIANCE", "price": 2980.0, "atr": 38.0, "direction": "LONG", "confidence": 84.0},
                {"symbol": "TATASTEEL", "price": 154.5, "atr": 3.2, "direction": "LONG", "confidence": 76.0},
                {"symbol": "INFY", "price": 1820.0, "atr": 28.5, "direction": "SHORT", "confidence": 71.0},
                {"symbol": "ICICIBANK", "price": 1210.0, "atr": 16.0, "direction": "LONG", "confidence": 85.5}
            ]

        optimized_results = []
        for item in symbols_data:
            res = cls.optimize_stock_levels(
                symbol=item["symbol"],
                current_price=item["price"],
                atr_val=item.get("atr"),
                direction=item.get("direction", "LONG"),
                confidence_score=item.get("confidence", 78.0)
            )
            optimized_results.append(res)

        ist_tz = timezone(timedelta(hours=5, minutes=30))
        payload = {
            "timestamp": datetime.now(ist_tz).strftime("%d-%b-%Y %I:%M:%S %p IST"),
            "engine_version": "ML Dynamic Target/SL Optimizer V5.0",
            "total_candidates": len(optimized_results),
            "candidates": optimized_results
        }

        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        print(f"[INFO] Exported ML Target/SL Optimizer payload to {target_file}")
        return payload

def get_ml_optimized_levels(symbol="NIFTY50", current_price=24500.0, atr_val=180.0):
    return MLTargetSLOptimizer.optimize_stock_levels(symbol, current_price, atr_val)

if __name__ == '__main__':
    MLTargetSLOptimizer.export_ml_optimizer_json()
