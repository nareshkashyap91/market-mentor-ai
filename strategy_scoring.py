import numpy as np

class StrategyScoringEngine:
    """Institutional Strategy Risk Scoring & NO TRADE Engine.
    Separates Historical Probability from AI Confidence Score, computes Risk-Reward Ratios,
    and enforces strict NO TRADE guardrails during unfavorable market regimes.
    """

    @staticmethod
    def evaluate_no_trade_conditions(regime_confidence, vix_val, is_stale=False, stale_reason=""):
        """Evaluates whether current market environment warrants a NO TRADE signal."""
        reasons = []

        if is_stale:
            reasons.append(f"STALE DATA: {stale_reason}")

        if regime_confidence < 35.0:
            reasons.append(f"LOW REGIME CONFIDENCE ({regime_confidence:.1f}% < 35.0% threshold)")

        if vix_val > 25.0:
            reasons.append(f"EXTREME VOLATILITY / EVENT RISK (India VIX: {vix_val:.1f} > 25.0)")

        is_no_trade = len(reasons) > 0

        return {
            "is_no_trade": is_no_trade,
            "trade_status": "NO TRADE (CAPITAL PROTECTION ACTIVE)" if is_no_trade else "ACTIVE QUANT SIGNALS",
            "reasons": reasons,
            "summary": " | ".join(reasons) if is_no_trade else "Market Conditions Optimal for Execution"
        }

    @classmethod
    def score_and_enrich_strategy(cls, strategy, regime_confidence, vix_val):
        """Enriches strategy with explicit Historical Probability vs AI Confidence, Risk-Reward, and Risk Score."""
        s = strategy.copy()

        # Parse historical win rate e.g. "82%" -> 82.0
        try:
            hist_win = float(s.get("win_prob", "70%").replace("%", "").strip())
        except Exception:
            hist_win = 70.0

        ai_confidence = float(regime_confidence)

        # Risk-Reward Calculation
        spot = s.get("entry_spot", 0.0)
        sl = s.get("sl_spot", spot)
        t1 = s.get("target1_spot", spot)

        risk_reward = 1.5 # Default
        if isinstance(spot, (int, float)) and isinstance(sl, (int, float)) and isinstance(t1, (int, float)) and spot > 0:
            risk_pts = abs(spot - sl)
            reward_pts = abs(t1 - spot)
            if risk_pts > 0:
                risk_reward = round(reward_pts / risk_pts, 2)

        # Quantitative Overall Composite Score
        composite_score = (hist_win * 0.5) + (ai_confidence * 0.3) + (min(risk_reward, 3.0) * 10.0 * 0.2)
        composite_score = round(min(100.0, max(20.0, composite_score)), 1)

        s["historical_win_probability"] = f"{hist_win:.0f}%"
        s["ai_confidence_score"] = f"{ai_confidence:.0f}%"
        s["risk_reward_ratio"] = f"1:{risk_reward:.1f}"
        s["composite_score"] = composite_score

        return s

# Helper function
def evaluate_strategies(strategies, regime_confidence, vix_val, is_stale=False):
    no_trade_eval = StrategyScoringEngine.evaluate_no_trade_conditions(regime_confidence, vix_val, is_stale)
    
    scored_strats = []
    for s in strategies:
        scored_strats.append(StrategyScoringEngine.score_and_enrich_strategy(s, regime_confidence, vix_val))

    return {
        "no_trade_eval": no_trade_eval,
        "strategies": scored_strats
    }
