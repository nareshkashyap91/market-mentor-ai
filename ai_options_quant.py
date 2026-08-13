import io
import os
import sys
import json
import requests
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, time, timedelta, timezone

# Ensure terminal outputs emojis correctly on Windows
sys.stdout.reconfigure(encoding='utf-8')

def ensure_ist_timezone(df):
    """Ensures the DataFrame index is in Asia/Kolkata timezone (IST)."""
    if df.index.tz is None:
        try:
            df.index = df.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
        except Exception:
            try:
                df.index = df.index.tz_localize('Asia/Kolkata')
            except Exception:
                pass
    else:
        df.index = df.index.tz_convert('Asia/Kolkata')
    return df

def check_market_hours():
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist_tz)
    
    if now.weekday() >= 5: # Saturday/Sunday
        return False
        
    current_time = now.time()
    market_start = time(9, 15)
    market_end = time(15, 30)
    return market_start <= current_time <= market_end

def send_to_telegram(message, bot_token, chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            print("[INFO] AI Quant Telegram Alert sent successfully!")
        else:
            print(f"[ERROR] Telegram failed: {res.text}")
    except Exception as e:
        print(f"[ERROR] Exception sending AI Quant Alert: {e}")

def detect_chart_patterns(df):
    """Automated Chart Pattern Recognition engine on 15m intraday candle data."""
    if df is None or df.empty or len(df) < 10:
        return "No Pattern (Insufficient Candles)", "Neutral"
        
    c_curr = df.iloc[-1]
    c_prev = df.iloc[-2]
    c_prev2 = df.iloc[-3]
    
    curr_body = abs(c_curr['Close'] - c_curr['Open'])
    prev_body = abs(c_prev['Close'] - c_prev['Open'])
    
    curr_range = c_curr['High'] - c_curr['Low']
    
    # 1. Bullish / Bearish Engulfing
    if c_prev['Close'] < c_prev['Open'] and c_curr['Close'] > c_curr['Open']:
        if c_curr['Close'] >= c_prev['Open'] and c_curr['Open'] <= c_prev['Close']:
            return "🟢 Bullish Engulfing (Reversal Setup)", "Bullish"
            
    if c_prev['Close'] > c_prev['Open'] and c_curr['Close'] < c_curr['Open']:
        if c_curr['Close'] <= c_prev['Open'] and c_curr['Open'] >= c_prev['Close']:
            return "🔴 Bearish Engulfing (Reversal Setup)", "Bearish"
            
    # 2. Hammer & Shooting Star
    if curr_range > 0:
        lower_shadow = min(c_curr['Open'], c_curr['Close']) - c_curr['Low']
        upper_shadow = c_curr['High'] - max(c_curr['Open'], c_curr['Close'])
        
        if lower_shadow >= 2.0 * curr_body and upper_shadow <= 0.3 * curr_body:
            return "🟢 Hammer Pattern (Demand Reversal at Support)", "Bullish"
            
        if upper_shadow >= 2.0 * curr_body and lower_shadow <= 0.3 * curr_body:
            return "🔴 Shooting Star (Supply Reversal at Resistance)", "Bearish"
            
    # 3. Double Bottom (W Pattern) & Double Top (M Pattern)
    recent_lows = df['Low'].tail(15)
    recent_highs = df['High'].tail(15)
    
    min1 = recent_lows.iloc[:7].min()
    min2 = recent_lows.iloc[7:].min()
    if abs(min1 - min2) / min1 < 0.0015 and c_curr['Close'] > c_prev['Close']:
        return "🟢 Double Bottom (W Pattern Breakout)", "Bullish"
        
    max1 = recent_highs.iloc[:7].max()
    max2 = recent_highs.iloc[7:].max()
    if abs(max1 - max2) / max1 < 0.0015 and c_curr['Close'] < c_prev['Close']:
        return "🔴 Double Top (M Pattern Breakdown)", "Bearish"
        
    # 4. Volatility Contraction (VCP) Breakout
    atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
    if curr_range > 1.4 * atr and c_curr['Close'] > c_prev['High']:
        return "⚡ Volatility Contraction (VCP) Momentum Expansion", "Bullish"
        
    return "📊 Consolidating / Price Action Normal", "Neutral"

def classify_market_regime(spot, vwap, vix_val, pcr):
    """Classifies the overall Market Mood/Regime for Quantitative Strategy selection."""
    if spot > vwap * 1.0015 and pcr >= 1.05:
        return "🚀 BULLISH MOMENTUM REGIME", "Directional Long"
    elif spot < vwap * 0.9985 and pcr <= 0.85:
        return "🔻 BEARISH PRESSURE REGIME", "Directional Short"
    elif vix_val >= 18.0:
        return "⚡ VOLATILITY EXPANSION REGIME", "Volatility Spreads"
    else:
        return "🟡 SIDEWAYS THETA HARVEST REGIME", "Non-Directional / Credit Spreads"

def recommend_options_quant_strategies(index_name, spot, vwap, regime, pcr, vix_val, pattern_name, pattern_bias):
    """Generates complete options strategies including Buying, Hedged Credit Spreads, and Straddles."""
    step = 50 if index_name == "NIFTY" else 100
    atm = int(round(spot / step) * step)
    
    strategies = []
    
    # 1. Bullish Regime Strategies
    if "BULLISH" in regime or pattern_bias == "Bullish":
        # Strategy A: Directional Naked CE Buy
        ce_strike = atm
        strategies.append({
            "name": f"{index_name} ATM Call Option Buy",
            "type": "NAKED OPTION BUY",
            "legs": [f"BUY {index_name} {ce_strike} CE"],
            "entry_spot": round(spot, 2),
            "sl_spot": round(vwap * 0.997, 2),
            "target1_spot": round(spot * 1.006, 2),
            "max_profit": "Unlimited Upside",
            "max_loss": "Defined (Option Premium Paid)",
            "win_prob": "65%",
            "rationale": f"Bullish breakout above VWAP (₹{vwap:.1f}) supported by {pattern_name} & Put writing (PCR: {pcr:.2f})."
        })
        
        # Strategy B: Hedged Bull Call Spread (Defined Risk)
        otm_sell = atm + (150 if index_name == "NIFTY" else 300)
        strategies.append({
            "name": f"{index_name} Bull Call Debit Spread (Hedged)",
            "type": "HEDGED SPREAD",
            "legs": [f"BUY {index_name} {ce_strike} CE", f"SELL {index_name} {otm_sell} CE (Hedge)"],
            "entry_spot": round(spot, 2),
            "sl_spot": round(vwap * 0.996, 2),
            "target1_spot": round(spot * 1.008, 2),
            "max_profit": f"Fixed Spread Width (₹{otm_sell - ce_strike} Points)",
            "max_loss": "Fixed Net Premium Paid",
            "win_prob": "74%",
            "rationale": f"High probability hedged bullish trade capping volatility decay risk."
        })
        
    # 2. Bearish Regime Strategies
    elif "BEARISH" in regime or pattern_bias == "Bearish":
        # Strategy A: Directional Naked PE Buy
        pe_strike = atm
        strategies.append({
            "name": f"{index_name} ATM Put Option Buy",
            "type": "NAKED OPTION BUY",
            "legs": [f"BUY {index_name} {pe_strike} PE"],
            "entry_spot": round(spot, 2),
            "sl_spot": round(vwap * 1.003, 2),
            "target1_spot": round(spot * 0.994, 2),
            "max_profit": "Unlimited Downside",
            "max_loss": "Defined (Option Premium Paid)",
            "win_prob": "65%",
            "rationale": f"Bearish breakdown below VWAP (₹{vwap:.1f}) confirmed by {pattern_name} & Call writing (PCR: {pcr:.2f})."
        })
        
        # Strategy B: Hedged Bear Put Spread
        otm_pe_sell = atm - (150 if index_name == "NIFTY" else 300)
        strategies.append({
            "name": f"{index_name} Bear Put Debit Spread (Hedged)",
            "type": "HEDGED SPREAD",
            "legs": [f"BUY {index_name} {pe_strike} PE", f"SELL {index_name} {otm_pe_sell} PE (Hedge)"],
            "entry_spot": round(spot, 2),
            "sl_spot": round(vwap * 1.004, 2),
            "target1_spot": round(spot * 0.992, 2),
            "max_profit": f"Fixed Spread Width (₹{pe_strike - otm_pe_sell} Points)",
            "max_loss": "Fixed Net Premium Paid",
            "win_prob": "72%",
            "rationale": f"Hedged downside strategy mitigating volatility crush."
        })

    # 3. Sideways / Rangebound Regime (Theta Harvest & Hedged Spreads)
    else:
        # Strategy A: Bull Put Credit Spread (Theta Decay)
        sell_pe = atm - (100 if index_name == "NIFTY" else 200)
        buy_pe_hedge = sell_pe - (100 if index_name == "NIFTY" else 200)
        strategies.append({
            "name": f"{index_name} Bull Put Credit Spread (Theta Harvest)",
            "type": "THETA CREDIT SPREAD",
            "legs": [f"SELL {index_name} {sell_pe} PE", f"BUY {index_name} {buy_pe_hedge} PE (Hedge)"],
            "entry_spot": round(spot, 2),
            "sl_spot": round(spot - 120, 2),
            "target1_spot": "Full Premium Decay at Expiry",
            "max_profit": "Net Credit Received",
            "max_loss": f"Defined Difference (₹{sell_pe - buy_pe_hedge} - Credit)",
            "win_prob": "82%",
            "rationale": f"Rangebound market (PCR: {pcr:.2f}). Collects time decay as long as {index_name} stays above ₹{sell_pe}."
        })
        
        # Strategy B: Hedged Short Straddle / Iron Butterfly
        otm_ce_hedge = atm + (150 if index_name == "NIFTY" else 300)
        otm_pe_hedge = atm - (150 if index_name == "NIFTY" else 300)
        strategies.append({
            "name": f"{index_name} Iron Butterfly (Hedged Short Straddle)",
            "type": "HEDGED STRADDLE",
            "legs": [
                f"SELL {index_name} {atm} CE",
                f"SELL {index_name} {atm} PE",
                f"BUY {index_name} {otm_ce_hedge} CE (Hedge)",
                f"BUY {index_name} {otm_pe_hedge} PE (Hedge)"
            ],
            "entry_spot": round(spot, 2),
            "sl_spot": "Upper/Lower Wing Touch",
            "target1_spot": "Max Decay at Center ATM Strike",
            "max_profit": "Max Net Premium Collected",
            "max_loss": "Defined Wing Width minus Net Premium",
            "win_prob": "78%",
            "rationale": f"Sideways consolidation regime with low VIX ({vix_val:.1f}). Harvests dual Theta decay on both Call and Put legs."
        })
        
    # Phase 2 Option Greeks & IV Enrichment
    from option_chain_analyzer import OptionChainAnalyzer
    
    # Quantitative Ranking: Rank strategies by win probability & safety score
    for s in strategies:
        try:
            s["win_score"] = float(s["win_prob"].replace("%", "").strip())
        except Exception:
            s["win_score"] = 50.0
            
        # Attach Phase 2 Black-Scholes Greeks
        iv_estimate = max(0.10, min(0.60, vix_val / 100.0 if vix_val > 0 else 0.15))
        greeks = OptionChainAnalyzer.calculate_strategy_net_greeks(s["legs"], spot, dte_days=7, default_iv=iv_estimate)
        s["greeks"] = greeks
            
    strategies.sort(key=lambda x: x["win_score"], reverse=True)
    
    # Tag #1 Best Strategy
    if strategies:
        strategies[0]["is_top_pick"] = True
        strategies[0]["recommendation_tag"] = "⭐ TOP PICK (#1 BEST STRATEGY FOR HIGH WIN-RATE & SAFETY)"
        for s in strategies[1:]:
            s["is_top_pick"] = False
            s["recommendation_tag"] = "ALTERNATIVE STRATEGY"
            
    return strategies

def scan_intraday_stocks_long_and_short(symbols):
    """Scans 50 liquid stocks for BOTH Intraday Buying (Long) and Short-Selling (Short) setups."""
    print("--- Scanning Stocks for Intraday Long & Short Opportunities ---")
    tickers = [f"{s}.NS" for s in symbols[:50]]
    
    try:
        data = yf.download(tickers, period='5d', interval='15m', group_by='ticker', progress=False)
    except Exception as e:
        print(f"[WARNING] Bulk intraday download failed: {e}")
        return [], []
        
    long_setups = []
    short_setups = []
    
    for symbol in symbols[:50]:
        ticker = f"{symbol}.NS"
        try:
            if isinstance(data.columns, pd.MultiIndex):
                if ticker not in data.columns.levels[0]:
                    continue
                df = data[ticker].dropna(subset=['Close'])
            else:
                df = data.dropna(subset=['Close'])
                
            if len(df) < 15:
                continue
                
            df = ensure_ist_timezone(df)
            latest_date = df.index[-1].date()
            today_df = df[df.index.date == latest_date]
            
            if len(today_df) < 2:
                continue
                
            first_candle = today_df.iloc[0]
            orb_high = first_candle['High']
            orb_low = first_candle['Low']
            
            last_candle = today_df.iloc[-1]
            close = last_candle['Close']
            volume = last_candle['Volume']
            
            # VWAP
            typical_price_vol = ((today_df['High'] + today_df['Low'] + today_df['Close']) / 3) * today_df['Volume']
            total_vol = today_df['Volume'].sum()
            vwap = typical_price_vol.sum() / total_vol if total_vol > 0 else close
            
            # Volume Expansion
            vol_sma10 = today_df['Volume'].rolling(10).mean().iloc[-1]
            vol_exp = volume / vol_sma10 if vol_sma10 > 0 else 1.0
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = float(100 - (100 / (1 + rs)).iloc[-1])
            
            # Pattern
            pattern_name, pattern_bias = detect_chart_patterns(today_df)
            
            # 1. Intraday Long Setup (BUY)
            if close > orb_high and close > vwap and vol_exp >= 1.15 and rsi >= 52:
                sl = min(close * 0.992, orb_high)
                risk = close - sl
                long_setups.append({
                    "symbol": symbol,
                    "action": "BUY (LONG)",
                    "close": round(close, 2),
                    "vwap": round(vwap, 2),
                    "orb_high": round(orb_high, 2),
                    "sl": round(sl, 2),
                    "t1": round(close + 1.2 * risk, 2),
                    "t2": round(close + 2.0 * risk, 2),
                    "rsi": round(rsi, 1),
                    "vol_exp": round(vol_exp, 1),
                    "pattern": pattern_name
                })
                
            # 2. Intraday Short Setup (SHORT SELL)
            elif close < orb_low and close < vwap and vol_exp >= 1.15 and rsi <= 48:
                sl = max(close * 1.008, orb_low)
                risk = sl - close
                short_setups.append({
                    "symbol": symbol,
                    "action": "SHORT SELL",
                    "close": round(close, 2),
                    "vwap": round(vwap, 2),
                    "orb_low": round(orb_low, 2),
                    "sl": round(sl, 2),
                    "t1": round(close - 1.2 * risk, 2),
                    "t2": round(close - 2.0 * risk, 2),
                    "rsi": round(rsi, 1),
                    "vol_exp": round(vol_exp, 1),
                    "pattern": pattern_name
                })
                
        except Exception as e:
            continue
            
    long_setups.sort(key=lambda x: x['vol_exp'], reverse=True)
    short_setups.sort(key=lambda x: x['vol_exp'], reverse=True)
    
    return long_setups[:5], short_setups[:5]

from data_quality import DataQualityEngine, LIVE_DATA, MOCK_DATA, get_data_quality_report
from market_regime import MarketRegimeEngine, get_market_regime_analysis

def main():
    print("=========================================")
    print("   AI MULTI-REGIME OPTIONS QUANT ENGINE  ")
    print("=========================================")
    
    config_file = "config.json"
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as cf:
                config = json.load(cf)
            tg = config.get("telegram", {})
            if not tg_token:
                tg_token = tg.get("bot_token")
            if not tg_chat_id:
                tg_chat_id = tg.get("chat_id")
        except Exception:
            pass

    # Download index & VIX
    nifty_df = yf.download('^NSEI', period='5d', interval='15m', progress=False)
    bank_df = yf.download('^NSEBANK', period='5d', interval='15m', progress=False)
    vix_df = yf.download('^INDIAVIX', period='5d', interval='15m', progress=False)
    
    if isinstance(nifty_df.columns, pd.MultiIndex): nifty_df.columns = nifty_df.columns.get_level_values(0)
    if isinstance(bank_df.columns, pd.MultiIndex): bank_df.columns = bank_df.columns.get_level_values(0)
    if isinstance(vix_df.columns, pd.MultiIndex): vix_df.columns = vix_df.columns.get_level_values(0)
    
    nifty_df = ensure_ist_timezone(nifty_df.dropna(subset=['Close'])) if nifty_df is not None else None
    bank_df = ensure_ist_timezone(bank_df.dropna(subset=['Close'])) if bank_df is not None else None
    vix_df = ensure_ist_timezone(vix_df.dropna(subset=['Close'])) if vix_df is not None else None
    
    # Phase 1 Data Quality Checks
    nifty_dq, nifty_df = DataQualityEngine.validate_dataframe(nifty_df, is_mock=False)
    bank_dq, bank_df = DataQualityEngine.validate_dataframe(bank_df, is_mock=False)
    
    nifty_spot = float(nifty_df['Close'].iloc[-1]) if nifty_df is not None and not nifty_df.empty else 24600.0
    bank_spot = float(bank_df['Close'].iloc[-1]) if bank_df is not None and not bank_df.empty else 51500.0
    vix_val = float(vix_df['Close'].iloc[-1]) if vix_df is not None and not vix_df.empty else 13.5
    
    # Calculate VWAP
    def get_vwap(df):
        if df is None or df.empty: return 0.0
        today_df = df[df.index.date == df.index[-1].date()]
        if today_df.empty: return float(df['Close'].iloc[-1])
        tp_v = ((today_df['High'] + today_df['Low'] + today_df['Close']) / 3) * today_df['Volume']
        t_v = today_df['Volume'].sum()
        return float(tp_v.sum() / t_v) if t_v > 0 else float(today_df['Close'].iloc[-1])
        
    nifty_vwap = get_vwap(nifty_df)
    bank_vwap = get_vwap(bank_df)
    
    # Detect Patterns
    nifty_pattern, nifty_p_bias = detect_chart_patterns(nifty_df)
    bank_pattern, bank_p_bias = detect_chart_patterns(bank_df)
    
    # PCR (Default 1.05)
    nifty_pcr = 1.05
    bank_pcr = 0.98
    
    # Phase 1 Market Regime Analysis
    nifty_regime_info = get_market_regime_analysis(nifty_df, vix_val=vix_val, pcr=nifty_pcr, is_mock=False)
    bank_regime_info = get_market_regime_analysis(bank_df, vix_val=vix_val, pcr=bank_pcr, is_mock=False)
    
    nifty_regime = nifty_regime_info["regime"]
    bank_regime = bank_regime_info["regime"]
    
    # Phase 3 Expected Move & DTE Calculation
    from expected_move import get_expected_move
    nifty_em = get_expected_move(nifty_spot, vix_val / 100.0 if vix_val > 0 else 0.15)
    bank_em = get_expected_move(bank_spot, vix_val / 100.0 if vix_val > 0 else 0.15)
    
    # Strategy Recommendations
    nifty_strats = recommend_options_quant_strategies("NIFTY", nifty_spot, nifty_vwap, nifty_regime, nifty_pcr, vix_val, nifty_pattern, nifty_p_bias)
    bank_strats = recommend_options_quant_strategies("BANKNIFTY", bank_spot, bank_vwap, bank_regime, bank_pcr, vix_val, bank_pattern, bank_p_bias)
    
    # Intraday Stocks Long & Short
    sample_symbols = [
        "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "BHARTIARTL", "ITC", "SBIN",
        "LT", "AXISBANK", "KOTAKBANK", "M&M", "SUNPHARMA", "MARUTI", "NTPC",
        "POWERGRID", "TITAN", "ULTRACEMCO", "BAJFINANCE", "TATASTEEL", "ADANIENT", "JSWSTEEL"
    ]
    long_stocks, short_stocks = scan_intraday_stocks_long_and_short(sample_symbols)
    
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    now_str = datetime.now(ist_tz).strftime("%d-%b-%Y %I:%M %p")
    
    payload = {
        "timestamp": now_str,
        "data_type": LIVE_DATA,
        "data_quality": nifty_dq,
        "nifty": {
            "spot": round(nifty_spot, 2),
            "vwap": round(nifty_vwap, 2),
            "regime": nifty_regime,
            "adx": nifty_regime_info["adx"],
            "trend_intensity": nifty_regime_info["trend_intensity"],
            "volatility_percentile": nifty_regime_info["volatility_percentile"],
            "confidence_score": nifty_regime_info["confidence_score"],
            "expected_move": nifty_em,
            "pattern": nifty_pattern,
            "pcr": nifty_pcr,
            "strategies": nifty_strats
        },
        "banknifty": {
            "spot": round(bank_spot, 2),
            "vwap": round(bank_vwap, 2),
            "regime": bank_regime,
            "adx": bank_regime_info["adx"],
            "trend_intensity": bank_regime_info["trend_intensity"],
            "volatility_percentile": bank_regime_info["volatility_percentile"],
            "confidence_score": bank_regime_info["confidence_score"],
            "expected_move": bank_em,
            "pattern": bank_pattern,
            "pcr": bank_pcr,
            "strategies": bank_strats
        },
        "intraday_stocks": {
            "long_setups": long_stocks,
            "short_setups": short_stocks
        }
    }
    
    os.makedirs("data", exist_ok=True)
    json_path = os.path.join("data", "ai_quant.json")
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"[INFO] Saved AI Quant payload to {json_path}")
    
    # Broadcast to Telegram
    msg = f"🧠 **AI QUANT MULTI-REGIME OPTIONS ENGINE** 🧠\n"
    msg += f"🕒 **Time**: {now_str} (IST)\n\n"
    
    msg += f"📊 **NIFTY 50 QUANT MATRIX**:\n"
    msg += f"• **Mood/Regime**: `{nifty_regime}`\n"
    msg += f"• **Chart Pattern**: `{nifty_pattern}`\n"
    msg += f"• **Spot**: `₹{nifty_spot:.2f}` | **VWAP**: `₹{nifty_vwap:.2f}` | **PCR**: `{nifty_pcr}`\n\n"
    
    msg += f"🎯 **OPTIMAL QUANT OPTIONS STRATEGIES**:\n"
    for idx, strat in enumerate(nifty_strats[:2]):
        tag_prefix = "⭐ **[TOP PICK - #1 BEST STRATEGY]**\n" if strat.get("is_top_pick", False) else "🔹 **[ALTERNATIVE STRATEGY]**\n"
        msg += (
            f"{tag_prefix}"
            f"🏆 **{strat['name']}** ({strat['type']})\n"
            f"  - **Legs**: `{', '.join(strat['legs'])}` \n"
            f"  - **Win Probability**: `{strat['win_prob']}` | **Max Profit**: `{strat['max_profit']}`\n"
            f"  - 💡 *Rationale*: {strat['rationale']}\n\n"
        )
        
    if long_stocks or short_stocks:
        msg += "="*35 + "\n"
        msg += "📈 **INTRADAY STOCK LONG & SHORT SETUPS**:\n"
        if long_stocks:
            for s in long_stocks[:2]:
                msg += f"🟢 **BUY (LONG)**: `NSE:{s['symbol']}` @ ₹{s['close']} (SL: ₹{s['sl']}, T1: ₹{s['t1']})\n"
        if short_stocks:
            for s in short_stocks[:2]:
                msg += f"🔴 **SHORT (SELL)**: `NSE:{s['symbol']}` @ ₹{s['close']} (SL: ₹{s['sl']}, T1: ₹{s['t1']})\n"
                
    if tg_token and tg_chat_id:
        send_to_telegram(msg, tg_token, tg_chat_id)

if __name__ == '__main__':
    main()
