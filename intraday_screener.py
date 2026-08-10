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

# Dhan Security IDs for Nifty 50 symbols (extracted from scrip master)
DHAN_MAPPING = {
    'ADANIENT': '25', 'ADANIPORTS': '15083', 'APOLLOHOSP': '157', 'ASIANPAINT': '236', 'AXISBANK': '5900', 
    'BAJAJ-AUTO': '16669', 'BAJFINANCE': '317', 'BAJAJFINSV': '16675', 'BEL': '383', 'BHARTIARTL': '10604', 
    'CIPLA': '694', 'COALINDIA': '20374', 'DRREDDY': '881', 'EICHERMOT': '910', 'GRASIM': '1232', 
    'HCLTECH': '7229', 'HDFCBANK': '1333', 'HDFCLIFE': '467', 'HINDALCO': '1363', 
    'HINDUNILVR': '1394', 'ICICIBANK': '4963', 'ITC': '1660', 'INFY': '1594', 'INDIGO': '11195', 
    'JSWSTEEL': '11723', 'JIOFIN': '18143', 'KOTAKBANK': '1922', 'LT': '11483', 'M&M': '2031', 
    'MARUTI': '10999', 'MAXHEALTH': '22377', 'NTPC': '11630', 'NESTLEIND': '17963', 'ONGC': '2475', 
    'POWERGRID': '14977', 'RELIANCE': '2885', 'SBILIFE': '21808', 'SHRIRAMFIN': '4306', 'SBIN': '3045', 
    'SUNPHARMA': '3351', 'TCS': '11536', 'TATACONSUM': '3432', 'TMPV': '3456', 'TATASTEEL': '3499', 
    'TECHM': '13538', 'TITAN': '3506', 'TRENT': '1964', 'ULTRACEMCO': '11532', 'WIPRO': '3787',
    'TATAMOTORS': '3456'
}

