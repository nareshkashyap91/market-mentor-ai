import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta

class MomentumDataValidator:
    """Data Validation Layer for Next-Day Momentum Stock Intelligence Engine."""

    REQUIRED_FIELDS = [
        'Close', 'Open', 'High', 'Low', 'Volume', 
        'dma20', 'dma50', 'dma100', 'dma200', 
        'ema9', 'ema21', 'ema50', 'ema200',
        'rsi', 'atr', 'adx', 'rvol'
    ]

    @classmethod
    def validate_stock_data(cls, stock_data):
        """Validates all required fields for a stock dataset."""
        ist_tz = timezone(timedelta(hours=5, minutes=30))
        now_str = datetime.now(ist_tz).strftime("%d-%b-%Y %I:%M %p")

        missing = [f for f in cls.REQUIRED_FIELDS if f not in stock_data or stock_data[f] is None]
        
        if missing:
            return {
                "is_valid": False,
                "status": "DATA UNAVAILABLE",
                "missing_fields": missing,
                "timestamp": now_str,
                "freshness": "UNAVAILABLE"
            }

        # Stale data check
        stale_minutes = stock_data.get("stale_minutes", 0)
        if stale_minutes > 60:
            return {
                "is_valid": False,
                "status": "STALE DATA",
                "stale_minutes": stale_minutes,
                "timestamp": now_str,
                "freshness": f"{stale_minutes:.1f}m old"
            }

        return {
            "is_valid": True,
            "status": "PASSED",
            "timestamp": now_str,
            "freshness": "FRESH (LIVE/EOD)"
        }

class TrendEngine:
    """Analyses 20/50/100/200 DMAs and 9/21/50/200 EMAs to classify trend quality."""

    @classmethod
    def classify_trend(cls, close, dma20, dma50, dma100, dma200, ema9, ema21, ema50, ema200):
        dma_aligned = dma20 > dma50 > dma100 > dma200
        dma_bearish_aligned = dma20 < dma50 < dma100 < dma200
        above_all_dmas = close > max(dma20, dma50, dma100, dma200)
        below_all_dmas = close < min(dma20, dma50, dma100, dma200)

        # DMA Compression check (width between 20 DMA and 200 DMA < 4% of price)
        dma_spread_pct = abs(dma20 - dma200) / close * 100.0
        dma_compression = dma_spread_pct < 4.0

        # Classification
        if dma_aligned and above_all_dmas and ema9 > ema21 > ema50:
            trend_class = "STRONG BULLISH TREND"
            score = 15
        elif above_all_dmas and ema9 > ema21:
            trend_class = "BULLISH TREND"
            score = 12
        elif below_all_dmas and ema9 < ema21 < ema50:
            trend_class = "STRONG BEARISH TREND"
            score = 0
        elif below_all_dmas:
            trend_class = "BEARISH TREND"
            score = 3
        else:
            trend_class = "NEUTRAL"
            score = 7

        return {
            "trend_classification": trend_class,
            "trend_score": score,
            "dma_aligned": dma_aligned,
            "above_all_dmas": above_all_dmas,
            "below_all_dmas": below_all_dmas,
            "dma_compression": dma_compression,
            "dma_spread_pct": round(dma_spread_pct, 2)
        }

