import math
import numpy as np

# Standard Risk-Free Rate for Indian Markets (RBI Repo Rate Benchmark ~ 6.5%)
RISK_FREE_RATE = 0.065

def norm_cdf(x):
    """Cumulative Distribution Function (CDF) for Standard Normal Distribution using math.erf."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def norm_pdf(x):
    """Probability Density Function (PDF) for Standard Normal Distribution."""
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)

class BlackScholesGreeksEngine:
    """Institutional Black-Scholes Option Pricing & Greeks Calculator.
    Calculates Delta, Gamma, Theta, Vega, and solves for Implied Volatility (IV).
    """

    @staticmethod
    def _d1_d2(spot, strike, dte_days, iv, r=RISK_FREE_RATE):
        if spot <= 0 or strike <= 0 or iv <= 0:
            return None, None
        
        # Prevent division by zero for 0 DTE
        t_years = max(dte_days / 365.0, 0.0001)
        
        d1 = (math.log(spot / strike) + (r + 0.5 * iv ** 2) * t_years) / (iv * math.sqrt(t_years))
        d2 = d1 - iv * math.sqrt(t_years)
        return d1, d2

    @classmethod
    def calculate_option_price(cls, option_type, spot, strike, dte_days, iv, r=RISK_FREE_RATE):
        """Calculates theoretical Black-Scholes Option Price."""
        d1, d2 = cls._d1_d2(spot, strike, dte_days, iv, r)
        if d1 is None:
            return 0.0

        t_years = max(dte_days / 365.0, 0.0001)
        
        if option_type.upper() in ["CE", "CALL"]:
            price = spot * norm_cdf(d1) - strike * math.exp(-r * t_years) * norm_cdf(d2)
        else:
            price = strike * math.exp(-r * t_years) * norm_cdf(-d2) - spot * norm_cdf(-d1)

        return max(0.0, round(float(price), 2))

    @classmethod
    def calculate_greeks(cls, option_type, spot, strike, dte_days, iv, r=RISK_FREE_RATE):
        """Calculates complete Option Greeks: Delta, Gamma, Theta (per day), Vega."""
        d1, d2 = cls._d1_d2(spot, strike, dte_days, iv, r)
        if d1 is None:
            return {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "iv": round(iv * 100, 1)}

        t_years = max(dte_days / 365.0, 0.0001)
        is_call = option_type.upper() in ["CE", "CALL"]

        # Delta
        delta = norm_cdf(d1) if is_call else norm_cdf(d1) - 1.0

        # Gamma
        gamma = norm_pdf(d1) / (spot * iv * math.sqrt(t_years))

        # Theta (Daily rupees decay)
        term1 = -(spot * norm_pdf(d1) * iv) / (2 * math.sqrt(t_years))
        if is_call:
            term2 = -r * strike * math.exp(-r * t_years) * norm_cdf(d2)
        else:
            term2 = r * strike * math.exp(-r * t_years) * norm_cdf(-d2)
        
        theta_annual = term1 + term2
        theta_daily = theta_annual / 365.0

        # Vega (Per 1% change in IV)
        vega = (spot * math.sqrt(t_years) * norm_pdf(d1)) / 100.0

        return {
            "delta": round(float(delta), 3),
            "gamma": round(float(gamma), 5),
            "theta": round(float(theta_daily), 2),
            "vega": round(float(vega), 2),
            "iv": round(float(iv * 100.0), 1)
        }

    @classmethod
    def calculate_iv(cls, market_price, option_type, spot, strike, dte_days, r=RISK_FREE_RATE):
        """Solves for Implied Volatility (IV) using Bisection solver."""
        if market_price <= 0 or spot <= 0 or strike <= 0:
            return 0.15 # Fallback 15% IV

        low_iv = 0.01
        high_iv = 3.0
        
        for _ in range(30): # 30 iterations for high precision
            mid_iv = (low_iv + high_iv) / 2.0
            price = cls.calculate_option_price(option_type, spot, strike, dte_days, mid_iv, r)
            
            diff = price - market_price
            if abs(diff) < 0.01:
                return round(float(mid_iv), 4)
            
            if diff > 0:
                high_iv = mid_iv
            else:
                low_iv = mid_iv

        return round(float((low_iv + high_iv) / 2.0), 4)

# Helper functions
def get_greeks(option_type, spot, strike, dte_days, iv):
    return BlackScholesGreeksEngine.calculate_greeks(option_type, spot, strike, dte_days, iv)

def get_iv(market_price, option_type, spot, strike, dte_days):
    return BlackScholesGreeksEngine.calculate_iv(market_price, option_type, spot, strike, dte_days)
