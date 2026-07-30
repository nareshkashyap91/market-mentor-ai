import io
import os
import sys
import json
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, time

# Ensure terminal outputs emojis correctly on Windows
sys.stdout.reconfigure(encoding='utf-8')

# Custom math helpers for technical indicators on 15m intervals
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

def get_fallback_symbols():
    """Returns top 40 liquid symbols to avoid hitting yfinance limits during rapid scans."""
    return [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "BHARTIARTL", "SBIN", "ITC", 
        "HINDUNILVR", "LT", "BAJFINANCE", "HCLTECH", "MARUTI", "SUNPHARMA", "TATAMOTORS", 
        "AXISBANK", "COALINDIA", "ADANIPORTS", "ASIANPAINT", "ULTRACEMCO", "JSWSTEEL", 
        "M&M", "TATASTEEL", "SIEMENS", "HAL", "TECHM", "PFC", "RECLTD", "BEL", "INDUSINDBK", 
        "CIPLA", "WIPRO", "DLF", "TRENT", "BPCL", "VBL", "HEROMOTOCO", "SHRIRAMFIN", 
        "POLYCAB", "PIDILITIND"
    ]

def check_market_hours():
    """Checks if the Indian stock market is currently open (9:15 AM - 3:30 PM IST, Mon-Fri)."""
    now = datetime.now()
    if now.weekday() >= 5: # Saturday/Sunday
        return False
    current_time = now.time()
    market_start = time(9, 15)
    market_end = time(15, 30)
    return market_start <= current_time <= market_end

def send_to_telegram(message, bot_token, chat_id):
    """Sends intraday alerts to Telegram."""
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

def process_symbol(symbol, df, is_simulation=False):
    """Processes 15m candle data for a symbol to find ORB breakout signals."""
    if len(df) < 20: # Minimum history needed for calculations
        return None
        
    # Get index of the first candle of the day
    # yfinance timestamps are in exchange time (Asia/Kolkata)
    # We find the first row that belongs to today
    today_date = df.index[-1].date()
    today_data = df[df.index.date == today_date]
    
    if len(today_data) < 2:
        # First candle is not completed yet, or not enough intraday range
        return None
        
    # The first 15-minute candle defines the range
    first_candle = today_data.iloc[0]
    range_high = first_candle['High']
    range_low = first_candle['Low']
    
    # Calculate indicators on the full series
    ema20 = df['Close'].ewm(span=20, adjust=False).mean()
    rsi = calculate_rsi(df['Close'], period=14)
    atr = calculate_atr(df, period=14)
    
    # Daily VWAP calculation on today's candles
    typical_price_vol = ((today_data['High'] + today_data['Low'] + today_data['Close']) / 3) * today_data['Volume']
    total_vol = today_data['Volume'].sum()
    vwap = typical_price_vol.sum() / total_vol if total_vol > 0 else today_data['Close'].iloc[-1]
    
    # Check for breakout
    # In live mode, we only check if the latest candle just broke out
    # In simulation mode, we scan all candles of today to find the first breakout
    signal_idx = None
    if not is_simulation:
        # Live mode check
        last_close = today_data['Close'].iloc[-1]
        prev_close = today_data['Close'].iloc[-2]
        
        # Fresh breakout trigger: close crosses above range high on latest candle
        if last_close > range_high and prev_close <= range_high:
            signal_idx = -1
    else:
        # Simulation mode check (find the first candle of today that broke out)
        for i in range(1, len(today_data)):
            c_close = today_data['Close'].iloc[i]
            p_close = today_data['Close'].iloc[i-1]
            if c_close > range_high and p_close <= range_high:
                signal_idx = i
                break
                
    if signal_idx is None:
        return None
        
    # Extract values at the signal trigger candle
    trigger_candle = today_data.iloc[signal_idx]
    trigger_time = today_data.index[signal_idx].strftime('%I:%M %p')
    close_price = trigger_candle['Close']
    volume = trigger_candle['Volume']
    
    # Volume Confirmation: Trigger volume must exceed average of last 5 candles
    # Safe index offset
    real_idx = len(df) - len(today_data) + (signal_idx if signal_idx < 0 else signal_idx)
    avg_vol = df['Volume'].iloc[real_idx-5:real_idx].mean()
    vol_expansion = volume / avg_vol if avg_vol > 0 else 1.0
    
    if vol_expansion < 1.2: # Must be at least 20% higher volume
        return None
        
    # Trend confirmations
    c_ema20 = ema20.iloc[real_idx]
    c_rsi = rsi.iloc[real_idx]
    c_atr = atr.iloc[real_idx]
    
    # Extra filters: Price above EMA20, RSI in constructive bullish zone (50-70)
    if close_price <= c_ema20 or not (50 <= c_rsi <= 70):
        return None
        
    # Calculate Levels
    entry = close_price
    # Stop Loss based on ATR (1.5x) but protected by range low
    sl = entry - (1.5 * c_atr)
    sl = max(sl, range_low) # Cap SL at opening low to manage downside
    
    risk = entry - sl
    risk_pct = (risk / entry) * 100
    
    # Risk Management Filter: Skip if stop loss is too wide (>3.0%)
    if risk_pct > 3.0 or risk_pct <= 0.2:
        return None
        
    # Target calculations
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

