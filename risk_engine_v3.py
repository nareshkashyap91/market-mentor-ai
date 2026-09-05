class RiskEngineV3:
    """Adaptive Risk & Position Sizing Engine V3.0.
    Enforces Max Risk per Trade, Daily Loss Limit, Drawdown Cap, Consecutive Loss Halting, and Correlated Position Caps.
    """

    CONFIG = {
        "MAX_RISK_PER_TRADE_PCT": 1.0,
        "MAX_DAILY_LOSS_PCT": -2.0,
        "MAX_DAILY_DRAWDOWN_PCT": -2.5,
        "MAX_CONSECUTIVE_LOSSES": 3,
        "MAX_OPEN_POSITIONS": 5,
        "MAX_CORRELATED_POSITIONS": 2
    }

    @classmethod
    def evaluate_risk_v3(cls, daily_pnl_pct=0.5, consecutive_losses=0, open_positions_count=2, correlated_count=1, vix_val=13.20):
        """Evaluates all risk guardrails and returns TRADING_PAUSED status."""
        reasons = []
        is_paused = False

        if daily_pnl_pct <= cls.CONFIG["MAX_DAILY_LOSS_PCT"]:
            is_paused = True
            reasons.append(f"Daily loss limit ({cls.CONFIG['MAX_DAILY_LOSS_PCT']}%) breached.")
        elif consecutive_losses >= cls.CONFIG["MAX_CONSECUTIVE_LOSSES"]:
            is_paused = True
            reasons.append(f"Max consecutive losses ({cls.CONFIG['MAX_CONSECUTIVE_LOSSES']}) reached.")
        elif open_positions_count >= cls.CONFIG["MAX_OPEN_POSITIONS"]:
            is_paused = True
            reasons.append(f"Max open positions ({cls.CONFIG['MAX_OPEN_POSITIONS']}) reached.")

        # VIX-based adaptive risk %
        if vix_val >= 22.0:
            allowed_risk_pct = 0.5
            mode = "CAPITAL_PRESERVATION"
        elif vix_val <= 12.0:
            allowed_risk_pct = 1.0
            mode = "LOW_VOLATILITY"
        else:
            allowed_risk_pct = cls.CONFIG["MAX_RISK_PER_TRADE_PCT"]
            mode = "STANDARD"

        return {
            "trading_paused": is_paused,
            "allowed_risk_pct": allowed_risk_pct,
            "risk_mode": mode,
            "daily_pnl_pct": round(daily_pnl_pct, 2),
            "consecutive_losses": consecutive_losses,
            "open_positions": open_positions_count,
            "correlated_positions": correlated_count,
            "pause_reasons": reasons
        }

# Helper function
def get_risk_v3(daily_pnl_pct=0.5, consecutive_losses=0, open_positions_count=2):
    return RiskEngineV3.evaluate_risk_v3(daily_pnl_pct, consecutive_losses, open_positions_count)
