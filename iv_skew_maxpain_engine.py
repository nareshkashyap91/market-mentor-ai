import numpy as np

class IVSkewMaxPainEngine:
    """Institutional Options IV Skew & Max Pain Reversal Engine.
    Calculates Max Pain Strike Price, Put-Call IV Skew, and Gamma Blast Squeeze Zones.
    """

    @classmethod
    def calculate_max_pain(cls, option_chain_strikes=None):
        """Calculates exact Max Pain Strike Price where option writers retain maximum premium."""
        if not option_chain_strikes:
            # Synthetic / Standard Chain Fallback
            option_chain_strikes = [
                {"strike": 23800, "call_oi": 15000, "put_oi": 85000},
                {"strike": 23900, "call_oi": 22000, "put_oi": 72000},
                {"strike": 24000, "call_oi": 45000, "put_oi": 120000},  # Heavy Put Wall
                {"strike": 24100, "call_oi": 65000, "put_oi": 60000},
                {"strike": 24200, "call_oi": 135000, "put_oi": 35000}, # Heavy Call Wall (Max Pain Candidate)
                {"strike": 24300, "call_oi": 95000, "put_oi": 18000},
                {"strike": 24400, "call_oi": 80000, "put_oi": 12000}
            ]

        strikes = [s["strike"] for s in option_chain_strikes]
        total_pains = []

        for target_k in strikes:
            cum_pain = 0
            for row in option_chain_strikes:
                k = row["strike"]
                c_oi = row["call_oi"]
                p_oi = row["put_oi"]

                # Call Pain (In The Money Calls)
                if target_k > k:
                    cum_pain += c_oi * (target_k - k)

                # Put Pain (In The Money Puts)
                if target_k < k:
                    cum_pain += p_oi * (k - target_k)

            total_pains.append(cum_pain)

        min_pain_idx = int(np.argmin(total_pains))
        max_pain_strike = strikes[min_pain_idx]

        return {
            "max_pain_strike": max_pain_strike,
            "min_total_pain_value": float(total_pains[min_pain_idx]),
            "max_pain_summary": f"EXPIRY PIN TARGET: ₹{max_pain_strike:.0f} (Max Pain Strike)"
        }

    @classmethod
    def calculate_iv_skew(cls, call_iv=12.5, put_iv=14.8):
        """Calculates Put-Call IV Skew and detects Gamma Blast Short Squeeze risk."""
        skew = round(put_iv - call_iv, 2)

        if skew > 3.0:
            skew_status = "HIGH PUT SKEW (HEAVY DOWN RISK HEDGING / POTENTIAL REVERSAL)"
            gamma_blast_risk = "HIGH PUT SHORT COVERING RISK"
        elif skew < -2.0:
            skew_status = "HIGH CALL SKEW (BULLISH CALL BUYING FRENZY)"
            gamma_blast_risk = "HIGH CALL SHORT COVERING SQUEEZE (GAMMA BLAST)"
        else:
            skew_status = "BALANCED IV SKEW"
            gamma_blast_risk = "NORMAL GAMMA EXPOSURE"

        return {
            "call_iv_pct": call_iv,
            "put_iv_pct": put_iv,
            "iv_skew_pct": skew,
            "skew_status": skew_status,
            "gamma_blast_risk": gamma_blast_risk
        }

# Helper function
def get_iv_skew_and_max_pain(option_chain_strikes=None):
    mp = IVSkewMaxPainEngine.calculate_max_pain(option_chain_strikes)
    skew = IVSkewMaxPainEngine.calculate_iv_skew()
    return {**mp, **skew}