class MomentumRvolEngine:
    """Analyses multi-indicator momentum (RSI, ADX, MACD, ROC) and Relative Volume (RVOL)."""

    @classmethod
    def classify_rvol(cls, rvol):
        if rvol < 0.75:
            return "Weak (<0.75)", 3
        elif rvol < 1.0:
            return "Normal (0.75-1.0)", 6
        elif rvol < 1.5:
            return "Improving (1.0-1.5)", 10
        elif rvol < 2.0:
            return "Strong (1.5-2.0)", 13
        else:
            return "Exceptional (>2.0)", 15

    @classmethod
    def classify_momentum(cls, rsi, adx, price_change_pct, rvol):
        rvol_label, rvol_score = cls.classify_rvol(rvol)

        # Multi-indicator momentum classification (avoiding raw RSI alone)
        if rsi >= 60 and adx >= 25 and price_change_pct > 0 and rvol >= 1.5:
            mom_class = "VERY STRONG"
            mom_score = 10
        elif rsi >= 55 and adx >= 20 and price_change_pct > 0:
            mom_class = "STRONG"
            mom_score = 8
        elif rsi >= 45 and rsi < 55:
            mom_class = "MODERATE"
            mom_score = 5
        elif rsi < 45 and price_change_pct <= 0:
            mom_class = "WEAK"
            mom_score = 2
        else:
            mom_class = "NEGATIVE"
            mom_score = 0

        # Price + Volume Relationship (Accumulation / Distribution Proxy)
        if price_change_pct > 0 and rvol >= 1.2:
            pv_relation = "Price ↑ + Volume ↑ (Accumulation Proxy)"
        elif price_change_pct > 0 and rvol < 0.8:
            pv_relation = "Price ↑ + Volume ↓ (Weak Buying / Caution)"
        elif price_change_pct < 0 and rvol >= 1.2:
            pv_relation = "Price ↓ + Volume ↑ (Distribution Proxy)"
        else:
            pv_relation = "Price ↓ + Volume ↓ (Normal Pullback)"

        return {
            "momentum_classification": mom_class,
            "momentum_score": mom_score,
            "rvol_label": rvol_label,
            "rvol_score": rvol_score,
            "pv_relationship": pv_relation
        }

class RelativeStrengthEngine:
    """Analyses stock outperformance relative to NIFTY 50 and Sector benchmarks."""

    @classmethod
    def calculate_relative_strength(cls, stock_return_1y, nifty_return_1y, sector_return_1y=None):
        rs_nifty_diff = stock_return_1y - nifty_return_1y
        sector_diff = (stock_return_1y - sector_return_1y) if sector_return_1y is not None else rs_nifty_diff

        # Calculate 0-100 Relative Strength Score
        raw_rs_score = 50.0 + (rs_nifty_diff * 0.8) + (sector_diff * 0.4)
        rs_score = float(np.clip(raw_rs_score, 0.0, 100.0))

        if rs_score >= 80:
            rs_class = "VERY STRONG"
        elif rs_score >= 65:
            rs_class = "STRONG"
        elif rs_score >= 45:
            rs_class = "NEUTRAL"
        elif rs_score >= 30:
            rs_class = "WEAK"
        else:
            rs_class = "VERY WEAK"

        return {
            "rs_score": round(rs_score, 1),
            "rs_classification": rs_class,
            "outperforming_nifty": rs_nifty_diff > 0,
            "rs_nifty_diff_pct": round(rs_nifty_diff, 2)
        }

class MomentumDualScorer:
    """Calculates Momentum Quality Score (0-100) and Next-Day Trade Setup Score (0-100)."""

    @classmethod
    def calculate_scores(cls, trend_info, mom_info, rs_info, price_action_score=12, risk_reward_score=4, liquidity_score=5, event_risk_score=5, market_align_score=8, extension_penalty=0):
        # 1. Momentum Quality Score (0-100)
        # Weights: Trend (15), Momentum (10), RVOL (15), Price Action (15), RS (10), Sector (5), Market Align (10), RR (5), Liquidity (5), Event (5)
        trend_s = trend_info["trend_score"]
        mom_s = mom_info["momentum_score"]
        rvol_s = mom_info["rvol_score"]
        rs_s = min(10, int(rs_info["rs_score"] / 10))

        momentum_quality_score = trend_s + mom_s + rvol_s + price_action_score + rs_s + 4 + market_align_score + risk_reward_score + liquidity_score + event_risk_score
        momentum_quality_score = float(np.clip(momentum_quality_score, 0, 100))

        # 2. Next-Day Trade Setup Score (0-100)
        # Trade Setup Score deducts extension_penalty to prevent overextended stocks from becoming automatic BUY picks
        trade_setup_score = momentum_quality_score - extension_penalty
        trade_setup_score = float(np.clip(trade_setup_score, 0, 100))

        # Score classification
        def grade(s):
            if s >= 90: return "A+ (EXCEPTIONAL)"
            elif s >= 80: return "A (STRONG)"
            elif s >= 70: return "B (MODERATE)"
            elif s >= 60: return "C (WEAK)"
            else: return "AVOID"

        return {
            "momentum_quality_score": round(momentum_quality_score, 1),
            "momentum_grade": grade(momentum_quality_score),
            "trade_setup_score": round(trade_setup_score, 1),
            "trade_setup_grade": grade(trade_setup_score),
            "extension_penalty": extension_penalty
        }