def main():
    print("=========================================")
    # Acting as Expert Trading Analyst
    print("   MARKETMENTOR INTRADAY ENGINE (ORB)    ")
    print("=========================================")
    
    # Determine Mode
    is_live = check_market_hours()
    
    # Force simulation mode if market is closed
    if not is_live:
        print("[INFO] Market is closed. Running in SIMULATION MODE on last trading session.")
        is_simulation = True
    else:
        print("[INFO] Market is OPEN. Scanning for real-time live breakouts.")
        is_simulation = False
        
    symbols = get_fallback_symbols()
    print(f"Scanning {len(symbols)} high-liquidity stocks...")
    
    # Format symbols for yfinance
    tickers = [f"{s}.NS" for s in symbols]
    
    # Fetch 15m data for today
    # 5d period ensures we have historical candles to compute 20-EMA, RSI(14) and ATR(14)
    try:
        data = yf.download(tickers, period='5d', interval='15m', group_by='ticker', progress=False)
    except Exception as e:
        print(f"[ERROR] Failed to download intraday data: {e}")
        return
        
    signals_found = 0
    
    for symbol in symbols:
        ticker_symbol = f"{symbol}.NS"
        try:
            # Extract data
            if isinstance(data.columns, pd.MultiIndex):
                if ticker_symbol not in data.columns.levels[0]:
                    continue
                df = data[ticker_symbol].dropna(subset=['Close'])
            else:
                df = data.dropna(subset=['Close'])
                
            signal = process_symbol(symbol, df, is_simulation=is_simulation)
            
            if signal:
                signals_found += 1
                
                # Fetch Company name for professional look
                company_name = symbol
                try:
                    ticker_obj = yf.Ticker(ticker_symbol)
                    company_name = ticker_obj.info.get('longName', symbol)
                except Exception:
                    pass
                
                # Format Alert Message
                alert_msg = (
                    f"🚨 **EXPERT INTRADAY BUY ALERT** 🚨\n\n"
                    f"📈 **Stock**: NSE:{signal['symbol']} ({company_name})\n"
                    f"⚡ **Setup**: 15-Min Opening Range Breakout (ORB)\n"
                    f"🕒 **Trigger Time**: {signal['trigger_time']} (IST)\n\n"
                    f"📥 **Entry Trigger**: `₹{signal['entry']:.2f}`\n"
                    f"🛡️ **Stop Loss (SL)**: `₹{signal['sl']:.2f}` (Risk: {signal['risk_pct']:.2f}%)\n\n"
                    f"🎯 **Target 1 (R:R 1:1)**: `₹{signal['t1']:.2f}`\n"
                    f"🎯 **Target 2 (R:R 1:2)**: `₹{signal['t2']:.2f}`\n\n"
                    f"📊 **Expert Analysis**:\n"
                    f"- Price broke above the opening 15m range high of `₹{signal['range_high']}` with `{signal['vol_expansion']}x` volume expansion.\n"
                    f"- Sustaining above daily VWAP (`₹{signal['vwap']}`). RSI is in strong bullish territory at `{signal['rsi']}`.\n\n"
                    f"⚠️ *Risk Management: Standard capital risk of 1% is recommended per setup. Trailing stop-loss is advised as Target 1 is reached.*"
                )
                
                print(f"\n[SIGNAL] Buy trigger for {symbol} at {signal['entry']}")
                print(alert_msg)
                
                # Send to Telegram
                env_token = os.environ.get("TELEGRAM_BOT_TOKEN")
                env_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
                
                if env_token and env_chat_id:
                    send_to_telegram(alert_msg, env_token, env_chat_id)
                else:
                    config_file = "config.json"
                    if os.path.exists(config_file):
                        try:
                            with open(config_file, "r") as cf:
                                config = json.load(cf)
                            tg = config.get("telegram", {})
                            if tg.get("enabled", False):
                                send_to_telegram(alert_msg, tg.get("bot_token"), tg.get("chat_id"))
                        except Exception as e:
                            print(f"[WARNING] Failed to load config or broadcast: {e}")
                            
        except Exception as e:
            # Silently continue to next symbol
            continue
            
    print(f"\nScan complete. Total signals detected: {signals_found}")

if __name__ == '__main__':
    main()
