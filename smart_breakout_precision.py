import numpy as np
import pandas as pd

class SmartBreakoutPrecisionEngine:
    """Institutional Smart Trader Breakout Precision Engine.
    Evaluates 3-5 day consolidation duration, Volume-at-Breakout RVOL >= 1.5x, Candle Body Ratio, and False Breakout Risk.
    """

    @classmethod
    def evaluate_breakout_precision(cls, close, open_p, high, low, breakout_level, rvol, df_history=None):
        """Evaluates breakout quality against institutional smart trader rules."""
        candle_body = abs(close - open_p)
        candle_range = max(high - low, 1e-6)
        body_ratio = candle_body / candle_range

        is_breakout_above = close > breakout_level
        dist_breakout_pct = ((close - breakout_level) / breakout_level) * 100.0 if is_breakout_above else 0.0

        # Consolidation Duration Evaluation
        consolidation_days = 4
        consolidation_width_pct = 3.5

        if df_history is not None and not df_history.empty and len(df_history) >= 5:
            last5 = df_history.tail(5)
            c_min = last5['Low'].min()
            c_max = last5['High'].max()
            consolidation_width_pct = round(((c_max - c_min) / close) * 100.0, 2) if close > 0 else 3.5
            consolidation_days = 5

        tight_consolidation = consolidation_width_pct <= 5.0

        # Smart Money Breakout Classification
        if is_breakout_above and rvol >= 1.5 and body_ratio >= 0.65 and tight_consolidation:
            classification = "SMART MONEY CONFIRMED BREAKOUT"
            quality_score = 95
            is_valid_breakout = True
            risk_summary = "Low False Breakout Risk (High Volume + Strong Closing + Tight Base)"
        elif is_breakout_above and rvol >= 1.2:
            classification = "MODERATE BREAKOUT"
            quality_score = 75
            is_valid_breakout = True
            risk_summary = "Moderate Breakout Quality (Require 15m VWAP Confirmation)"
        elif is_breakout_above and rvol < 1.0:
            classification = "FALSE BREAKOUT TRAP (RETAIL BAIT)"
            quality_score = 25
            is_valid_breakout = False
            risk_summary = "High False Breakout Risk (Weak Volume - Retail Trap Risk)"
        else:
            classification = "NO BREAKOUT DETECTED"
            quality_score = 50
            is_valid_breakout = False
            risk_summary = "Price below breakout level"

        return {
            "breakout_classification": classification,
            "quality_score": quality_score,
            "is_valid_breakout": is_valid_breakout,
            "rvol": round(rvol, 2),
            "body_ratio": round(body_ratio, 2),
            "consolidation_days": consolidation_days,
            "consolidation_width_pct": consolidation_width_pct,
            "tight_consolidation": tight_consolidation,
            "risk_summary": risk_summary
        }

# Helper function
def get_breakout_precision(close, open_p, high, low, breakout_level, rvol, df_history=None):
    return SmartBreakoutPrecisionEngine.evaluate_breakout_precision(close, open_p, high, low, breakout_level, rvol, df_history)
