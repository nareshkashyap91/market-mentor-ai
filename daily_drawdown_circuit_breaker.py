class DailyDrawdownCircuitBreakerEngine:
    """Daily Drawdown Circuit Breaker & Consecutive Loss Halting Engine.
    Enforces daily loss cap (-2.0%) and halts trading after 3 consecutive stop-losses.
    """
    MAX_DAILY_LOSS_PCT = -2.0  # -2.0% daily drawdown limit
    MAX_CONSECUTIVE_LOSSES = 3  # Halt trading after 3 consecutive SLs

    @classmethod
    def evaluate_circuit_breaker(cls, daily_pnl_pct=0.8, consecutive_losses=0):
        """Evaluates daily PnL and loss count against risk circuit breaker thresholds."""
        is_drawdown_breached = daily_pnl_pct <= cls.MAX_DAILY_LOSS_PCT
        is_consecutive_losses_breached = consecutive_losses >= cls.MAX_CONSECUTIVE_LOSSES

        if is_drawdown_breached:
            status = "🔴 CIRCUIT BREAKER TRIPPED: MAX DAILY DRAWDOWN LIMIT BREACHED (-2.0%)"
            trading_allowed = False
            action_required = "TRADING HALTED FOR THE DAY (CAPITAL PRESERVATION)"
        elif is_consecutive_losses_breached:
            status = f"🔴 CIRCUIT BREAKER TRIPPED: {consecutive_losses} CONSECUTIVE LOSSES REACHED"
            trading_allowed = False
            action_required = "TRADING HALTED FOR THE DAY (NO OVER-TRADING)"
        else:
            status = "🟢 CIRCUIT BREAKER NORMAL (TRADING ALLOWED)"
            trading_allowed = True
            action_required = "EXECUTE QUALIFIED SETUPS WITH RISK DISCIPLINE"

        return {
            "circuit_breaker_status": status,
            "trading_allowed": trading_allowed,
            "daily_pnl_pct": round(daily_pnl_pct, 2),
            "consecutive_losses": consecutive_losses,
            "action_required": action_required
        }

# Helper function
def evaluate_circuit_breaker(daily_pnl_pct=0.8, consecutive_losses=0):
    return DailyDrawdownCircuitBreakerEngine.evaluate_circuit_breaker(daily_pnl_pct, consecutive_losses)
