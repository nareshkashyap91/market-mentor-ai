# Market Mentor AI — V3.0 Master Upgrade Plan

This document details the architectural evolution, new components, upgraded engines, deprecations, backtesting mandates, and manual approval guardrails for upgrading **Market Mentor AI** to **V3.0**.

---

## 🏛️ V3.0 Central Architecture Flow

```
DATA LAYER
    ↓
DATA QUALITY ENGINE (freshness, metadata, status: LIVE/STALE/MISSING/INVALID/CONFLICTING)
    ↓
MARKET REGIME ENGINE (10 Regimes: TRENDING_BULLISH, TRENDING_BEARISH, SIDEWAYS, HIGH_VOLATILITY, etc.)
    ↓
STRATEGY ROUTER (Routes setups based on active regime)
    ↓
STRATEGY ENGINES (Momentum RS, Intraday ORB MTF, Liquidity Sweep Proxy, Options Delta/IV)
    ↓
CONFLUENCE ENGINE (Multi-factor weighting, MTF alignment check)
    ↓
TRADE QUALITY GATE (Configurable 4+ independent confirmations; NO TRADE generated if gate fails)
    ↓
RISK ENGINE (Daily Loss Cap, Drawdown Limit, Consecutive Loss Circuit Breaker)
    ↓
EXECUTION ENGINE (Paper Trading Order Validation & Slippage Model)
    ↓
AI EXPLANATION ENGINE ("Why this stock? Why this strategy? What invalidates it? What changes AI's mind?")
    ↓
TELEGRAM INTELLIGENCE (A/A+ Setups, NO TRADE Explanations, /status, /market, /risk, /report)
    ↓
TRADE JOURNAL (30+ fields per trade: PnL, R_multiple, MFE, MAE, Holding Time)
    ↓
PERFORMANCE ENGINE (Win Rate, Profit Factor, Expectancy by Strategy + Regime)
```

---

## 📂 Component Classification Matrix

### 🟢 EXISTING (Preserved Working Infrastructure)
- **`run_local_scheduler.py`**: 15-minute pulse scanner with weekend guardrails.
- **`run_telegram_bot_listener.py`**: 2-Way interactive polling listener daemon.
- **`paper_trading.py`**: Virtual order placement and portfolio tracking.
- **`position_manager.py`**: Signal database synchronization and SQLite ledger.
- **`chart_plotter_engine.py`**: Matplotlib HD chart image renderer.
- **`whatsapp_notifier.py`**: CallMeBot WhatsApp alert gateway (Unconfigured fallback).

---

### 🟡 UPGRADE (Enhanced Functional Modules)
- **`data_quality.py`**: Upgraded to central **Data Quality Engine** with `LIVE`, `FRESH`, `STALE`, `MISSING`, `INVALID`, `CONFLICTING` metadata.
- **`market_regime.py`**: Expanded from 3 regimes to **10 Centralized Regimes** (`TRENDING_BULLISH`, `TRENDING_BEARISH`, `SIDEWAYS`, `HIGH_VOLATILITY`, `LOW_VOLATILITY`, `BREAKOUT`, `BREAKDOWN`, `MEAN_REVERSION`, `EVENT_RISK`, `UNSAFE`).
- **`momentum_intelligence_engine.py`**: Upgraded to V3 with Mansfield RS vs Nifty, RS vs Sector, Sector Breadth, ATR Compression, and A+/A/B ranking.
- **`intraday_orb_vwap_precision.py`**: Upgraded with 15m/30m/45m Opening Ranges, Retest tracking, and Market Structure ($\text{BOS}$, $\text{CHOCH}$, $\text{HH}$, $\text{HL}$, $\text{LH}$, $\text{LL}$).
- **`smc_liquidity_sweep_engine.py`**: Relabeled as **LIQUIDITY SWEEP / STOP-RUN PROXY** (avoiding institutional certainty claims).
- **`iv_skew_maxpain_engine.py` & `option_greeks.py`**: Upgraded to V3 with Delta-based strike selection and `MODEL_ESTIMATED_POP`.
- **`mcx_commodity_engine.py`**: Upgraded with dynamic **EIA Event Protection Engine** and configurable pre/post event lockouts.
- **`fii_dii_engine.py`**: Relabeled as **POSITIONING PROXY** (FII Cash, DII Cash, Futures Long Ratio).
- **`daily_drawdown_circuit_breaker.py` & `adaptive_risk_regime.py`**: Upgraded to V3 Risk Engine with strategy loss limits and correlated position caps.
- **`telegram_bot_interactive.py`**: Upgraded with expanded slash commands (`/market`, `/risk`, `/positions`, `/performance`, `/report`, `/pause`, `/resume`).
- **`index.html` & `app.js`**: Redesigned to **Trader Command Center UI** with prop-terminal aesthetics and Risk Cockpit.

---

## 🔵 NEW (Newly Created System Engines)
- **`data_quality_engine.py`**: Central Data Quality Gate.
- **`strategy_router.py`**: Regime-based Strategy Selector.
- **`confluence_engine.py`**: Multi-factor signal confluence calculator.
- **`trade_quality_gate.py`**: Central Trade Gate (blocks setups with < 4 confirmations).
- **`ai_explanation_engine.py`**: Generates mandatory AI trade rationales ("Why this stock? What invalidates it? What changes AI's mind?").
- **`fomo_overextension_engine.py`**: FOMO and VWAP/ATR overextension risk classifier.
- **`market_session_engine.py`**: Handles Pre-market, Opening, Morning Trend, Midday, Afternoon, Closing sessions.
- **`walk_forward_engine.py`**: In-sample, out-of-sample, and paper trading validation framework.
- **`strategy_health_engine.py`**: Rolling performance monitor (`HEALTHY`, `DEGRADED`, `DISABLED`).

---

## 🔴 DEPRECATED (Replaced / Removed Practices)
- **Direct Telegram Signal Broadcasting:** Strategies no longer send Telegram messages directly without passing through `TradeQualityGate`.
- **Certainty Claims:** Terms like "Smart Money Certainty", "100% Accuracy", and "Guaranteed Profit" are strictly deprecated and removed.
- **Fixed Win Rate Claims:** Hardcoded "78% Win Rate" is replaced by dynamic `MODEL_ESTIMATED_POP`.

---

## 🧪 REQUIRES_BACKTEST (Validation Mandate)
- **V3 Next-Day Momentum RS vs Sector Rules**
- **30m & 45m ORB Breakout Retest Strategies**
- **Delta-Based Options Strike Selector ($\Delta = 0.35 / 0.65$)**
- **Trailing Stop Loss Management Rules**

---

## ✋ REQUIRES_MANUAL_APPROVAL (Safety Guardrail)
- **Parameter Mining / Auto-Optimization:** AI self-learning may recommend parameter adjustments, but ANY change to live parameters requires: `PROPOSAL ➔ BACKTEST ➔ OUT-OF-SAMPLE TEST ➔ PAPER TRADE ➔ MANUAL APPROVAL ➔ PRODUCTION`.
- **Trading Circuit Breaker Reset:** Resetting trading after a Daily Drawdown Circuit Breaker trip requires explicit manual user approval.