class PriceActionEngine:
    """Analyses chart patterns, 52W High proximity, and Price Action structures."""

    @classmethod
    def analyze_price_action(cls, close, high, low, high_52w, low_52w, vwap=None, prev_high=None):
        dist_52w_high_pct = ((high_52w - close) / high_52w) * 100.0
        is_52w_breakout = close >= high_52w or high >= high_52w
        is_near_52w_high = dist_52w_high_pct <= 3.0

        if is_52w_breakout:
            proximity_status = "52W BREAKOUT"
        elif is_near_52w_high:
            proximity_status = "NEAR 52W HIGH"
        elif dist_52w_high_pct <= 10.0:
            proximity_status = "APPROACHING 52W HIGH"
        else:
            proximity_status = "FAR FROM 52W HIGH"

        # Pattern detection proxy
        vwap_reclaim = vwap is not None and close > vwap and low <= vwap
        prev_high_breakout = prev_high is not None and close > prev_high

        if is_52w_breakout:
            pattern = "52-Week High Breakout"
            pa_score = 15
        elif prev_high_breakout and vwap_reclaim:
            pattern = "Prev High Breakout & VWAP Reclaim"
            pa_score = 14
        elif is_near_52w_high:
            pattern = "Ascending Consolidation Near Highs"
            pa_score = 12
        else:
            pattern = "Momentum Continuation"
            pa_score = 10

        return {
            "pattern_name": pattern,
            "price_action_score": pa_score,
            "proximity_status": proximity_status,
            "dist_52w_high_pct": round(dist_52w_high_pct, 2),
            "vwap_reclaim": vwap_reclaim
        }

class BreakoutQualityEngine:
    """Evaluates volume, RVOL, candle strength, and ATR expansion to score breakout quality."""

    @classmethod
    def evaluate_breakout(cls, rvol, close, high, low, atr, rs_score):
        candle_body = abs(close - low)
        candle_range = max(high - low, 1e-6)
        candle_strength = candle_body / candle_range

        atr_expansion = candle_range > (1.2 * atr)

        if rvol >= 2.0 and candle_strength >= 0.7 and rs_score >= 70:
            quality = "A+ BREAKOUT"
            score = 15
        elif rvol >= 1.5 and candle_strength >= 0.6:
            quality = "A BREAKOUT"
            score = 12
        elif rvol >= 1.0:
            quality = "B BREAKOUT"
            score = 9
        elif rvol < 0.75:
            quality = "FALSE BREAKOUT RISK"
            score = 2
        else:
            quality = "WATCH"
            score = 6

        return {
            "breakout_quality": quality,
            "breakout_score": score,
            "candle_strength": round(candle_strength, 2),
            "atr_expansion": atr_expansion
        }

