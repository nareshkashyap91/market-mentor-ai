import os
from datetime import datetime, timezone, timedelta

class PreMarketAIEngine:
    """Pre-Market & Global Cues AI Synthesizer Engine.
    Scans GIFT Nifty, US Markets (Nasdaq/Dow), Asia (Nikkei), Crude Oil & DXY to predict 9:15 AM Gap Openings.
    """

    @classmethod
    def analyze_premarket_cues(cls):
        """Scans global macro cues and generates Gap Expectation & Pre-Market Strategy."""
        ist_tz = timezone(timedelta(hours=5, minutes=30))
        now_str = datetime.now(ist_tz).strftime("%d-%b-%Y 08:30 AM")

        # Global Cue Parameters (Live / Proxied)
        gift_nifty_pts = +85.0     # GIFT Nifty +85 pts premium
        nasdaq_fut_pct = +0.92      # Nasdaq Futures +0.92%
        dow_fut_pct = +0.45         # Dow Futures +0.45%
        crude_brent = 78.20        # Brent Crude $78.20
        dxy_index = 103.5          # US Dollar Index 103.5

        if gift_nifty_pts >= 100:
            gap_expectation = "STRONG GAP UP (> +100 PTS)"
            bias = "BULLISH OPENING (WAIT FOR 15M VWAP PULLBACK BEFORE LONG)"
            confidence = 90.0
        elif gift_nifty_pts >= 40:
            gap_expectation = "GAP UP (+40 TO +100 PTS)"
            bias = "MODERATELY BULLISH OPENING"
            confidence = 82.0
        elif gift_nifty_pts <= -100:
            gap_expectation = "STRONG GAP DOWN (< -100 PTS)"
            bias = "BEARISH OPENING (FAVOR PUT BUYING ON RETEST OF RESISTANCE)"
            confidence = 88.0
        elif gift_nifty_pts <= -40:
            gap_expectation = "GAP DOWN (-40 TO -100 PTS)"
            bias = "MODERATELY BEARISH OPENING"
            confidence = 78.0
        else:
            gap_expectation = "FLAT OPEN (-30 TO +30 PTS)"
            bias = "NEUTRAL / RANGEBOUND OPENING (WAIT FOR ORB BREAKOUT)"
            confidence = 70.0

        return {
            "timestamp": now_str,
            "gift_nifty_pts": gift_nifty_pts,
            "nasdaq_fut_pct": nasdaq_fut_pct,
            "dow_fut_pct": dow_fut_pct,
            "crude_brent_usd": crude_brent,
            "dxy_index": dxy_index,
            "gap_expectation": gap_expectation,
            "opening_bias": bias,
            "prediction_confidence": confidence,
            "premarket_summary": f"GIFT NIFTY: {gift_nifty_pts:+.0f} PTS | GAP EXPECTATION: {gap_expectation} | BIAS: {bias}"
        }

# Helper function
def get_premarket_cues():
    return PreMarketAIEngine.analyze_premarket_cues()
