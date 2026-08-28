import numpy as np

class IntradayOrbVwapPrecisionEngine:
    """Intraday ORB (Opening Range Breakout) & VWAP Precision Engine.
    Validates first 15m ORB High/Low breakouts, VWAP support, and VWAP Overextension Filters.
    """

    @classmethod
    def evaluate_orb_vwap(cls, close, vwap, atr, orb_high, orb_low):
        """Evaluates intraday ORB breakout and VWAP extension safety."""
        is_above_orb_high = close > orb_high
        is_above_vwap = close > vwap

        dist_vwap_atr = (close - vwap) / max(atr, 1e-6)
        is_overextended = dist_vwap_atr > 2.5

        if is_above_orb_high and is_above_vwap and not is_overextended:
            status = "CONFIRMED ORB LONG BREAKOUT (VWAP SUPPORTED)"
            bias = "BULLISH"
            score = 90
            is_trade_allowed = True
        elif is_above_orb_high and is_overextended:
            status = "CHASE RISK (EXTENDED > 2.5x ATR ABOVE VWAP)"
            bias = "CAUTION"
            score = 45
            is_trade_allowed = False
        elif close < orb_low and close < vwap:
            status = "CONFIRMED ORB SHORT BREAKDOWN (BEARISH VWAP)"
            bias = "BEARISH"
            score = 85
            is_trade_allowed = True
        else:
            status = "INSIDE OPENING RANGE (WAIT FOR ORB BREAKOUT)"
            bias = "NEUTRAL"
            score = 50
            is_trade_allowed = False

        return {
            "orb_status": status,
            "intraday_bias": bias,
            "precision_score": score,
            "is_trade_allowed": is_trade_allowed,
            "dist_vwap_atr": round(dist_vwap_atr, 2),
            "orb_high": orb_high,
            "orb_low": orb_low
        }

# Helper function
def evaluate_intraday_precision(close, vwap, atr, orb_high, orb_low):
    return IntradayOrbVwapPrecisionEngine.evaluate_orb_vwap(close, vwap, atr, orb_high, orb_low)
