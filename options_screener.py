import io
import os
import sys
import json
import requests
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
    # Indian Standard Time (IST) is UTC + 5:30
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist_tz)
    
    if now.weekday() >= 5: # Saturday/Sunday
        return False
        
    current_time = now.time()
    market_start = time(9, 15)
    market_end = time(15, 30)
    return market_start <= current_time <= market_end

from telegram_config import send_deduplicated_telegram_alert

def send_to_telegram(message, bot_token, chat_id):
    return send_deduplicated_telegram_alert(message, bot_token, chat_id)

def fetch_index_15m(ticker):
    """Fetches 15-minute intraday candle data for index symbols."""
    try:
        df = yf.download(ticker, period='5d', interval='15m', progress=False)
        if df is not None and not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna(subset=['Close'])
            df = ensure_ist_timezone(df)
            return df
    except Exception as e:
        print(f"[WARNING] Failed to fetch 15m data for {ticker}: {e}")
    return None

def fetch_nse_option_chain(symbol):
    """Fetches live Option Chain data from NSE API with session headers."""
    symbol = "NIFTY" if symbol.upper() == "NIFTY" else "BANKNIFTY"
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        session = requests.Session()
        # Initial request to grab NSE cookies
        session.get("https://www.nseindia.com", headers=headers, timeout=5)
        res = session.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"[WARNING] NSE Option Chain API fetch failed for {symbol}: {e}")
    return None

def process_option_chain_metrics(oc_data, spot_price):
    """Calculates Put-Call Ratio (PCR), Max Call OI (Resistance), and Max Put OI (Support)."""
    if not oc_data or "records" not in oc_data:
        # Fallback estimation if NSE API blocks
        return {
            "pcr": 1.0,
            "max_call_oi_strike": round(spot_price, -2) + 200,
            "max_put_oi_strike": round(spot_price, -2) - 200,
            "total_call_oi": 0,
            "total_put_oi": 0
        }
        
    records = oc_data.get("records", {})
    data = records.get("data", [])
    
    total_call_oi = 0
    total_put_oi = 0
    
    call_oi_map = {}
    put_oi_map = {}
    
    for item in data:
        strike = item.get("strikePrice")
        if not strike:
            continue
            
        CE = item.get("CE", {})
        PE = item.get("PE", {})
        
        c_oi = CE.get("openInterest", 0) or 0
        p_oi = PE.get("openInterest", 0) or 0
        
        total_call_oi += c_oi
        total_put_oi += p_oi
        
        if c_oi > 0:
            call_oi_map[strike] = c_oi
        if p_oi > 0:
            put_oi_map[strike] = p_oi
            
    pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else 1.0
    
    max_call_strike = max(call_oi_map, key=call_oi_map.get) if call_oi_map else round(spot_price, -2) + 200
    max_put_strike = max(put_oi_map, key=put_oi_map.get) if put_oi_map else round(spot_price, -2) - 200
    
    return {
        "pcr": float(pcr),
        "max_call_oi_strike": float(max_call_strike),
        "max_put_oi_strike": float(max_put_strike),
        "total_call_oi": int(total_call_oi),
        "total_put_oi": int(total_put_oi)
    }

def analyze_index_sentiment(df, oc_metrics):
    """Determines 15-minute Market Pulse sentiment for an index."""
    if df is None or df.empty or len(df) < 5:
        return "YELLOW (Neutral)", 0.0, 0.0
        
    latest_date = df.index[-1].date()
    today_data = df[df.index.date == latest_date]
    
    if len(today_data) == 0:
        return "YELLOW (Neutral)", 0.0, 0.0
        
    first_candle = today_data.iloc[0]
    last_candle = today_data.iloc[-1]
    
    spot_close = last_candle['Close']
    first_open = first_candle['Open']
    pct_change = ((spot_close - first_open) / first_open) * 100
    
    # Calculate VWAP
    typical_price_vol = ((today_data['High'] + today_data['Low'] + today_data['Close']) / 3) * today_data['Volume']
    total_vol = today_data['Volume'].sum()
    vwap = typical_price_vol.sum() / total_vol if total_vol > 0 else spot_close
    
    pcr = oc_metrics.get("pcr", 1.0)
    
    # Quantitative Sentiment Classification
    if spot_close > vwap and pct_change > 0.15 and pcr >= 0.95:
        sentiment = "🟢 BULLISH MOMENTUM"
    elif spot_close < vwap and pct_change < -0.15 and pcr <= 0.85:
        sentiment = "🔴 BEARISH PRESSURE"
    else:
        sentiment = "🟡 SIDEWAYS / RANGEBOUND"
        
    return sentiment, round(float(spot_close), 2), round(float(vwap), 2)

