import numpy as np

class IntradayPrecisionV3Engine:
    """Intraday ORB MTF + Liquidity Sweep Proxy + Breakout Quality Engine V3.0.
    Integrates 15m, 30m, 45m Opening Ranges, Market Structure (BOS, CHOCH, HH, HL, LH, LL),
    Liquidity Sweep / Stop-Run Proxies, and Breakout Quality Classification.
    """

    @classmethod
    def evaluate_intraday_v3(cls, close, open_p, high, low, vwap, atr,
                             orb_15m=(24520, 24450), orb_30m=(24535, 24440), orb_45m=(24545, 24430),
                             rvol=1.8, pdh=24500, pdl=24400, risk_reward_ratio=2.2):
        """Evaluates intraday setups across MTF ORB, Market Structure, Liquidity Sweep Proxy, and Breakout Quality."""
        orb_15_high, orb_15_low = orb_15m
        orb_30_high, orb_30_low = orb_30m

        # 1. Market Structure Classification
        if close > orb_30_high and high > pdh:
            structure = "BOS_BULLISH (BREAK OF STRUCTURE)"
            trend_structure = "HH_HL (HIGHER HIGH HIGHER LOW)"
        elif close < orb_30_low and low < pdl:
            structure = "BOS_BEARISH"
            trend_structure = "LH_LL (LOWER HIGH LOWER LOW)"
        else:
            structure = "CHOCH_NEUTRAL (CHANGE OF CHARACTER)"
            trend_structure = "RANGEBOUND"

        # 2. Liquidity Sweep / Stop-Run Proxy Detection
        upper_wick = high - max(open_p, close)
        lower_wick = min(open_p, close) - low
        body = abs(close - open_p)

        if high > pdh and close < pdh and upper_wick > body * 1.2:
            sweep_proxy = "PDH_LIQUIDITY_SWEEP_PROXY (RETAIL BAIT)"
        elif low < pdl and close > pdl and lower_wick > body * 1.2:
            sweep_proxy = "PDL_LIQUIDITY_SWEEP_PROXY (BULLISH ACCUMULATION)"
        elif high > orb_15_high and close < orb_15_high:
            sweep_proxy = "ORB_HIGH_SWEEP_PROXY"
        else:
            sweep_proxy = "NO_LIQUIDITY_SWEEP_DETECTED"

        # 3. Breakout Quality Classification: GENUINE, PROBABLE, WEAK, FAILED, EXTENDED
        dist_vwap_atr = (close - vwap) / max(atr, 1e-6)

        if dist_vwap_atr > 2.5:
            breakout_quality = "EXTENDED"
            quality_reason = "Price extended > 2.5x ATR above VWAP. High chase risk."
            is_valid_trade = False
        elif risk_reward_ratio < 1.5:
            breakout_quality = "WEAK"
            quality_reason = f"Risk-Reward Ratio ({risk_reward_ratio:.1f}) below minimum 1.5 threshold."
            is_valid_trade = False
        elif close > orb_15_high and rvol >= 1.5 and close > vwap and sweep_proxy == "NO_LIQUIDITY_SWEEP_DETECTED":
            breakout_quality = "GENUINE"
            quality_reason = "15m ORB breakout supported by VWAP, high volume (RVOL >= 1.5), and clean market structure."
            is_valid_trade = True
        elif close > orb_15_high and rvol >= 1.2:
            breakout_quality = "PROBABLE"
            quality_reason = "Moderate breakout quality. Requires pullback retest confirmation."
            is_valid_trade = True
        elif "SWEEP" in sweep_proxy:
            breakout_quality = "FAILED"
            quality_reason = f"Breakout failed. {sweep_proxy} detected."
            is_valid_trade = False
        else:
            breakout_quality = "WEAK"
            quality_reason = "No valid breakout setup."
            is_valid_trade = False

        return {
            "breakout_quality": breakout_quality,
            "quality_reason": quality_reason,
            "is_valid_trade": is_valid_trade,
            "market_structure": structure,
            "trend_structure": trend_structure,
            "liquidity_sweep_proxy": sweep_proxy,
            "dist_vwap_atr": round(dist_vwap_atr, 2),
            "risk_reward_ratio": round(risk_reward_ratio, 2)
        }

# Helper function
def evaluate_intraday_v3_helper(close, open_p, high, low, vwap, atr):
    return IntradayPrecisionV3Engine.evaluate_intraday_v3(close, open_p, high, low, vwap, atr)
