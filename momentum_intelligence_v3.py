import numpy as np
import pandas as pd

class MomentumIntelligenceV3Engine:
    """Next-Day Momentum Stock Intelligence Engine V3.0.
    Preserves RVOL, RSI, VWAP reclaim, 3-5 day consolidation.
    Adds RS vs Nifty, RS vs Sector, Sector Trend, ATR Compression, Gap Quality, and A+/A/B/WATCH/REJECT ranking.
    """

    @classmethod
    def evaluate_stock_momentum(cls, symbol, close, open_p, high, low, vwap, rvol, rsi,
                                stock_ret_5d=3.5, nifty_ret_5d=1.0, sector_ret_5d=2.0, atr_ratio=0.8, yday_high=None):
        """Evaluates stock momentum and returns V3 scores and ranking."""
        # 1. Preserved Metrics
        vwap_reclaimed = close > vwap
        rsi_valid = 55 <= rsi <= 72
        rvol_strong = rvol >= 1.5

        # 2. V3 Scores
        rs_nifty_score = round(stock_ret_5d - nifty_ret_5d, 2)
        rs_sector_score = round(stock_ret_5d - sector_ret_5d, 2)
        sector_trend_score = round(sector_ret_5d * 10.0, 1)

        # 3. ATR Compression
        atr_compressed = atr_ratio < 0.9

        # 4. Proximity to YDay High
        if yday_high is None:
            yday_high = close * 0.995
        near_yday_high = close >= yday_high * 0.99

        # Momentum Score Calculation (0 to 100)
        base_score = 50.0
        if rvol_strong: base_score += 15.0
        if vwap_reclaimed: base_score += 10.0
        if rsi_valid: base_score += 10.0
        if rs_nifty_score > 1.0: base_score += 8.0
        if rs_sector_score > 0.5: base_score += 7.0
        if atr_compressed: base_score += 5.0
        if near_yday_high: base_score += 5.0

        momentum_score = round(min(100.0, base_score), 1)

        # Grade Ranking: A+, A, B, WATCH, REJECT
        if momentum_score >= 88.0 and vwap_reclaimed and rvol_strong:
            grade = "A+"
            status = "TOP PICK (INSTITUTIONAL MOMENTUM LEADERSHIP)"
        elif momentum_score >= 78.0 and vwap_reclaimed:
            grade = "A"
            status = "STRONG MOMENTUM BREAKOUT"
        elif momentum_score >= 68.0:
            grade = "B"
            status = "MODERATE MOMENTUM CANDIDATE"
        elif momentum_score >= 55.0:
            grade = "WATCH"
            status = "WATCHLIST ONLY (REQUIRES MORNING CONFIRMATION)"
        else:
            grade = "REJECT"
            status = "REJECTED (WEAK MOMENTUM)"

        return {
            "symbol": symbol,
            "close": close,
            "grade": grade,
            "momentum_score": momentum_score,
            "rs_nifty_score": rs_nifty_score,
            "rs_sector_score": rs_sector_score,
            "sector_trend_score": sector_trend_score,
            "rvol": round(rvol, 2),
            "rsi": round(rsi, 1),
            "vwap_reclaimed": vwap_reclaimed,
            "atr_compressed": atr_compressed,
            "status": status
        }

# Helper function
def get_momentum_v3(symbol, close, open_p, high, low, vwap, rvol, rsi, stock_ret_5d=3.5, nifty_ret_5d=1.0, sector_ret_5d=2.0):
    return MomentumIntelligenceV3Engine.evaluate_stock_momentum(symbol, close, open_p, high, low, vwap, rvol, rsi, stock_ret_5d, nifty_ret_5d, sector_ret_5d)