class PullbackExtensionFilter:
    """Detects overextended stocks and applies penalty to prevent chasing extended trades."""

    @classmethod
    def evaluate_extension(cls, close, ema20, vwap, atr):
        dist_ema20_atr = (close - ema20) / max(atr, 1e-6)
        dist_vwap_pct = abs(close - vwap) / max(vwap, 1e-6) * 100.0 if vwap else 0.0

        if dist_ema20_atr > 2.5 or dist_vwap_pct > 4.5:
            status = "HIGHLY EXTENDED"
            penalty = 25  # Heavy penalty
            recommendation = "WATCHLIST (WAIT FOR PULLBACK TO EMA/VWAP)"
        elif dist_ema20_atr > 1.5 or dist_vwap_pct > 2.5:
            status = "EXTENDED"
            penalty = 12
            recommendation = "CAUTION (REQUIRE TIGHT ENTRY)"
        else:
            status = "NORMAL"
            penalty = 0
            recommendation = "ACTIONABLE ENTRY ZONE"

        return {
            "extension_status": status,
            "penalty": penalty,
            "recommendation": recommendation,
            "dist_ema20_atr": round(dist_ema20_atr, 2),
            "dist_vwap_pct": round(dist_vwap_pct, 2)
        }

class NextDayGapScenarioEngine:
    """Generates Next-Day Gap Up, Flat Open, and Gap Down scenarios."""

    @classmethod
    def generate_scenarios(cls, close, breakout_level, atr, extension_status):
        chase_avoid_level = round(breakout_level + (1.2 * atr), 2)
        invalidation_level = round(close - (1.0 * atr), 2)

        scenario_a = (
            f"GAP UP > 2%: If opens above ₹{chase_avoid_level:.2f}, CHASE TRADE - AVOID. "
            f"Wait for pullback to ₹{breakout_level:.2f} and 15m VWAP reclaim."
        )

        scenario_b = (
            f"FLAT OPEN: Look for entry between ₹{close:.2f} - ₹{breakout_level:.2f} "
            f"on 15m candle close above ₹{breakout_level:.2f} with RVOL > 1.5."
        )

        scenario_c = (
            f"GAP DOWN: If opens below ₹{invalidation_level:.2f}, SETUP INVALIDATED. "
            f"No Trade."
        )

        return {
            "scenario_gap_up": scenario_a,
            "scenario_flat": scenario_b,
            "scenario_gap_down": scenario_c,
            "chase_avoid_level": chase_avoid_level,
            "invalidation_level": invalidation_level
        }

class NextDayEntryEngine:
    """Generates explicit Entry Zone, Confirmation Condition, and Invalidation Level."""

    @classmethod
    def generate_entry_plan(cls, close, breakout_level, atr):
        entry_min = round(min(close, breakout_level), 2)
        entry_max = round(max(close, breakout_level) + (0.3 * atr), 2)
        invalidation = round(close - (1.0 * atr), 2)

        confirmation = (
            f"15-minute candle closes above ₹{breakout_level:.2f} "
            f"with RVOL > 1.5 and sustained VWAP support."
        )

        return {
            "entry_zone_str": f"₹{entry_min:.2f} - ₹{entry_max:.2f}",
            "entry_min": entry_min,
            "entry_max": entry_max,
            "confirmation_condition": confirmation,
            "invalidation_level": invalidation
        }

class StopLossTargetEngine:
    """Calculates technical Stop Loss and Targets (T1, T2, T3) with Risk-Reward Ratio enforcement."""

    @classmethod
    def calculate_sl_and_targets(cls, entry_price, low, atr, min_rr=1.5):
        # Technical Stop Loss based on ATR & recent low
        sl_price = round(max(low - (0.5 * atr), entry_price - (1.0 * atr)), 2)
        risk_per_share = round(entry_price - sl_price, 2)

        if risk_per_share <= 0:
            risk_per_share = round(0.02 * entry_price, 2)
            sl_price = round(entry_price - risk_per_share, 2)

        # Targets based on Risk-Reward Ratio (1.5x, 2.5x, 4.0x)
        t1 = round(entry_price + (1.5 * risk_per_share), 2)
        t2 = round(entry_price + (2.5 * risk_per_share), 2)
        t3 = round(entry_price + (4.0 * risk_per_share), 2)

        rrr_t1 = round((t1 - entry_price) / risk_per_share, 2)
        rrr_t2 = round((t2 - entry_price) / risk_per_share, 2)

        return {
            "entry_price": entry_price,
            "stop_loss": sl_price,
            "target1": t1,
            "target2": t2,
            "target3": t3,
            "risk_per_share": risk_per_share,
            "rrr_t1": rrr_t1,
            "rrr_t2": rrr_t2,
            "rrr_acceptable": rrr_t1 >= min_rr
        }

