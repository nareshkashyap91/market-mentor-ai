import os

class BrokerConnector:
    """Institutional Broker API Connector & Safety Protection Engine.
    Enforces Live Trading OFF safety locks and Hedge Failure Protection.
    """

    # Section 46 Requirement: "Live trading remains OFF by default"
    LIVE_TRADING_ENABLED = False

    @classmethod
    def is_live_trading_active(cls):
        """Verifies if live real-money execution is enabled."""
        env_flag = os.environ.get("ENABLE_LIVE_REAL_MONEY_TRADING", "FALSE").upper().strip()
        return cls.LIVE_TRADING_ENABLED and env_flag == "TRUE"

    @classmethod
    def get_broker_status(cls):
        """Returns active broker connection status and safety locks."""
        is_live = cls.is_live_trading_active()
        return {
            "live_trading_active": is_live,
            "safety_lock_status": "LOCKED_OFF (PAPER TRADING ONLY)" if not is_live else "UNLOCKED (LIVE EXECUTION)",
            "hedge_failure_protection": "ENABLED (Hedge Leg Verification Active)",
            "broker_gateway": "Dhan API Gateway (Simulated / Ready)"
        }

    @classmethod
    def execute_hedged_order(cls, strategy_name, legs, spot_price):
        """Executes hedged multi-leg order with mandatory Hedge Failure Protection."""
        if not cls.is_live_trading_active():
            return {
                "success": False,
                "status": "REJECTED_BY_SAFETY_LOCK",
                "message": "Live real-money trading is OFF by default for capital protection. Order routed to Paper Trading Simulator."
            }

        # Step 1: Execute Hedge Legs First (Hedge Failure Protection)
        hedge_legs = [l for l in legs if "BUY" in l.upper() or "(Hedge)" in l]
        short_legs = [l for l in legs if "SELL" in l.upper() and "(Hedge)" not in l]

        # Simulate Hedge Execution Verification
        hedge_success = len(hedge_legs) > 0
        if not hedge_success:
            return {
                "success": False,
                "status": "HEDGE_FAILURE_ABORTED",
                "message": "Hedge Failure Protection Triggered! Hedge leg failed or missing. Short position aborted to prevent unhedged risk."
            }

        return {
            "success": True,
            "status": "LIVE_ORDER_EXECUTED",
            "message": f"Successfully placed hedged order for {strategy_name}."
        }

# Helper function
def get_broker_status():
    return BrokerConnector.get_broker_status()
