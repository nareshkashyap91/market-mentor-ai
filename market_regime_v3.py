import numpy as np
import pandas as pd

class MarketRegimeV3Engine:
    """Central Market Regime Engine V3.0.
    Classifies market state into 10 explicit Regimes:
    1. TRENDING_BULLISH
    2. TRENDING_BEARISH
    3. SIDEWAYS
    4. HIGH_VOLATILITY
    5. LOW_VOLATILITY
    6. BREAKOUT
    7. BREAKDOWN
    8. MEAN_REVERSION
    9. EVENT_RISK
    10. UNSAFE
    """

    REGIMES = [
        "TRENDING_BULLISH", "TRENDING_BEARISH", "SIDEWAYS",
        "HIGH_VOLATILITY", "LOW_VOLATILITY", "BREAKOUT",
        "BREAKDOWN", "MEAN_REVERSION", "EVENT_RISK", "UNSAFE"
    ]

    @classmethod
    def detect_regime(cls, nifty_spot=24580.25, vwap=24550.0, ema20=24500.0, ema50=24400.0, ema200=24000.0,
                      adx=28.4, vix_val=13.20, rvol=1.5, is_event_day=False):
        """Centralized regime detector returning REGIME, REGIME_CONFIDENCE, and REGIME_REASON."""
        reasons = []

        if is_event_day:
            return {
                "regime": "EVENT_RISK",
                "regime_confidence": 95.0,
                "regime_reason": "High-impact economic news/event scheduled today. Trades subject to event lockout.",
                "is_trade_allowed": False
            }

        if vix_val >= 25.0:
            return {
                "regime": "UNSAFE",
                "regime_confidence": 90.0,
                "regime_reason": f"Extreme volatility risk (India VIX {vix_val:.2f} >= 25.0). Trading halted for safety.",
                "is_trade_allowed": False
            }

        is_bullish_alignment = nifty_spot > vwap and ema20 > ema50 > ema200
        is_bearish_alignment = nifty_spot < vwap and ema20 < ema50 < ema200

        if vix_val >= 20.0:
            regime = "HIGH_VOLATILITY"
            confidence = 85.0
            reasons.append(f"Elevated India VIX ({vix_val:.2f}) indicates high option premium volatility.")
            is_trade_allowed = True
        elif nifty_spot > vwap * 1.008 and rvol >= 1.8:
            regime = "BREAKOUT"
            confidence = 88.0
            reasons.append("Strong intraday price expansion above VWAP with high volume.")
            is_trade_allowed = True
        elif nifty_spot < vwap * 0.992 and rvol >= 1.8:
            regime = "BREAKDOWN"
            confidence = 88.0
            reasons.append("Sharpe breakdown below VWAP with high relative volume.")
            is_trade_allowed = True
        elif is_bullish_alignment and adx >= 22.0:
            regime = "TRENDING_BULLISH"
            confidence = min(95.0, 70.0 + (adx * 0.8))
            reasons.append("15m structure bullish, price above VWAP, EMA alignment positive (EMA20 > EMA50 > EMA200), ADX confirms trend.")
            is_trade_allowed = True
        elif is_bearish_alignment and adx >= 22.0:
            regime = "TRENDING_BEARISH"
            confidence = min(95.0, 70.0 + (adx * 0.8))
            reasons.append("15m structure bearish, price below VWAP, EMA alignment negative, ADX confirms downtrend.")
            is_trade_allowed = True
        elif vix_val <= 11.5 and adx < 18.0:
            regime = "LOW_VOLATILITY"
            confidence = 80.0
            reasons.append(f"Ultra-low India VIX ({vix_val:.2f}) and low ADX ({adx:.1f}). Options buying non-favorable.")
            is_trade_allowed = True
        elif abs(nifty_spot - vwap) / vwap * 100.0 > 1.8:
            regime = "MEAN_REVERSION"
            confidence = 78.0
            reasons.append("Price significantly extended from VWAP benchmark. High probability of mean reversion.")
            is_trade_allowed = True
        else:
            regime = "SIDEWAYS"
            confidence = 75.0
            reasons.append("Market oscillating in a tight consolidation range around VWAP with low ADX.")
            is_trade_allowed = True

        return {
            "regime": regime,
            "regime_confidence": round(confidence, 1),
            "regime_reason": " ".join(reasons),
            "is_trade_allowed": is_trade_allowed
        }

# Helper function
def get_regime_v3(nifty_spot=24580.25, vwap=24550.0, ema20=24500.0, ema50=24400.0, ema200=24000.0, adx=28.4, vix_val=13.20):
    return MarketRegimeV3Engine.detect_regime(nifty_spot, vwap, ema20, ema50, ema200, adx, vix_val)