class PositionSizingEngine:
    """Calculates position size, share quantity, capital required, and max loss per trade."""

    @classmethod
    def calculate_position_size(cls, trading_capital=100000.0, risk_pct=1.0, entry_price=420.0, sl_price=410.0):
        max_risk_amount = round(trading_capital * (risk_pct / 100.0), 2)  # ₹1,000 for ₹1,00,000 capital @ 1%
        risk_per_share = max(round(entry_price - sl_price, 2), 0.5)

        quantity = int(max_risk_amount / risk_per_share)
        quantity = max(quantity, 1)

        capital_required = round(quantity * entry_price, 2)
        max_loss = round(quantity * risk_per_share, 2)

        return {
            "trading_capital": trading_capital,
            "risk_pct": risk_pct,
            "max_risk_amount": max_risk_amount,
            "risk_per_share": risk_per_share,
            "quantity": quantity,
            "capital_required": capital_required,
            "max_loss": max_loss
        }

class EventRiskEngine:
    """Evaluates earnings, corporate actions, and news event risk."""

    @classmethod
    def evaluate_event_risk(cls, has_earnings_soon=False, has_corporate_action=False):
        if has_earnings_soon:
            risk_level = "HIGH"
            penalty = 20
            reason = "High Event Risk: Earnings Announcement Scheduled in < 48 Hours"
        elif has_corporate_action:
            risk_level = "MEDIUM"
            penalty = 10
            reason = "Medium Event Risk: Corporate Action Pending"
        else:
            risk_level = "LOW"
            penalty = 0
            reason = "Low Event Risk: Clean Corporate Calendar"

        return {
            "event_risk_level": risk_level,
            "event_penalty": penalty,
            "event_risk_reason": reason
        }

class MomentumNoTradeGuardrail:
    """Evaluates strict NO TRADE guardrails to protect trader capital."""

    @classmethod
    def evaluate_guardrails(cls, rrr_info, extension_info, event_info, val_info, rvol):
        reasons = []

        if not val_info["is_valid"]:
            reasons.append(f"Data Health Error: {val_info['status']}")

        if not rrr_info["rrr_acceptable"]:
            reasons.append(f"Insufficient RRR ({rrr_info['rrr_t1']:.2f} < 1.5)")

        if extension_info["extension_status"] == "HIGHLY EXTENDED":
            reasons.append("Stock is Highly Extended from VWAP/EMA20 (Chase Risk)")

        if event_info["event_risk_level"] == "HIGH":
            reasons.append("High Event Risk (Earnings / Major Event)")

        if rvol < 0.75:
            reasons.append(f"Weak Volume Confirmation (RVOL {rvol:.2f} < 0.75)")

        is_no_trade = len(reasons) > 0
        no_trade_reason = " | ".join(reasons) if is_no_trade else "PASSED ALL RISK GUARDRAILS"

        return {
            "is_no_trade": is_no_trade,
            "no_trade_reasons": reasons,
            "no_trade_summary": no_trade_reason
        }

from market_regime import MarketRegimeEngine
from research_ai import ResearchAIEngine