def generate_options_signal(index_name, spot_price, vwap, sentiment, oc_metrics, is_simulation=False):
    """Generates Call (CE) or Put (PE) buying options trade signals when conditions align."""
    pcr = oc_metrics.get("pcr", 1.0)
    
    # ATM Strike rounding (50 for Nifty, 100 for Bank Nifty)
    step = 50 if index_name == "NIFTY" else 100
    atm_strike = round(spot_price / step) * step
    
    if "BULLISH" in sentiment and pcr >= 1.0:
        # CE Buy Signal
        strike = int(atm_strike)
        option_symbol = f"{index_name} {strike} CE"
        entry_spot = spot_price
        sl_spot = min(entry_spot - (30 if index_name == "NIFTY" else 90), vwap)
        risk = entry_spot - sl_spot
        
        t1_spot = entry_spot + (1.2 * risk)
        t2_spot = entry_spot + (2.0 * risk)
        
        return {
            "type": "BUY CE (CALL)",
            "index": index_name,
            "option_symbol": option_symbol,
            "strike": strike,
            "spot_price": round(entry_spot, 2),
            "sl_spot": round(sl_spot, 2),
            "t1_spot": round(t1_spot, 2),
            "t2_spot": round(t2_spot, 2),
            "pcr": pcr,
            "rationale": f"{index_name} sustaining above VWAP (₹{vwap:.1f}) with strong Put writing support (PCR: {pcr})."
        }
        
    elif "BEARISH" in sentiment and pcr <= 0.80:
        # PE Buy Signal
        strike = int(atm_strike)
        option_symbol = f"{index_name} {strike} PE"
        entry_spot = spot_price
        sl_spot = max(entry_spot + (30 if index_name == "NIFTY" else 90), vwap)
        risk = sl_spot - entry_spot
        
        t1_spot = entry_spot - (1.2 * risk)
        t2_spot = entry_spot - (2.0 * risk)
        
        return {
            "type": "BUY PE (PUT)",
            "index": index_name,
            "option_symbol": option_symbol,
            "strike": strike,
            "spot_price": round(entry_spot, 2),
            "sl_spot": round(sl_spot, 2),
            "t1_spot": round(t1_spot, 2),
            "t2_spot": round(t2_spot, 2),
            "pcr": pcr,
            "rationale": f"{index_name} trading below VWAP (₹{vwap:.1f}) with aggressive Call writing pressure (PCR: {pcr})."
        }
        
    return None

def save_options_json(pulse_data):
    """Saves options metrics and market pulse to data/options.json for dashboard sync."""
    os.makedirs("data", exist_ok=True)
    json_path = os.path.join("data", "options.json")
    
    try:
        with open(json_path, "w") as f:
            json.dump(pulse_data, f, indent=2)
        print(f"[INFO] Saved options & market pulse to {json_path}")
    except Exception as e:
        print(f"[ERROR] Failed to save options.json: {e}")