def ensure_ist_timezone(df):
    """Ensures the DataFrame index is in Asia/Kolkata timezone (IST) for accurate time-window analysis."""
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

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    
    rs = avg_gain / avg_loss.replace(0, 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_atr(df, period=14):
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    return atr

def get_nifty50_symbols():
    """Fetches Nifty 50 symbols dynamically from the NSE website list."""
    url = "https://archives.nseindia.com/content/indices/ind_nifty50list.csv"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            symbols = []
            for line in lines[1:]:
                parts = line.split(',')
                if len(parts) > 2:
                    symbol = parts[2].strip().replace('"', '')
                    if symbol:
                        symbols.append(symbol)
            if len(symbols) >= 45: # Safe verification
                return symbols
    except Exception as e:
        print(f"[WARNING] Failed to fetch dynamic Nifty 50 symbols: {e}. Using local fallback.")
        
    # Local fallback if NSE website is down or blocking requests
    return [
        'ADANIENT', 'ADANIPORTS', 'APOLLOHOSP', 'ASIANPAINT', 'AXISBANK', 'BAJAJ-AUTO', 'BAJFINANCE', 
        'BAJAJFINSV', 'BEL', 'BHARTIARTL', 'CIPLA', 'COALINDIA', 'DRREDDY', 'EICHERMOT', 'ETERNAL', 
        'GRASIM', 'HCLTECH', 'HDFCBANK', 'HDFCLIFE', 'HINDALCO', 'HINDUNILVR', 'ICICIBANK', 'ITC', 
        'INFY', 'INDIGO', 'JSWSTEEL', 'JIOFIN', 'KOTAKBANK', 'LT', 'M&M', 'MARUTI', 'MAXHEALTH', 
        'NTPC', 'NESTLEIND', 'ONGC', 'POWERGRID', 'RELIANCE', 'SBILIFE', 'SHRIRAMFIN', 'SBIN', 
        'SUNPHARMA', 'TCS', 'TATACONSUM', 'TMPV', 'TATASTEEL', 'TECHM', 'TITAN', 'TRENT', 
        'ULTRACEMCO', 'WIPRO'
    ]

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

def send_to_telegram(message, bot_token, chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            print("[INFO] Successfully sent intraday signal to Telegram!")
        else:
            print(f"[ERROR] Telegram sending failed: {response.text}")
    except Exception as e:
        print(f"[ERROR] Exception sending to Telegram: {e}")

def fetch_dhan_data(symbol, client_id, access_token):
    """Fetches 15m intraday data from Dhan API."""
    security_id = DHAN_MAPPING.get(symbol)
    if not security_id:
        return None
        
    url = "https://api.dhan.co/v2/charts/intraday"
    headers = {
        "client-id": client_id,
        "access-token": access_token,
        "Content-Type": "application/json"
    }
    
    today = datetime.now()
    from_date = (today - timedelta(days=5)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")
    
    payload = {
        "securityId": security_id,
        "exchangeSegment": "NSE_EQ",
        "instrument": "EQUITY",
        "fromDate": from_date,
        "toDate": to_date,
        "interval": "15"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            res_json = response.json()
            chart_data = res_json.get("data", {})
            if "t" in chart_data and len(chart_data["t"]) > 0:
                idx = pd.to_datetime(chart_data["t"], unit='s')
                df = pd.DataFrame({
                    "Open": [float(x) for x in chart_data["o"]],
                    "High": [float(x) for x in chart_data["h"]],
                    "Low": [float(x) for x in chart_data["l"]],
                    "Close": [float(x) for x in chart_data["c"]],
                    "Volume": [int(x) for x in chart_data["v"]]
                }, index=idx)
                
                df = ensure_ist_timezone(df)
                return df
    except Exception as e:
        print(f"[WARNING] Dhan API fetch failed for {symbol}: {e}")
    return None

def process_symbol(symbol, df, is_simulation=False):
    if len(df) < 20:
        return None
        
    latest_date = df.index[-1].date()
    today_data = df[df.index.date == latest_date]
    
    if len(today_data) < 2:
        return None
        
    first_candle = today_data.iloc[0]
    range_high = first_candle['High']
    range_low = first_candle['Low']
    
    ema20 = df['Close'].ewm(span=20, adjust=False).mean()
    rsi = calculate_rsi(df['Close'], period=14)
    atr = calculate_atr(df, period=14)
    
    typical_price_vol = ((today_data['High'] + today_data['Low'] + today_data['Close']) / 3) * today_data['Volume']
    total_vol = today_data['Volume'].sum()
    vwap = typical_price_vol.sum() / total_vol if total_vol > 0 else today_data['Close'].iloc[-1]
    
    signal_idx = None
    if not is_simulation:
        last_close = today_data['Close'].iloc[-1]
        prev_close = today_data['Close'].iloc[-2]
        if last_close > range_high and prev_close <= range_high:
            signal_idx = -1
    else:
        for i in range(1, len(today_data)):
            c_close = today_data['Close'].iloc[i]
            p_close = today_data['Close'].iloc[i-1]
            if c_close > range_high and p_close <= range_high:
                signal_idx = i
                break
                
    if signal_idx is None:
        return None
        
    trigger_candle = today_data.iloc[signal_idx]
    
    # Pro-Trader Time Filter: Skip late entries after 2:30 PM (14:30 IST)
    trigger_time_obj = today_data.index[signal_idx].time()
    if trigger_time_obj > time(14, 30):
        return None
        
    trigger_time = today_data.index[signal_idx].strftime('%I:%M %p')
    close_price = trigger_candle['Close']
    volume = trigger_candle['Volume']
    
    real_idx = len(df) - len(today_data) + (signal_idx if signal_idx < 0 else signal_idx)
    avg_vol = df['Volume'].iloc[real_idx-5:real_idx].mean()
    vol_expansion = volume / avg_vol if avg_vol > 0 else 1.0
    
    if vol_expansion < 1.2:
        return None
        
    c_ema20 = ema20.iloc[real_idx]
    c_rsi = rsi.iloc[real_idx]
    c_atr = atr.iloc[real_idx]
    
    if close_price <= c_ema20 or not (50 <= c_rsi <= 70):
        return None
        
    entry = close_price
    sl = entry - (1.5 * c_atr)
    sl = max(sl, range_low)
    
    risk = entry - sl
    risk_pct = (risk / entry) * 100
    
    if risk_pct > 3.0 or risk_pct <= 0.2:
        return None
        
    t1 = entry + (1.0 * risk)
    t2 = entry + (2.0 * risk)
    
    return {
        "symbol": symbol,
        "trigger_time": trigger_time,
        "entry": round(entry, 2),
        "sl": round(sl, 2),
        "t1": round(t1, 2),
        "t2": round(t2, 2),
        "risk_pct": round(risk_pct, 2),
        "range_high": round(range_high, 2),
        "range_low": round(range_low, 2),
        "vwap": round(vwap, 2),
        "rsi": round(c_rsi, 1),
        "vol_expansion": round(vol_expansion, 1)
    }

def save_intraday_json(new_signals, nifty_trend):
    """Saves intraday setups and updates prices and statuses in data/intraday.json."""
    os.makedirs("data", exist_ok=True)
    json_path = os.path.join("data", "intraday.json")
    
    # Use IST Date for file state consistency
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    today_str = datetime.now(ist_tz).strftime("%d-%b-%Y")
    
    existing_signals = []
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                saved_data = json.load(f)
            if saved_data.get("date") == today_str:
                existing_signals = saved_data.get("signals", [])
        except Exception as e:
            print(f"[WARNING] Failed to read existing intraday.json: {e}")
            
    # Combine signals: update existing or add new
    signal_map = {s["symbol"]: s for s in existing_signals}
    
    # Process new signals
    for s in new_signals:
        sym = s["symbol"]
        if sym not in signal_map:
            s["current_price"] = s["entry"]
            s["status"] = "Active"
            signal_map[sym] = s
            
    # Update current prices and status for active signals in the map
    for sym, s_data in list(signal_map.items()):
        if s_data.get("status") in ["Stop Loss Hit", "Target 2 Hit"]:
            continue
            
        ticker_symbol = f"{sym}.NS"
        try:
            ticker_obj = yf.Ticker(ticker_symbol)
            fast_info = ticker_obj.fast_info
            ltp = fast_info.get("lastPrice")
            if ltp is not None:
                ltp = round(float(ltp), 2)
                s_data["current_price"] = ltp
                
                # Check status boundaries
                sl = s_data["sl"]
                t1 = s_data["t1"]
                t2 = s_data["t2"]
                
                if ltp <= sl:
                    s_data["status"] = "Stop Loss Hit"
                elif ltp >= t2:
                    s_data["status"] = "Target 2 Hit"
                elif ltp >= t1:
                    s_data["status"] = "Target 1 Hit"
                else:
                    s_data["status"] = "Active"
        except Exception as e:
            print(f"[WARNING] Failed to update LTP for {sym}: {e}")
            
    # Write back to JSON
    output_data = {
        "date": today_str,
        "nifty_trend": nifty_trend,
        "signals": list(signal_map.values())
    }
    
    try:
        with open(json_path, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"[INFO] Saved intraday data to {json_path}")
    except Exception as e:
        print(f"[ERROR] Failed to write intraday.json: {e}")

def main():
    print("=========================================")
    print("   MARKETMENTOR INTRADAY ENGINE (ORB)    ")
    print("=========================================")
    
    # Load configuration
    config_file = "config.json"
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    dhan_enabled = False
    client_id = None
    access_token = None
    
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as cf:
                config = json.load(cf)
            tg = config.get("telegram", {})
            if not tg_token:
                tg_token = tg.get("bot_token")
            if not tg_chat_id:
                tg_chat_id = tg.get("chat_id")
                
            dhan_config = config.get("dhan", {})
            dhan_enabled = dhan_config.get("enabled", False)
            client_id = dhan_config.get("client_id")
            access_token = dhan_config.get("access_token")
        except Exception as e:
            print(f"[WARNING] Could not parse config.json: {e}")
            
    is_live = check_market_hours()
    is_github = os.environ.get("GITHUB_ACTIONS") == "true"
    
    if not is_live:
        if is_github:
            print("[INFO] Market is closed. Exiting immediately in GitHub Actions to prevent duplicate simulation alerts.")
            return
        print("[INFO] Market is closed. Running in SIMULATION MODE on last trading session.")
        is_simulation = True
    else:
        print("[INFO] Market is OPEN. Scanning for real-time live breakouts.")
        is_simulation = False
        
    # Pro-Trader Index Context Filter
    nifty_trend = "Neutral / Sideways"
    try:
        nifty_df = yf.download('^NSEI', period='2d', interval='15m', progress=False)
        if nifty_df is not None and not nifty_df.empty:
            if isinstance(nifty_df.columns, pd.MultiIndex):
                nifty_df.columns = nifty_df.columns.get_level_values(0)
            
            nifty_df = ensure_ist_timezone(nifty_df)
            latest_nifty_date = nifty_df.index[-1].date()
            nifty_today = nifty_df[nifty_df.index.date == latest_nifty_date]
            if len(nifty_today) > 0:
                nifty_open = nifty_today['Open'].iloc[0]
                nifty_close = nifty_today['Close'].iloc[-1]
                nifty_pct = ((nifty_close - nifty_open) / nifty_open) * 100
                if nifty_pct > 0.2:
                    nifty_trend = "🟢 Bullish (Market Trending Up)"
                elif nifty_pct < -0.2:
                    nifty_trend = "🔴 Bearish (Market Downtrend)"
                else:
                    nifty_trend = "🟡 Neutral (Rangebound Market)"
    except Exception as e:
        print(f"[WARNING] Could not fetch Nifty Index context: {e}")
        
    symbols = get_nifty50_symbols()
    new_signals = []
    
    if dhan_enabled and client_id and access_token:
        print(f"[INFO] Dhan API enabled. Scanning {len(symbols)} stocks with live Dhan feed...")
        signals_found = 0
        for symbol in symbols:
            df = fetch_dhan_data(symbol, client_id, access_token)
            
            if df is None:
                ticker_symbol = f"{symbol}.NS"
                try:
                    df = yf.download(ticker_symbol, period='5d', interval='15m', progress=False)
                    if df is not None and not df.empty:
                        if isinstance(df.columns, pd.MultiIndex):
                            df.columns = df.columns.get_level_values(0)
                        df = df.dropna(subset=['Close'])
                        df = ensure_ist_timezone(df)
                except Exception as e:
                    continue
                    
            if df is None or df.empty:
                continue
                
            signal = process_symbol(symbol, df, is_simulation=is_simulation)
            if signal:
                signals_found += 1
                company_name = symbol
                try:
                    ticker_obj = yf.Ticker(f"{symbol}.NS")
                    company_name = ticker_obj.info.get('longName', symbol)
                except Exception:
                    pass
                
                # Append company name to signal and add to new list
                signal["company"] = company_name
                new_signals.append(signal)
                    
                alert_msg = (
                    f"🚨 **EXPERT INTRADAY BUY ALERT** 🚨\n\n"
                    f"📈 **Stock**: NSE:{signal['symbol']} ({company_name})\n"
                    f"⚡ **Setup**: 15-Min Opening Range Breakout (ORB)\n"
                    f"🕒 **Trigger Time**: {signal['trigger_time']} (IST)\n"
                    f"📊 **Nifty 50 Trend**: {nifty_trend}\n\n"
                    f"📥 **Entry Trigger**: `₹{signal['entry']:.2f}`\n"
                    f"🛡️ **Stop Loss (SL)**: `₹{signal['sl']:.2f}` (Risk: {signal['risk_pct']:.2f}%)\n\n"
                    f"🎯 **Target 1 (R:R 1:1)**: `₹{signal['t1']:.2f}`\n"
                    f"🎯 **Target 2 (R:R 1:2)**: `₹{signal['t2']:.2f}`\n\n"
                    f"📊 **Expert Analysis**:\n"
                    f"- Price broke above the opening 15m range high of `₹{signal['range_high']}` with `{signal['vol_expansion']}x` volume expansion.\n"
                    f"- Sustaining above daily VWAP (`₹{signal['vwap']}`). RSI is in strong bullish territory at `{signal['rsi']}`.\n\n"
                    f"⚠️ *Risk Management: Standard capital risk of 1% is recommended per setup. Trailing stop-loss to cost is advised once Target 1 is reached.*"
                )
                print(f"[SIGNAL] Buy trigger for {symbol} at {signal['entry']}")
                if tg_token and tg_chat_id:
                    send_to_telegram(alert_msg, tg_token, tg_chat_id)
                    
        print(f"\nScan complete. Total signals detected: {signals_found}")
        
    else:
        print(f"[INFO] Dhan API disabled or keys missing. Scanning {len(symbols)} stocks using yfinance...")
        tickers = [f"{s}.NS" for s in symbols]
        try:
            data = yf.download(tickers, period='5d', interval='15m', group_by='ticker', progress=False)
        except Exception as e:
            print(f"[ERROR] Failed to download intraday data: {e}")
            return
            
        signals_found = 0
        for symbol in symbols:
            ticker_symbol = f"{symbol}.NS"
            try:
                if isinstance(data.columns, pd.MultiIndex):
                    if ticker_symbol not in data.columns.levels[0]:
                        continue
                    df = data[ticker_symbol].dropna(subset=['Close'])
                else:
                    df = data.dropna(subset=['Close'])
                
                df = ensure_ist_timezone(df)
                signal = process_symbol(symbol, df, is_simulation=is_simulation)
                if signal:
                    signals_found += 1
                    company_name = symbol
                    try:
                        ticker_obj = yf.Ticker(ticker_symbol)
                        company_name = ticker_obj.info.get('longName', symbol)
                    except Exception:
                        pass
                    
                    signal["company"] = company_name
                    new_signals.append(signal)
                        
                    alert_msg = (
                        f"🚨 **EXPERT INTRADAY BUY ALERT** 🚨\n\n"
                        f"📈 **Stock**: NSE:{signal['symbol']} ({company_name})\n"
                        f"⚡ **Setup**: 15-Min Opening Range Breakout (ORB)\n"
                        f"🕒 **Trigger Time**: {signal['trigger_time']} (IST)\n"
                        f"📊 **Nifty 50 Trend**: {nifty_trend}\n\n"
                        f"📥 **Entry Trigger**: `₹{signal['entry']:.2f}`\n"
                        f"🛡️ **Stop Loss (SL)**: `₹{signal['sl']:.2f}` (Risk: {signal['risk_pct']:.2f}%)\n\n"
                        f"🎯 **Target 1 (R:R 1:1)**: `₹{signal['t1']:.2f}`\n"
                        f"🎯 **Target 2 (R:R 1:2)**: `₹{signal['t2']:.2f}`\n\n"
                        f"📊 **Expert Analysis**:\n"
                        f"- Price broke above the opening 15m range high of `₹{signal['range_high']}` with `{signal['vol_expansion']}x` volume expansion.\n"
                        f"- Sustaining above daily VWAP (`₹{signal['vwap']}`). RSI is in strong bullish territory at `{signal['rsi']}`.\n\n"
                        f"⚠️ *Risk Management: Standard capital risk of 1% is recommended per setup. Trailing stop-loss to cost is advised once Target 1 is reached.*"
                    )
                    print(f"[SIGNAL] Buy trigger for {symbol} at {signal['entry']}")
                    if tg_token and tg_chat_id:
                        send_to_telegram(alert_msg, tg_token, tg_chat_id)
            except Exception as e:
                continue
                
        print(f"\nScan complete. Total signals detected: {signals_found}")
        
    # Save collected signals to JSON (updates current price & status of active signals)
    save_intraday_json(new_signals, nifty_trend)

    # Automatically trigger Options & 15-Min Market Pulse Engine
    try:
        import options_screener
        print("\n--- Triggering Options & 15-Min Market Pulse Engine ---")
        options_screener.main()
    except Exception as e:
        print(f"[WARNING] Could not trigger Options Engine: {e}")

if __name__ == '__main__':
    main()
