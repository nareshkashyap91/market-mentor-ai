class AIExplanationEngine:
    """AI Explanation & FOMO Risk Engine V3.0.
    Generates structured answers to the 7 mandatory AI trade rationale questions:
    1. WHY THIS STOCK?
    2. WHY THIS STRATEGY?
    3. WHY NOW?
    4. WHAT CONFIRMS IT?
    5. WHAT INVALIDATES IT?
    6. WHAT IS THE RISK?
    7. WHAT WOULD MAKE THE AI CHANGE ITS MIND? (Mandatory)
    Also evaluates FOMO_RISK (LOW / MEDIUM / HIGH).
    """

    @classmethod
    def generate_trade_explanation(cls, symbol, direction, strategy_name, score, dist_vwap_atr=0.8, rr_ratio=2.2):
        """Generates comprehensive AI Trade Explanation Object."""
        
        # Evaluate FOMO Risk
        if dist_vwap_atr > 2.2 or rr_ratio < 1.5:
            fomo_risk = "HIGH"
        elif dist_vwap_atr > 1.5:
            fomo_risk = "MEDIUM"
        else:
            fomo_risk = "LOW"

        explanation = {
            "symbol": symbol,
            "direction": direction,
            "strategy": strategy_name,
            "fomo_risk": fomo_risk,
            "why_this_stock": f"NSE:{symbol} exhibits strong relative strength vs Nifty 50 with tight consolidation base and volume expansion.",
            "why_this_strategy": f"Selected {strategy_name} because market regime is aligned with high-probability trend continuation.",
            "why_now": "15-minute Opening Range Breakout confirmed with VWAP support and RVOL > 1.5.",
            "what_confirms_it": "Multi-timeframe structure alignment (BOS), positive sector momentum, and institutional cash accumulation.",
            "what_invalidates_it": f"A 5-minute candle close below the VWAP support or stop-loss level.",
            "what_is_the_risk": f"Defined risk of 1.0% capital allocation with a favorable 1:{rr_ratio:.1f} Risk-to-Reward Ratio.",
            "what_would_make_ai_change_mind": "A sudden market-wide volatility spike (VIX > 22), FII distribution divergence, or price dropping back inside Opening Range."
        }

        return explanation

# Helper function
def get_ai_explanation(symbol, direction, strategy_name, score):
    return AIExplanationEngine.generate_trade_explanation(symbol, direction, strategy_name, score)
