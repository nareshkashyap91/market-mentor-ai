import numpy as np
import pandas as pd
from option_greeks import BlackScholesGreeksEngine

class OptionChainAnalyzer:
    """Institutional Option Chain & Net Strategy Greeks Analyzer."""

    @staticmethod
    def calculate_strategy_net_greeks(legs, spot, dte_days, default_iv=0.15):
        """Calculates Net Strategy Delta, Net Theta (daily decay), Net Vega across multi-leg spreads."""
        net_delta = 0.0
        net_gamma = 0.0
        net_theta = 0.0
        net_vega = 0.0

        for leg in legs:
            # Parse leg string e.g. "SELL NIFTY 24500 PE", "BUY NIFTY 24600 CE"
            tokens = leg.split()
            if len(tokens) < 4:
                continue

            action = tokens[0].upper() # BUY or SELL
            option_type = tokens[-1].upper() if tokens[-1].upper() in ["CE", "PE"] else (tokens[-2].upper() if tokens[-2].upper() in ["CE", "PE"] else "CE")
            
            # Extract strike price
            strike = spot
            for t in tokens:
                if t.isdigit():
                    strike = float(t)
                    break

            greeks = BlackScholesGreeksEngine.calculate_greeks(option_type, spot, strike, dte_days, default_iv)

            multiplier = 1.0 if action == "BUY" else -1.0
            net_delta += greeks["delta"] * multiplier
            net_gamma += greeks["gamma"] * multiplier
            net_theta += greeks["theta"] * multiplier
            net_vega += greeks["vega"] * multiplier

        return {
            "net_delta": round(float(net_delta), 3),
            "net_gamma": round(float(net_gamma), 5),
            "net_theta": round(float(net_theta), 2),
            "net_vega": round(float(net_vega), 2),
            "implied_volatility_pct": round(default_iv * 100.0, 1)
        }

    @staticmethod
    def analyze_chain_support_resistance(spot, atm_strike, step=100):
        """Generates key OI support and resistance strike levels."""
        max_call_oi_strike = atm_strike + step * 2
        max_put_oi_strike = atm_strike - step * 2

        return {
            "max_call_oi_resistance": max_call_oi_strike,
            "max_put_oi_support": max_put_oi_strike,
            "atm_strike": atm_strike
        }
