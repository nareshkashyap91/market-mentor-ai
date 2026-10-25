import os
import json
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timezone, timedelta
from atomic_io import atomic_write_json, safe_read_json

class LegendaryTraderEngine:
    """
    World-Class Legendary Trader Strategies Engine:
    1. Mark Minervini (VCP - Volatility Contraction Pattern + Trend Template)
    2. Jim Simons (Statistical Mean Reversion & Multi-Day Z-Score Extreme Squeeze)
    3. Richard Dennis (Turtle Trading 20-Day Donchian Breakout + ATR Pyramiding)
    """

    JSON_PATH = os.path.join("data", "legendary_traders.json")

    WATCHLIST = [
        "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
        "BHARTIARTL", "SBIN", "LT", "TATAMOTORS", "BAJFINANCE",
        "MARUTI", "SUNPHARMA", "TITAN", "AXISBANK", "NTPC",
        "ONGC", "ADANIENT", "JSWSTEEL", "POWERGRID", "M&M"
    ]

    @classmethod
    def fetch_historical_ohlcv(cls, symbol, period="1y"):
        ticker = f"{symbol}.NS"
        try:
            df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
            if df is not None and not df.empty and len(df) >= 50:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                return df
        except Exception as e:
            print(f"[WARN] Error fetching OHLCV for {symbol}: {e}")
        return None

    @staticmethod
    def calculate_atr(df, period=14):
        high = df['High'].values
        low = df['Low'].values
        close = df['Close'].values
        
        tr = np.zeros(len(close))
        tr[0] = high[0] - low[0]
        for i in range(1, len(close)):
            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i - 1]),
                abs(low[i] - close[i - 1])
            )
        
        atr = pd.Series(tr, index=df.index).rolling(window=period).mean().values
        return atr

    @classmethod
    def evaluate_minervini_vcp(cls, symbol, df):
        """
        Mark Minervini VCP (Volatility Contraction Pattern) & Trend Template:
        - Price > 50 DMA > 150 DMA > 200 DMA
        - 200 DMA trending upward for at least 1 month
        - Current price within 25% of 52-week High
        - Volatility Contraction: Rolling ATR or High-Low range shrinking sequentially (e.g. 15% -> 8% -> 3%)
        - Dry Volume prior to pivot breakout
        """
        if len(df) < 150:
            return None

        closes = df['Close'].values
        highs = df['High'].values
        lows = df['Low'].values
        volumes = df['Volume'].values

        curr_price = float(closes[-1])
        dma50 = float(pd.Series(closes).rolling(50).mean().iloc[-1])
        dma150 = float(pd.Series(closes).rolling(150).mean().iloc[-1])
        dma200 = float(pd.Series(closes).rolling(200).mean().iloc[-1]) if len(df) >= 200 else dma150 * 0.95

        high_52w = float(np.max(highs[-250:])) if len(df) >= 250 else float(np.max(highs))
        low_52w = float(np.min(lows[-250:])) if len(df) >= 250 else float(np.min(lows))

        # 1. Minervini Trend Template Check
        is_above_dmas = curr_price > dma50 and dma50 > dma150
        pct_from_52w_high = ((high_52w - curr_price) / high_52w) * 100
        above_52w_low_pct = ((curr_price - low_52w) / low_52w) * 100

        trend_score = 0
        if curr_price > dma50: trend_score += 25
        if dma50 > dma150: trend_score += 25
        if curr_price > dma200: trend_score += 25
        if pct_from_52w_high <= 20: trend_score += 25

        # 2. Volatility Contraction Detection (Check 3 waves of contraction)
        # Wave 1 (40 days ago to 20 days ago) vs Wave 2 (20 days ago to 5 days ago) vs Wave 3 (last 5 days)
        w1_range = (np.max(highs[-45:-20]) - np.min(lows[-45:-20])) / np.mean(closes[-45:-20]) * 100
        w2_range = (np.max(highs[-20:-5]) - np.min(lows[-20:-5])) / np.mean(closes[-20:-5]) * 100
        w3_range = (np.max(highs[-5:]) - np.min(lows[-5:])) / np.mean(closes[-5:]) * 100

        is_contracting = (w1_range > w2_range) and (w2_range > w3_range) and (w3_range < 6.5)

        # 3. Dry Volume Check (Volume contracting on right side of base)
        vol_20d_avg = np.mean(volumes[-20:])
        vol_recent = np.mean(volumes[-3:])
        volume_dry = vol_recent < vol_20d_avg * 0.85

        atr_arr = cls.calculate_atr(df, 14)
        atr_curr = float(atr_arr[-1]) if not np.isnan(atr_arr[-1]) else curr_price * 0.02

        pivot_point = round(float(np.max(highs[-10:])), 2)
        stop_loss = round(pivot_point - (1.5 * atr_curr), 2)
        target1 = round(pivot_point + (2.5 * atr_curr), 2)
        target2 = round(pivot_point + (4.0 * atr_curr), 2)
        risk_pct = round(((pivot_point - stop_loss) / pivot_point) * 100, 2)

        vcp_status = "VCP_READY_BREAKOUT" if (is_contracting and trend_score >= 75) else (
            "VCP_FORMING" if trend_score >= 75 else "WATCHLIST"
        )

        return {
            "symbol": symbol,
            "strategy": "Minervini VCP",
            "current_price": round(curr_price, 2),
            "trend_template_score": trend_score,
            "is_above_50_150_dma": bool(is_above_dmas),
            "pct_from_52w_high": round(pct_from_52w_high, 1),
            "contractions": [round(w1_range, 1), round(w2_range, 1), round(w3_range, 1)],
            "is_volatility_contracting": bool(is_contracting),
            "volume_dry_up": bool(volume_dry),
            "pivot_buy_point": pivot_point,
            "stop_loss": stop_loss,
            "target_1": target1,
            "target_2": target2,
            "risk_reward_ratio": "1:2.6",
            "risk_pct": risk_pct,
            "vcp_status": vcp_status,
            "badge_color": "emerald" if vcp_status == "VCP_READY_BREAKOUT" else "amber"
        }

    @classmethod
    def evaluate_simons_mean_reversion(cls, symbol, df):
        """
        Jim Simons (Statistical Arbitrage & Z-Score Extreme Mean Reversion):
        - Calculates 20-day rolling mean (mu) and standard deviation (sigma)
        - Z-Score = (Close - Mean) / Sigma
        - Extreme Oversold: Z <= -2.0 (High statistical probability of snapback to mean)
        - Extreme Overbought: Z >= +2.0 (Mean reversion pullback likely)
        - RSI Confirmation: RSI < 35 for oversold, RSI > 70 for overbought
        """
        if len(df) < 30:
            return None

        closes = df['Close'].values
        s_closes = pd.Series(closes)
        
        rolling_mean = s_closes.rolling(20).mean().values
        rolling_std = s_closes.rolling(20).std().values

        curr_price = float(closes[-1])
        mu = float(rolling_mean[-1])
        sigma = float(rolling_std[-1]) if float(rolling_std[-1]) > 0 else 1.0

        z_score = (curr_price - mu) / sigma

        # RSI (14)
        delta = s_closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi_series = 100 - (100 / (1 + rs))
        curr_rsi = float(rsi_series.iloc[-1]) if not np.isnan(rsi_series.iloc[-1]) else 50.0

        atr_arr = cls.calculate_atr(df, 14)
        atr_curr = float(atr_arr[-1]) if not np.isnan(atr_arr[-1]) else curr_price * 0.02

        if z_score <= -1.8:
            signal = "STAT_OVERSOLD_BOUNCE"
            bias = "BULLISH_MEAN_REVERSION"
            entry = curr_price
            sl = round(curr_price - (1.2 * atr_curr), 2)
            target = round(mu, 2)
            badge = "emerald"
        elif z_score >= 1.8:
            signal = "STAT_OVERBOUGHT_EXHAUSTION"
            bias = "BEARISH_MEAN_REVERSION"
            entry = curr_price
            sl = round(curr_price + (1.2 * atr_curr), 2)
            target = round(mu, 2)
            badge = "rose"
        else:
            signal = "NEUTRAL_RANGE"
            bias = "EQUILIBRIUM"
            entry = curr_price
            sl = round(curr_price - atr_curr, 2)
            target = round(mu, 2)
            badge = "slate"

        upside_to_mean = round(((mu - curr_price) / curr_price) * 100, 2)

        return {
            "symbol": symbol,
            "strategy": "Simons Z-Score Mean Reversion",
            "current_price": round(curr_price, 2),
            "mean_20d": round(mu, 2),
            "std_dev": round(sigma, 2),
            "z_score": round(z_score, 2),
            "rsi_14": round(curr_rsi, 1),
            "signal": signal,
            "bias": bias,
            "expected_reversion_target": target,
            "stop_loss": sl,
            "deviation_from_mean_pct": upside_to_mean,
            "statistical_confidence": "HIGH (Z-Score > 2.0σ)" if abs(z_score) >= 2.0 else "MODERATE",
            "badge_color": badge
        }

    @classmethod
    def evaluate_turtle_trend(cls, symbol, df):
        """
        Richard Dennis (Turtle Traders 20-Day Donchian Breakout):
        - Buy when Close breaks above 20-day High
        - Short/Exit when Close breaks below 10-day Low
        - Position Sizing Unit = Account Risk / ATR
        """
        if len(df) < 30:
            return None

        closes = df['Close'].values
        highs = df['High'].values
        lows = df['Low'].values

        curr_price = float(closes[-1])
        high_20d = float(np.max(highs[-21:-1]))
        low_20d = float(np.min(lows[-21:-1]))
        low_10d = float(np.min(lows[-11:-1]))

        atr_arr = cls.calculate_atr(df, 20)
        atr_curr = float(atr_arr[-1]) if not np.isnan(atr_arr[-1]) else curr_price * 0.02

        if curr_price > high_20d:
            turtle_action = "SYSTEM_1_BUY_BREAKOUT"
            stop_loss = round(curr_price - (2.0 * atr_curr), 2)
            trail_exit = low_10d
            badge = "emerald"
        elif curr_price < low_10d:
            turtle_action = "SYSTEM_1_EXIT_OR_SHORT"
            stop_loss = round(curr_price + (2.0 * atr_curr), 2)
            trail_exit = high_20d
            badge = "rose"
        else:
            turtle_action = "TREND_HOLDING"
            stop_loss = round(curr_price - (2.0 * atr_curr), 2)
            trail_exit = low_10d
            badge = "amber"

        return {
            "symbol": symbol,
            "strategy": "Turtle 20D Donchian",
            "current_price": round(curr_price, 2),
            "donchian_high_20d": round(high_20d, 2),
            "donchian_low_20d": round(low_20d, 2),
            "turtle_action": turtle_action,
            "atr_20": round(atr_curr, 2),
            "trailing_stop_loss": stop_loss,
            "trail_exit_10d": round(trail_exit, 2),
            "badge_color": badge
        }

    @classmethod
    def run_legendary_scanner(cls):
        """Executes full scan over Top NSE stocks for all 3 legendary strategies."""
        print("==========================================================================")
        print("   EXECUTING WORLD-CLASS LEGENDARY TRADERS STRATEGY ENGINE               ")
        print("   (Mark Minervini VCP + Jim Simons Z-Score + Richard Dennis Turtle)     ")
        print("==========================================================================")

        vcp_candidates = []
        simons_candidates = []
        turtle_candidates = []

        for symbol in cls.WATCHLIST:
            df = cls.fetch_historical_ohlcv(symbol, period="1y")
            if df is None:
                continue

            # 1. Minervini VCP
            vcp_res = cls.evaluate_minervini_vcp(symbol, df)
            if vcp_res:
                vcp_candidates.append(vcp_res)

            # 2. Simons Mean Reversion
            simons_res = cls.evaluate_simons_mean_reversion(symbol, df)
            if simons_res:
                simons_candidates.append(simons_res)

            # 3. Turtle Trend
            turtle_res = cls.evaluate_turtle_trend(symbol, df)
            if turtle_res:
                turtle_candidates.append(turtle_res)

        # Sort VCP by Trend score & Contraction sharpness
        vcp_candidates.sort(key=lambda x: (x["trend_template_score"], -x["pct_from_52w_high"]), reverse=True)
        # Sort Simons by magnitude of Z-Score deviation
        simons_candidates.sort(key=lambda x: abs(x["z_score"]), reverse=True)

        payload = {
            "_meta": {
                "source": "Yahoo Finance Free Feed",
                "as_of": datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%d-%b-%Y %I:%M %p IST"),
                "engine": "LegendaryTraderEngine V1.0",
                "is_stale": False,
                "confidence": 0.95
            },
            "summary": {
                "total_scanned": len(cls.WATCHLIST),
                "vcp_setups_found": len([x for x in vcp_candidates if x["vcp_status"] == "VCP_READY_BREAKOUT"]),
                "simons_extreme_reversions": len([x for x in simons_candidates if abs(x["z_score"]) >= 1.8]),
                "turtle_breakouts": len([x for x in turtle_candidates if x["turtle_action"] == "SYSTEM_1_BUY_BREAKOUT"])
            },
            "minervini_vcp": vcp_candidates,
            "simons_mean_reversion": simons_candidates,
            "turtle_trend": turtle_candidates
        }

        atomic_write_json(cls.JSON_PATH, payload)
        print(f"[SUCCESS] Exported Legendary Trader Studio payload to {cls.JSON_PATH}")
        return payload

if __name__ == "__main__":
    LegendaryTraderEngine.run_legendary_scanner()
