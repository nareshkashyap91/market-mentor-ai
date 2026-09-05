import numpy as np

class SMCLiquiditySweepEngine:
    """Smart Money Concepts (SMC) Liquidity Sweep & Order Block Detector Engine.
    Detects liquidity sweep wicks (Retail Baits) and Institutional Order Block zones.
    """

    @classmethod
    def evaluate_smc_liquidity(cls, close, open_p, high, low, orb_high, orb_low, rvol=1.2):
        """Evaluates price action for SMC liquidity sweeps and order block zones."""
        upper_wick = high - max(open_p, close)
        lower_wick = min(open_p, close) - low
        body = abs(close - open_p)

        # Upper Liquidity Sweep (Fake breakout above ORB High with long upper wick & weak close)
        is_upper_sweep = (high > orb_high) and (close < orb_high) and (upper_wick > body * 1.5)
        
        # Lower Liquidity Sweep (Fake breakdown below ORB Low with long lower wick & bullish close)
        is_lower_sweep = (low < orb_low) and (close > orb_low) and (lower_wick > body * 1.5)

        if is_upper_sweep:
            status = "SMC UPPER LIQUIDITY SWEEP DETECTED (RETAIL BUY BAIT)"
            signal = "BEARISH REVERSAL"
            order_block_zone = f"₹{high:.2f} - ₹{orb_high:.2f}"
            is_valid_setup = False
        elif is_lower_sweep:
            status = "SMC LOWER LIQUIDITY SWEEP DETECTED (BULLISH ACCUMULATION)"
            signal = "BULLISH REVERSAL"
            order_block_zone = f"₹{orb_low:.2f} - ₹{low:.2f}"
            is_valid_setup = True
        elif close > orb_high and rvol >= 1.5:
            status = "INSTITUTIONAL ORDER BLOCK BREAKOUT (GENUINE EXPANSION)"
            signal = "BULLISH CONTINUATION"
            order_block_zone = f"₹{orb_high:.2f} (Support)"
            is_valid_setup = True
        else:
            status = "NORMAL ORDER FLOW"
            signal = "NEUTRAL"
            order_block_zone = "No Order Block"
            is_valid_setup = True

        return {
            "smc_status": status,
            "smc_signal": signal,
            "order_block_zone": order_block_zone,
            "is_valid_setup": is_valid_setup,
            "upper_wick": round(upper_wick, 2),
            "lower_wick": round(lower_wick, 2)
        }

# Helper function
def get_smc_liquidity_analysis(close, open_p, high, low, orb_high, orb_low, rvol=1.2):
    return SMCLiquiditySweepEngine.evaluate_smc_liquidity(close, open_p, high, low, orb_high, orb_low, rvol)