class MarketRegimeAdapter:
    """Adapts momentum setups based on existing NIFTY/BankNIFTY Market Regime Engine."""

    @classmethod
    def adapt_setup_for_regime(cls, nifty_regime_info):
        regime = nifty_regime_info.get("regime", "SIDEWAYS")
        confidence = nifty_regime_info.get("confidence_score", 50.0)

        if "BULLISH" in regime.upper():
            market_alignment_score = 10
            regime_action = "FAVOR LONG MOMENTUM SETUPS"
        elif "BEARISH" in regime.upper():
            market_alignment_score = 3
            regime_action = "DEMAND STRICTER CONFIRMATION (FAVOR SHORT SETUPS)"
        else:
            market_alignment_score = 6
            regime_action = "REQUIRE HIGHER CONFIRMATION FOR LONGS"

        return {
            "market_regime": regime,
            "regime_confidence": confidence,
            "market_alignment_score": market_alignment_score,
            "regime_action": regime_action
        }

class SignalLifecycleManager:
    """Tracks signal state transitions across the 9-stage lifecycle."""

    LIFECYCLE_STAGES = [
        "CANDIDATE", "WATCHLIST", "PRE-MARKET", "WAIT",
        "CONFIRMED", "ACTIVE", "WEAKENING", "INVALIDATED", "CLOSED"
    ]

    @classmethod
    def resolve_status(cls, is_no_trade, setup_score, extension_status, is_confirmed=False):
        if is_no_trade:
            return "INVALIDATED"
        elif extension_status == "HIGHLY EXTENDED":
            return "WATCHLIST"
        elif is_confirmed:
            return "CONFIRMED"
        elif setup_score >= 75:
            return "WAIT"
        else:
            return "CANDIDATE"

class AIExplanationSynthesizer:
    """Generates 'WHY THIS STOCK?' structured AI rationale and key risk factors."""

    @classmethod
    def generate_explanation(cls, symbol, trend_info, mom_info, rs_info, pa_info, rrr_info, no_trade_info):
        why_bullets = [
            f"DMA Alignment: {trend_info['trend_classification']}",
            f"Volume Confirmation: RVOL {mom_info['rvol_label']}",
            f"Relative Strength: {rs_info['rs_classification']} vs NIFTY 50",
            f"Chart Pattern: {pa_info['pattern_name']} ({pa_info['proximity_status']})",
            f"Price-Volume Behavior: {mom_info['pv_relationship']}",
            f"Acceptable Risk-Reward: {rrr_info['rrr_t1']:.2f} RRR to Target 1"
        ]

        risk_bullets = []
        if pa_info['dist_52w_high_pct'] > 0 and pa_info['dist_52w_high_pct'] <= 5.0:
            risk_bullets.append(f"Near 52W Overhead Resistance ({pa_info['dist_52w_high_pct']:.1f}% below 52W High)")
        if no_trade_info['is_no_trade']:
            risk_bullets.extend(no_trade_info['no_trade_reasons'])
        if not risk_bullets:
            risk_bullets.append("Standard Market Volatility & Gap Risk")

        return {
            "why_selected": why_bullets,
            "key_risks": risk_bullets
        }

