import pytest
import pandas as pd
import numpy as np
from legendary_trader_engine import LegendaryTraderEngine

def test_legendary_trader_math_calculations():
    # Synthetic DataFrame with 220 days of data
    dates = pd.date_range("2026-01-01", periods=220)
    # Steady uptrend followed by tight consolidation
    base_prices = [100 + i * 0.3 for i in range(180)]
    tight_prices = [base_prices[-1] + np.sin(i * 0.5) * (10 / (i + 1)) for i in range(40)]
    prices = base_prices + tight_prices
    
    df = pd.DataFrame({
        "Open": prices,
        "High": [p + 1.0 for p in prices],
        "Low": [p - 1.0 for p in prices],
        "Close": prices,
        "Volume": [100000] * 220
    }, index=dates)

    # 1. Minervini VCP check
    vcp_res = LegendaryTraderEngine.evaluate_minervini_vcp("TEST_STOCK", df)
    assert vcp_res is not None
    assert "trend_template_score" in vcp_res
    assert "contractions" in vcp_res
    assert "pivot_buy_point" in vcp_res
    assert "stop_loss" in vcp_res
    assert vcp_res["risk_pct"] > 0

    # 2. Jim Simons Reversion check
    simons_res = LegendaryTraderEngine.evaluate_simons_mean_reversion("TEST_STOCK", df)
    assert simons_res is not None
    assert "z_score" in simons_res
    assert "mean_20d" in simons_res
    assert "rsi_14" in simons_res
    assert "expected_reversion_target" in simons_res

    # 3. Richard Dennis Turtle check
    turtle_res = LegendaryTraderEngine.evaluate_turtle_trend("TEST_STOCK", df)
    assert turtle_res is not None
    assert "donchian_high_20d" in turtle_res
    assert "donchian_low_20d" in turtle_res
    assert "trailing_stop_loss" in turtle_res
    assert turtle_res["atr_20"] > 0

    # 4. Larry Connors RSI(2) check
    connors_res = LegendaryTraderEngine.evaluate_connors_rsi2("TEST_STOCK", df)
    assert connors_res is not None
    assert "rsi_2" in connors_res
    assert "sma_200" in connors_res
    assert "sma_5" in connors_res
    assert "exit_target_sma5" in connors_res
    assert "historical_win_rate" in connors_res
    assert connors_res["is_above_200_sma"] is True

    # 5. Andreas Clenow Exponential Momentum check
    clenow_res = LegendaryTraderEngine.evaluate_clenow_momentum("TEST_STOCK", df)
    assert clenow_res is not None
    assert "annualized_slope_pct" in clenow_res
    assert "r_squared" in clenow_res
    assert "clenow_momentum_score" in clenow_res
    assert "risk_parity_shares" in clenow_res
    assert clenow_res["r_squared"] >= 0.0
