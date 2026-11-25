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

    # 6. Smart Money Concepts (SMC) Liquidity Sweep check
    smc_res = LegendaryTraderEngine.evaluate_smc_liquidity_sweep("TEST_STOCK", df)
    assert smc_res is not None
    assert "swing_low_20d" in smc_res
    assert "demand_order_block" in smc_res
    assert "entry_trigger" in smc_res
    assert "stop_loss" in smc_res
    assert "target_1" in smc_res
    assert "target_2" in smc_res
    assert "conviction_score" in smc_res

    # 7. Sector Relative Strength (RS) Leader check
    rs_res = LegendaryTraderEngine.evaluate_sector_rs_leader("TEST_STOCK", df, nifty_3m_return=5.0)
    assert rs_res is not None
    assert "stock_3m_return_pct" in rs_res
    assert "rs_score" in rs_res
    assert "rs_status" in rs_res
    assert "entry_trigger" in rs_res
    assert "stop_loss" in rs_res

    # 8. Delta-Neutral Options Strangle check
    strangle_res = LegendaryTraderEngine.evaluate_delta_neutral_strangle("NIFTY 50", spot=23500.0, iv_pct=13.5, dte=3)
    assert strangle_res is not None
    assert strangle_res["call_strike"] > 23500.0
    assert strangle_res["put_strike"] < 23500.0
    assert "stop_loss_per_leg" in strangle_res
    assert "profit_target_decay" in strangle_res
    assert "total_premium_collected" in strangle_res

    # 9. Nicolas Darvas Box check
    darvas_res = LegendaryTraderEngine.evaluate_darvas_box("TEST_STOCK", df)
    assert darvas_res is not None
    assert "box_ceiling" in darvas_res
    assert "box_floor" in darvas_res
    assert "darvas_status" in darvas_res
    assert "entry_trigger" in darvas_res

    # 10. Toby Crabel NR7 check
    crabel_res = LegendaryTraderEngine.evaluate_crabel_nr7("TEST_STOCK", df)
    assert crabel_res is not None
    assert "current_day_range" in crabel_res
    assert "is_nr7" in crabel_res
    assert "nr7_status" in crabel_res

    # 11. Stan Weinstein Stage 2 check
    weinstein_res = LegendaryTraderEngine.evaluate_weinstein_stage2("TEST_STOCK", df)
    assert weinstein_res is not None
    assert "sma_150" in weinstein_res
    assert "base_resistance" in weinstein_res
    assert "weinstein_stage" in weinstein_res

    # 12. John Bollinger Squeeze check
    bollinger_res = LegendaryTraderEngine.evaluate_bollinger_squeeze("TEST_STOCK", df)
    assert bollinger_res is not None
    assert "upper_band" in bollinger_res
    assert "middle_band_sma20" in bollinger_res
    assert "bandwidth_pct" in bollinger_res
    assert "bollinger_status" in bollinger_res

    # 13. Oliver Velez Elephant Bar check
    velez_res = LegendaryTraderEngine.evaluate_velez_elephant_bar("TEST_STOCK", df)
    assert velez_res is not None
    assert "candle_body_pct" in velez_res
    assert "ema_20" in velez_res
    assert "velez_status" in velez_res
