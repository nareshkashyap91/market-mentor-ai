class AdaptiveRiskRegimeEngine:
    """Adaptive Regime Risk Engine.
    Dynamically adjusts Risk-per-Trade % (0.5%, 1.0%, 1.5%) based on Market Regime confidence and VIX.
    """

    @classmethod
    def calculate_adaptive_risk_pct(cls, regime="🟢 BULLISH_TRENDING", confidence_score=78.5, vix_val=13.20):
        """Calculates dynamic adaptive risk percentage per trade."""
        if vix_val > 22.0 or confidence_score < 55.0 or "SIDEWAYS" in regime.upper():
            risk_pct = 0.5
            mode = "CAPITAL PRESERVATION MODE (0.5% RISK PER TRADE)"
            reason = "High Volatility (VIX > 22) or Low Regime Confidence"
        elif confidence_score >= 80.0 and "TRENDING" in regime.upper():
            risk_pct = 1.5
            mode = "AGGRESSIVE TREND EXPANSION MODE (1.5% RISK PER TRADE)"
            reason = "Strong Trending Market & High Regime Confidence (>80%)"
        else:
            risk_pct = 1.0
            mode = "STANDARD ALLOCATION MODE (1.0% RISK PER TRADE)"
            reason = "Normal Market Conditions"

        return {
            "adaptive_risk_pct": risk_pct,
            "risk_mode": mode,
            "regime_confidence": confidence_score,
            "vix_val": vix_val,
            "reason": reason
        }

# Helper function
def get_adaptive_risk(regime="🟢 BULLISH_TRENDING", confidence_score=78.5, vix_val=13.20):
    return AdaptiveRiskRegimeEngine.calculate_adaptive_risk_pct(regime, confidence_score, vix_val)