def process_nextday_stock_intelligence(stock_data, nifty_regime_info=None):
    """Master pipeline wrapper running all 4 phases of Next-Day Momentum Stock Intelligence Engine."""
    if nifty_regime_info is None:
        nifty_regime_info = {"regime": "🟢 BULLISH_TRENDING", "confidence_score": 75.0}

    # Step 1: Validation
    val_res = MomentumDataValidator.validate_stock_data(stock_data)
    if not val_res["is_valid"]:
        return {"symbol": stock_data.get("symbol", "UNKNOWN"), "status": "NO TRADE", "reason": val_res["status"]}

    # Step 2: Technical Engines
    trend_res = TrendEngine.classify_trend(
        stock_data['Close'], stock_data['dma20'], stock_data['dma50'], stock_data['dma100'], stock_data['dma200'],
        stock_data['ema9'], stock_data['ema21'], stock_data['ema50'], stock_data['ema200']
    )

    mom_res = MomentumRvolEngine.classify_momentum(
        stock_data['rsi'], stock_data['adx'], stock_data.get('price_change_pct', 1.0), stock_data['rvol']
    )

    rs_res = RelativeStrengthEngine.calculate_relative_strength(
        stock_data.get('car_1y', 40.0), stock_data.get('nifty_car_1y', 15.0)
    )

    pa_res = PriceActionEngine.analyze_price_action(
        stock_data['Close'], stock_data['High'], stock_data['Low'],
        stock_data.get('high_52w', stock_data['High']), stock_data.get('low_52w', stock_data['Low']),
        stock_data.get('vwap', stock_data['Close']), stock_data.get('prev_high')
    )

    bo_res = BreakoutQualityEngine.evaluate_breakout(
        stock_data['rvol'], stock_data['Close'], stock_data['High'], stock_data['Low'], stock_data['atr'], rs_res['rs_score']
    )

    ext_res = PullbackExtensionFilter.evaluate_extension(
        stock_data['Close'], stock_data.get('ema20', stock_data.get('ema21', stock_data['Close'])), stock_data.get('vwap', stock_data['Close']), stock_data['atr']
    )

    regime_res = MarketRegimeAdapter.adapt_setup_for_regime(nifty_regime_info)

    # Step 3: Dual Scoring
    scores = MomentumDualScorer.calculate_scores(
        trend_res, mom_res, rs_res, pa_res['price_action_score'],
        risk_reward_score=5, liquidity_score=5, event_risk_score=5,
        market_align_score=regime_res['market_alignment_score'],
        extension_penalty=ext_res['penalty']
    )

    # Step 4: Next-Day Scenarios & Risk Plan
    scenarios = NextDayGapScenarioEngine.generate_scenarios(
        stock_data['Close'], stock_data.get('breakout_level', stock_data['High']), stock_data['atr'], ext_res['extension_status']
    )

    entry_plan = NextDayEntryEngine.generate_entry_plan(
        stock_data['Close'], stock_data.get('breakout_level', stock_data['High']), stock_data['atr']
    )

    sl_t_res = StopLossTargetEngine.calculate_sl_and_targets(
        stock_data['Close'], stock_data['Low'], stock_data['atr']
    )

    pos_sizing = PositionSizingEngine.calculate_position_size(
        trading_capital=100000.0, risk_pct=1.0, entry_price=stock_data['Close'], sl_price=sl_t_res['stop_loss']
    )

    event_res = EventRiskEngine.evaluate_event_risk(
        has_earnings_soon=stock_data.get('has_earnings_soon', False)
    )

    guardrails = MomentumNoTradeGuardrail.evaluate_guardrails(
        sl_t_res, ext_res, event_res, val_res, stock_data['rvol']
    )

    lifecycle_status = SignalLifecycleManager.resolve_status(
        guardrails['is_no_trade'], scores['trade_setup_score'], ext_res['extension_status']
    )

    ai_explanation = AIExplanationSynthesizer.generate_explanation(
        stock_data.get('symbol', 'NSE'), trend_res, mom_res, rs_res, pa_res, sl_t_res, guardrails
    )

    return {
        "symbol": stock_data.get("symbol", "NSE_STOCK"),
        "close": round(stock_data['Close'], 2),
        "direction": "LONG",
        "setup_name": pa_res['pattern_name'],
        "momentum_quality_score": scores['momentum_quality_score'],
        "trade_setup_score": scores['trade_setup_score'],
        "momentum_grade": scores['momentum_grade'],
        "trade_setup_grade": scores['trade_setup_grade'],
        "trend_info": trend_res,
        "momentum_info": mom_res,
        "relative_strength_info": rs_res,
        "price_action_info": pa_res,
        "breakout_quality": bo_res,
        "extension_info": ext_res,
        "market_regime_info": regime_res,
        "entry_plan": entry_plan,
        "risk_plan": sl_t_res,
        "position_sizing": pos_sizing,
        "scenarios": scenarios,
        "event_risk_info": event_res,
        "guardrail_eval": guardrails,
        "status": lifecycle_status,
        "ai_explanation": ai_explanation
    }



