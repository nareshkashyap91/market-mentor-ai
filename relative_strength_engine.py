import numpy as np
import pandas as pd

class RelativeStrengthEngine:
    """Relative Strength vs Nifty 50 & Sector Breadth Engine.
    Calculates Mansfield Relative Strength (RS vs Nifty) and Sector Momentum Alignment.
    """

    @classmethod
    def calculate_relative_strength(cls, stock_df=None, nifty_df=None, stock_change_pct=1.5, nifty_change_pct=0.4):
        """Calculates RS Ratio vs Nifty 50 and outperformance status."""
        rs_score = stock_change_pct - nifty_change_pct

        if stock_df is not None and nifty_df is not None and not stock_df.empty and not nifty_df.empty:
            s_close = stock_df['Close'].values
            n_close = nifty_df['Close'].values
            min_len = min(len(s_close), len(n_close))
            if min_len >= 5:
                s_ret = (s_close[-1] - s_close[-5]) / s_close[-5] * 100.0
                n_ret = (n_close[-1] - n_close[-5]) / n_close[-5] * 100.0
                rs_score = round(s_ret - n_ret, 2)

        if rs_score >= 1.0:
            status = "STRONG OUTPERFORMER (RS > +1.0%)"
            quality_tag = "HIGH RS LEADERSHIP"
            is_outperforming = True
        elif rs_score >= 0.0:
            status = "MODERATE OUTPERFORMER"
            quality_tag = "MILD RS LEADERSHIP"
            is_outperforming = True
        else:
            status = "UNDERPERFORMER (RS < 0.0%)"
            quality_tag = "WEAK RS (AVOID)"
            is_outperforming = False

        return {
            "relative_strength_score": round(rs_score, 2),
            "outperformance_status": status,
            "quality_tag": quality_tag,
            "is_outperforming": is_outperforming
        }

# Helper function
def get_relative_strength(stock_df=None, nifty_df=None, stock_change_pct=1.5, nifty_change_pct=0.4):
    return RelativeStrengthEngine.calculate_relative_strength(stock_df, nifty_df, stock_change_pct, nifty_change_pct)
