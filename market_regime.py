import os
import sys
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timezone, timedelta
from data_quality import DataQualityEngine, LIVE_DATA, MOCK_DATA

class MarketRegimeEngine:
    """Institutional Market Regime & Volatility Analysis Engine.
    Calculates ADX Trend Intensity, Volatility Percentile, and Regime Confidence Scoring.
    """

    @staticmethod
    def calculate_adx(df, period=14):
        """Calculates Average Directional Index (ADX) measuring trend strength."""
        if df is None or len(df) < period * 2:
            return 15.0, "WEAK"  # Fallback

        df = df.copy()
        df['High-Low'] = df['High'] - df['Low']
        df['High-PrevClose'] = (df['High'] - df['Close'].shift(1)).abs()
        df['Low-PrevClose'] = (df['Low'] - df['Close'].shift(1)).abs()

        df['TR'] = df[['High-Low', 'High-PrevClose', 'Low-PrevClose']].max(axis=1)

        df['PlusDM'] = np.where(
            (df['High'] - df['High'].shift(1)) > (df['Low'].shift(1) - df['Low']),
            np.maximum(df['High'] - df['High'].shift(1), 0), 0
        )
        df['MinusDM'] = np.where(
            (df['Low'].shift(1) - df['Low']) > (df['High'] - df['High'].shift(1)),
            np.maximum(df['Low'].shift(1) - df['Low'], 0), 0
        )

        tr_smooth = df['TR'].rolling(period).sum()
        plus_di = 100 * (df['PlusDM'].rolling(period).sum() / tr_smooth)
        minus_di = 100 * (df['MinusDM'].rolling(period).sum() / tr_smooth)

        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        adx = dx.rolling(period).mean().iloc[-1]

        if np.isnan(adx):
            adx = 15.0

        adx_val = round(float(adx), 1)

        if adx_val >= 25.0:
            intensity = "STRONG TREND"
        elif adx_val >= 20.0:
            intensity = "MODERATE TREND"
        else:
            intensity = "WEAK / SIDEWAYS"

        return adx_val, intensity

    @staticmethod
    def calculate_volatility_percentile(vix_val, vix_df=None):
        """Calculates VIX percentile relative to historical 252-session range."""
        if vix_df is not None and not vix_df.empty and len(vix_df) > 20:
            low_vix = vix_df['Low'].min()
            high_vix = vix_df['High'].max()
            if high_vix > low_vix:
                percentile = ((vix_val - low_vix) / (high_vix - low_vix)) * 100.0
                return round(float(np.clip(percentile, 0, 100)), 1)
        
        # Fallback estimation
        estimated_percentile = max(0.0, min(100.0, ((vix_val - 10.0) / 15.0) * 100.0))
        return round(float(estimated_percentile), 1)

    @staticmethod
    def compute_regime_confidence(spot, vwap, adx_val, pcr, rsi_val=60):
        """Computes a quantitative Regime Confidence Score (0% to 100%)."""
        confidence = 50.0 # Base neutral

        # ADX trend weight (+25 max)
        if adx_val >= 25:
            confidence += 25.0
        elif adx_val >= 20:
            confidence += 15.0

        # VWAP Distance weight (+15 max)
        vwap_dist = abs((spot - vwap) / vwap) * 100.0
        if vwap_dist > 0.3:
            confidence += 15.0
        elif vwap_dist > 0.1:
            confidence += 10.0

        # PCR Extreme Alignment (+10 max)
        if pcr >= 1.2 or pcr <= 0.75:
            confidence += 10.0

        return round(min(100.0, max(20.0, confidence)), 1)

    @classmethod
    def analyze_regime(cls, df_index, vix_val=13.5, pcr=1.0, is_mock=False):
        """Analyzes 15m index candles and returns complete Market Regime Analysis."""
        data_tag = MOCK_DATA if is_mock else LIVE_DATA

        if df_index is None or df_index.empty or len(df_index) < 5:
            return {
                "regime": "🟡 SIDEWAYS_RANGEBOUND",
                "adx": 15.0,
                "trend_intensity": "WEAK / SIDEWAYS",
                "volatility_percentile": 30.0,
                "confidence_score": 50.0,
                "spot_price": 24500.0,
                "vwap": 24500.0,
                "pcr": pcr,
                "vix": vix_val,
                "data_type": data_tag
            }

        spot = float(df_index['Close'].iloc[-1])

        # VWAP
        today_df = df_index[df_index.index.date == df_index.index[-1].date()] if hasattr(df_index.index, 'date') else df_index
        if not today_df.empty:
            tp_vol = ((today_df['High'] + today_df['Low'] + today_df['Close']) / 3) * today_df['Volume']
            tot_vol = today_df['Volume'].sum()
            vwap = float(tp_vol.sum() / tot_vol) if tot_vol > 0 else spot
        else:
            vwap = spot

        # ADX & Trend Intensity
        adx_val, trend_intensity = cls.calculate_adx(df_index)

        # Volatility Percentile
        vix_percentile = cls.calculate_volatility_percentile(vix_val)

        # Confidence Score
        confidence_score = cls.compute_regime_confidence(spot, vwap, adx_val, pcr)

        # Formal Classification Logic
        if adx_val >= 20.0 and spot > vwap * 1.001 and pcr >= 1.05:
            regime = "🚀 TRENDING_BULLISH"
        elif adx_val >= 20.0 and spot < vwap * 0.999 and pcr <= 0.85:
            regime = "🔻 TRENDING_BEARISH"
        elif vix_val >= 18.0:
            regime = "⚡ VOLATILITY_EXPANSION"
        else:
            regime = "🟡 SIDEWAYS_RANGEBOUND"

        return {
            "regime": regime,
            "adx": adx_val,
            "trend_intensity": trend_intensity,
            "volatility_percentile": vix_percentile,
            "confidence_score": confidence_score,
            "spot_price": round(spot, 2),
            "vwap": round(vwap, 2),
            "pcr": float(pcr),
            "vix": float(vix_val),
            "data_type": data_tag
        }

# Helper function
def get_market_regime_analysis(df_index, vix_val=13.5, pcr=1.0, is_mock=False):
    return MarketRegimeEngine.analyze_regime(df_index, vix_val, pcr, is_mock=is_mock)
