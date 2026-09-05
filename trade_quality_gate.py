class TradeQualityGateEngine:
    """Central Trade Quality Gate & Confluence Engine V3.0.
    Evaluates setups across Data Quality, Market Regime, Strategy Router, Risk Engine, and Confluence.
    Requires minimum 4 independent confirmations and minimum score of 70 (Grade B or above) before allowing trade execution.
    No strategy sends Telegram alerts directly without passing through this gate.
    """

    MIN_CONFIRMATIONS = 4
    MIN_SCORE = 70.0

    @classmethod
    def evaluate_trade_gate(cls, symbol, direction, strategy_name, data_quality_res, regime_res,
                            risk_res, confirmations_list, trade_score=85.0):
        """Central gate decision engine."""
        gate_reasons = []
        is_gate_passed = True

        # 1. Data Quality Check
        if not data_quality_res.get("is_trade_ready", True):
            is_gate_passed = False
            gate_reasons.append("Data quality check failed (Stale/Missing data).")

        # 2. Market Regime Safety Check
        if not regime_res.get("is_trade_allowed", True):
            is_gate_passed = False
            gate_reasons.append(f"Regime {regime_res.get('regime')} does not allow trade.")

        # 3. Risk Engine Check
        if risk_res.get("trading_paused", False):
            is_gate_passed = False
            gate_reasons.append("Risk Engine circuit breaker active (Trading Paused).")

        # 4. Independent Confluence Confirmations Count
        unique_confirmations = list(set(confirmations_list))
        if len(unique_confirmations) < cls.MIN_CONFIRMATIONS:
            is_gate_passed = False
            gate_reasons.append(f"Insufficient independent confirmations ({len(unique_confirmations)} < {cls.MIN_CONFIRMATIONS}).")

        # 5. Trade Score Threshold
        if trade_score < cls.MIN_SCORE:
            is_gate_passed = False
            gate_reasons.append(f"Trade score ({trade_score}) below minimum {cls.MIN_SCORE} threshold.")

        # Assign Grade
        if trade_score >= 90.0: grade = "A+"
        elif trade_score >= 80.0: grade = "A"
        elif trade_score >= 70.0: grade = "B"
        elif trade_score >= 60.0: grade = "WATCH"
        else: grade = "NO_TRADE"

        decision = f"TRADE_{direction.upper()}" if is_gate_passed else "NO_TRADE"

        return {
            "symbol": symbol,
            "direction": direction,
            "strategy": strategy_name,
            "is_gate_passed": is_gate_passed,
            "decision": decision,
            "trade_score": trade_score,
            "grade": grade,
            "confirmations_count": len(unique_confirmations),
            "confirmations": unique_confirmations,
            "reasons": gate_reasons if not is_gate_passed else ["All 5 central gate criteria satisfied."]
        }

# Helper function
def evaluate_gate(symbol, direction, strategy_name, data_quality_res, regime_res, risk_res, confirmations_list, trade_score=85.0):
    return TradeQualityGateEngine.evaluate_trade_gate(symbol, direction, strategy_name, data_quality_res, regime_res, risk_res, confirmations_list, trade_score)