def main():
    print("=========================================")
    print("  MARKETMENTOR OPTIONS & PULSE ENGINE    ")
    print("=========================================")
    
    from telegram_config import get_telegram_credentials
    tg_token, tg_chat_id = get_telegram_credentials()
            
    is_live = check_market_hours()
    is_github = os.environ.get("GITHUB_ACTIONS") == "true"
    
    if not is_live:
        if is_github:
            print("[INFO] Market is closed. Exiting immediately in GitHub Actions.")
            return
        print("[INFO] Market is closed. Running in SIMULATION MODE on last trading session.")
        is_simulation = True
    else:
        print("[INFO] Market is OPEN. Scanning Nifty, Bank Nifty & India VIX live feeds...")
        is_simulation = False

    # 1. Fetch 15m Index & VIX Data
    nifty_df = fetch_index_15m('^NSEI')
    banknifty_df = fetch_index_15m('^NSEBANK')
    vix_df = fetch_index_15m('^INDIAVIX')
    
    vix_val = 14.5
    if vix_df is not None and not vix_df.empty:
        vix_val = round(float(vix_df['Close'].iloc[-1]), 2)
        
    # VIX Volatility status
    if vix_val < 13.0:
        vix_status = "🟢 Low Volatility (Ideal for Option Buying Momentum)"
    elif vix_val <= 18.0:
        vix_status = "🟡 Moderate Volatility (Favorable Option Trading Range)"
    else:
        vix_status = "🔴 High Volatility (High Premium Decay Risk)"

    # 2. Fetch Option Chains
    nifty_spot = float(nifty_df['Close'].iloc[-1]) if nifty_df is not None and not nifty_df.empty else 24700.0
    banknifty_spot = float(banknifty_df['Close'].iloc[-1]) if banknifty_df is not None and not banknifty_df.empty else 51500.0
    
    nifty_oc_raw = fetch_nse_option_chain('NIFTY')
    banknifty_oc_raw = fetch_nse_option_chain('BANKNIFTY')
    
    nifty_oc = process_option_chain_metrics(nifty_oc_raw, nifty_spot)
    banknifty_oc = process_option_chain_metrics(banknifty_oc_raw, banknifty_spot)
    
    # 3. Analyze Market Sentiments
    nifty_sentiment, nifty_close, nifty_vwap = analyze_index_sentiment(nifty_df, nifty_oc)
    banknifty_sentiment, banknifty_close, banknifty_vwap = analyze_index_sentiment(banknifty_df, banknifty_oc)
    
    # 4. Generate Options Signals
    nifty_signal = generate_options_signal("NIFTY", nifty_close, nifty_vwap, nifty_sentiment, nifty_oc, is_simulation=is_simulation)
    banknifty_signal = generate_options_signal("BANKNIFTY", banknifty_close, banknifty_vwap, banknifty_sentiment, banknifty_oc, is_simulation=is_simulation)
    
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    now_str = datetime.now(ist_tz).strftime("%d-%b-%Y %I:%M %p")
    
    # Compile JSON Output payload
    pulse_payload = {
        "timestamp": now_str,
        "vix": {
            "value": vix_val,
            "status": vix_status
        },
        "indices": {
            "NIFTY": {
                "spot": nifty_close,
                "vwap": nifty_vwap,
                "sentiment": nifty_sentiment,
                "pcr": nifty_oc["pcr"],
                "max_call_oi": nifty_oc["max_call_oi_strike"],
                "max_put_oi": nifty_oc["max_put_oi_strike"]
            },
            "BANKNIFTY": {
                "spot": banknifty_close,
                "vwap": banknifty_vwap,
                "sentiment": banknifty_sentiment,
                "pcr": banknifty_oc["pcr"],
                "max_call_oi": banknifty_oc["max_call_oi_strike"],
                "max_put_oi": banknifty_oc["max_put_oi_strike"]
            }
        },
        "options_signals": [s for s in [nifty_signal, banknifty_signal] if s is not None]
    }
    
    # Save to data/options.json
    save_options_json(pulse_payload)
    
    # 5. Telegram Broadcast (15-Min Market Pulse & Options Signals)
    pulse_msg = (
        f"⚡ **15-MIN MARKET PULSE & OPTIONS UPDATE** ⚡\n"
        f"🕒 **Time**: {now_str} (IST)\n\n"
        f"📊 **Index Sentiments & PCR**:\n"
        f"• **Nifty 50**: `{nifty_sentiment}`\n"
        f"  - Spot: `₹{nifty_close}` | VWAP: `₹{nifty_vwap}` | PCR: `{nifty_oc['pcr']}`\n"
        f"  - Major OI Support: `₹{nifty_oc['max_put_oi_strike']:.0f}` | Resistance: `₹{nifty_oc['max_call_oi_strike']:.0f}`\n\n"
        f"• **Bank Nifty**: `{banknifty_sentiment}`\n"
        f"  - Spot: `₹{banknifty_close}` | VWAP: `₹{banknifty_vwap}` | PCR: `{banknifty_oc['pcr']}`\n"
        f"  - Major OI Support: `₹{banknifty_oc['max_put_oi_strike']:.0f}` | Resistance: `₹{banknifty_oc['max_call_oi_strike']:.0f}`\n\n"
        f"📈 **India VIX**: `{vix_val}` ({vix_status})\n"
    )
    
    if nifty_signal or banknifty_signal:
        pulse_msg += "\n" + "="*35 + "\n"
        pulse_msg += "🎯 **HIGH-PROBABILITY INDEX OPTIONS SIGNALS**:\n\n"
        for sig in [nifty_signal, banknifty_signal]:
            if sig:
                pulse_msg += (
                    f"🚨 **{sig['option_symbol']}** ({sig['type']})\n"
                    f"📥 **Spot Entry**: `₹{sig['spot_price']}`\n"
                    f"🛡️ **Spot SL**: `₹{sig['sl_spot']}`\n"
                    f"🎯 **Target 1**: `₹{sig['t1_spot']}` | **Target 2**: `₹{sig['t2_spot']}`\n"
                    f"💡 *Rationale*: {sig['rationale']}\n\n"
                )
                
    if tg_token and tg_chat_id:
        print("[BROADCAST] Sending Market Pulse to Telegram...")
        send_to_telegram(pulse_msg, tg_token, tg_chat_id)

if __name__ == '__main__':
    main()
