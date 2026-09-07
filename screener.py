import io
import os
import sys
import json
import requests
import numpy as np
import pandas as pd
import yfinance as yf
from mftool import Mftool
from datetime import datetime, timedelta

# Ensure terminal outputs emojis correctly on Windows
sys.stdout.reconfigure(encoding='utf-8')

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        if isinstance(obj, (np.integer, int)):
            return int(obj)
        if isinstance(obj, (np.floating, float)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

def sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    elif hasattr(obj, "item"):
        return obj.item()
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.floating, float)):
        return float(obj)
    return obj

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

# Emojis for categories
EMOJIS = {
    "Large Cap": "🏆",
    "Mid Cap": "🚀",
    "Small Cap": "🌟",
    "Flexi Cap": "🛡️"
}

# Curated top performing Direct Growth Mutual Funds
MUTUAL_FUNDS = {
    "Large Cap": {
        "SBI Large Cap Fund - Direct Growth": "119598",
        "ICICI Prudential Large Cap Fund - Direct Growth": "120586",
        "Mirae Asset Large Cap Fund - Direct Growth": "118825"
    },
    "Mid Cap": {
        "HDFC Mid-Cap Opportunities Fund - Direct Growth": "118989",
        "Kotak Emerging Equity Fund - Direct Growth": "119775",
        "Motilal Oswal Midcap Fund - Direct Growth": "127042"
    },
    "Small Cap": {
        "Nippon India Small Cap Fund - Direct Growth": "118778",
        "Quant Small Cap Fund - Direct Growth": "120828",
        "SBI Small Cap Fund - Direct Growth": "119717"
    },
    "Flexi Cap": {
        "Parag Parikh Flexi Cap Fund - Direct Growth": "122639",
        "Quant Flexi Cap Fund - Direct Growth": "120843",
        "HDFC Flexi Cap Fund - Direct Growth": "118955"
    }
}

# Fallback stock list (top liquid Nifty stocks) in case NSE download fails
FALLBACK_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "BHARTIARTL", "SBIN", "LICI", 
    "ITC", "HINDUNILVR", "LT", "BAJFINANCE", "HCLTECH", "MARUTI", "SUNPHARMA", 
    "ADANIENT", "KOTAKBANK", "TITAN", "ONGC", "TATAMOTORS", "NTPC", "AXISBANK", 
    "COALINDIA", "ADANIPORTS", "ASIANPAINT", "ULTRACEMCO", "POWERGRID", "JSWSTEEL", 
    "ADANIPOWER", "BAJAJFINSV", "M&M", "TATASTEEL", "SIEMENS", "HAL", "SBILIFE", 
    "IOC", "IRFC", "GRASIM", "HINDALCO", "NESTLEIND", "TECHM", "PFC", "RECLTD", 
    "BEL", "DIVISLAB", "INDUSINDBK", "BRITANNIA", "CIPLA", "EICHERMOT", "WIPRO", 
    "DLF", "TRENT", "TATACONSUM", "DRREDDY", "ADANIGREEN", "BPCL", "GMRINFRA", 
    "JIOFIN", "VBL", "LTIM", "BAJAJ-AUTO", "CHOLAFIN", "HEROMOTOCO", "SHRIRAMFIN", 
    "JINDALSTEL", "TATAELXSI", "HDFCLIFE", "ICICIPRULI", "MUTHOOTFIN", "APOLLOHOSP", 
    "POLYCAB", "INDHOTEL", "COLPAL", "PIDILITIND", "MCDOWELL-N", "UPL", "GAIL", 
    "PETRONET", "MRF", "BALKRISIND", "ASHOKLEY", "AUROPHARMA", "CUMMINSIND", 
    "OBEROIRLTY", "TATACOMM", "MAXHEALTH", "TVSMOTOR", "BHARATFORG", "LUPIN", 
    "PIIND", "BOSCHLTD", "ESCORTS", "PERSISTENT", "JSWENERGY"
]

def fetch_nifty500_symbols():
    """Downloads the Nifty 500 stock list from NSE/NiftyIndices. Fallbacks to static list on failure."""
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    
    print("Fetching Nifty 500 stock universe from niftyindices.com...")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            symbols = df['Symbol'].dropna().unique().tolist()
            # Clean symbols (some might have spaces)
            symbols = [s.strip() for s in symbols if s.strip()]
            print(f"Successfully loaded {len(symbols)} symbols from Nifty 500 list.")
            return symbols
        else:
            print(f"Failed to fetch. Status code: {response.status_code}. Using fallback list.")
    except Exception as e:
        print(f"Error fetching Nifty 500: {e}. Using fallback list.")
    
    print(f"Using fallback list of {len(FALLBACK_STOCKS)} liquid stocks.")
    return FALLBACK_STOCKS

def calculate_cagr(df, years):
    """Calculates CAGR return for a given number of years based on historical NAV data."""
    if len(df) < 2:
        return None
    
    latest_row = df.iloc[-1]
    latest_date = latest_row['date']
    latest_nav = latest_row['nav']
    
    target_date = latest_date - timedelta(days=int(years * 365.25))
    
    if target_date < df.iloc[0]['date']:
        return None  # Fund does not have enough history
        
    # Find closest date in DataFrame
    closest_idx = (df['date'] - target_date).abs().idxmin()
    past_row = df.iloc[closest_idx]
    past_date = past_row['date']
    past_nav = past_row['nav']
    
    # If the gap between target date and actual matched date is too large, skip
    if abs((past_date - target_date).days) > 30:
        return None
        
    cagr = ((latest_nav / past_nav) ** (1.0 / years) - 1.0) * 100.0
    return round(cagr, 2)

def analyze_mutual_funds():
    """Fetches Mutual Fund NAV data and calculates CAGR rankings."""
    print("\n--- Processing Mutual Fund CAGR Rankings ---")
    mf = Mftool()
    results = {}
    
    for category, funds in MUTUAL_FUNDS.items():
        print(f"Analyzing {category} Mutual Funds...")
        category_data = []
        for name, code in funds.items():
            try:
                raw_data = mf.get_scheme_historical_nav(code)
                if not raw_data or 'data' not in raw_data:
                    print(f"  Failed to fetch NAV history for {name} ({code})")
                    continue
                
                df = pd.DataFrame(raw_data['data'])
                df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
                df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
                df = df.dropna().sort_values('date').reset_index(drop=True)
                
                cagr_1y = calculate_cagr(df, 1)
                cagr_3y = calculate_cagr(df, 3)
                cagr_5y = calculate_cagr(df, 5)
                cagr_10y = calculate_cagr(df, 10)
                
                category_data.append({
                    "name": name,
                    "cagr_1y": cagr_1y,
                    "cagr_3y": cagr_3y,
                    "cagr_5y": cagr_5y,
                    "cagr_10y": cagr_10y,
                    "latest_nav": df.iloc[-1]['nav'],
                    "latest_date": df.iloc[-1]['date'].strftime('%d-%b-%Y')
                })
            except Exception as e:
                print(f"  Error processing {name}: {e}")
                
        # Rank by 3-Year CAGR (Standard time horizon for rankings, fallback to 1-Year if 3-Year is missing)
        category_data = sorted(
            category_data,
            key=lambda x: (x['cagr_3y'] if x['cagr_3y'] is not None else -999, 
                           x['cagr_5y'] if x['cagr_5y'] is not None else -999),
            reverse=True
        )
        results[category] = category_data
        
    return results

def screen_stocks(symbols):
    """Screens stocks based on liquidity, quality, EMA crossovers, volume expansion, and VWAP position."""
    print("\n--- Processing Stock Momentum Screener ---")
    
    # Download Nifty 50 for Relative Strength calculation
    nifty_close = None
    try:
        print("Downloading Nifty 50 benchmark data for Relative Strength calculation...")
        nifty_df = yf.download("^NSEI", period='18mo', interval='1d', progress=False)
        if not nifty_df.empty:
            if isinstance(nifty_df.columns, pd.MultiIndex):
                nifty_close = nifty_df['Close']['^NSEI'].dropna()
            else:
                nifty_close = nifty_df['Close'].dropna()
    except Exception as e:
        print(f"Warning: Could not download Nifty 50 data: {e}")
        
    # Format symbols for Yahoo Finance
    tickers = [f"{s}.NS" for s in symbols]
    
    # Step 1: Bulk download daily EOD data (18 months) to calculate DMA & Volume averages
    print(f"Downloading historical daily data for {len(tickers)} stocks...")
    try:
        # Download in one large batch
        hist_data = yf.download(tickers, period='18mo', interval='1d', group_by='ticker', progress=False)
    except Exception as e:
        print(f"Error downloading bulk EOD data: {e}")
        return []

    passed_stocks = []
    
    # Process each ticker
    for symbol in tickers:
        try:
            # Extract ticker data
            if isinstance(hist_data.columns, pd.MultiIndex):
                if symbol not in hist_data.columns.levels[0]:
                    continue
                df = hist_data[symbol].dropna(subset=['Close'])
            else:
                # Single ticker fallback
                df = hist_data.dropna(subset=['Close'])
            if len(df) < 200: # Minimum history for 200-DMA Simple Moving Average
                continue
            
            # Latest day values
            close_price = df['Close'].iloc[-1]
            volume = df['Volume'].iloc[-1]
            turnover = close_price * volume
            
            # 1. Daily Turnover Filter: > ₹10 Crores (100,000,000 INR)
            if turnover < 100000000:
                continue
                
            # Calculate technical parameters
            # EMAs
            ema9 = df['Close'].ewm(span=9, adjust=False).mean()
            ema20 = df['Close'].ewm(span=20, adjust=False).mean()
            ema21 = df['Close'].ewm(span=21, adjust=False).mean()
            ema50 = df['Close'].ewm(span=50, adjust=False).mean()
            
            # DMAs (Simple Moving Averages)
            dma20_series = df['Close'].rolling(window=20).mean()
            dma50_series = df['Close'].rolling(window=50).mean()
            dma100_series = df['Close'].rolling(window=100).mean()
            dma200_series = df['Close'].rolling(window=200).mean()
            
            dma20_val = float(dma20_series.iloc[-1])
            dma50_val = float(dma50_series.iloc[-1])
            dma100_val = float(dma100_series.iloc[-1])
            dma200_val = float(dma200_series.iloc[-1])
            
            dma_aligned = bool(dma20_val > dma50_val > dma100_val > dma200_val)
            
            # 1-Year CAR (Compound Annualized Return)
            if len(df) >= 252:
                price_1y_ago = df['Close'].iloc[-252]
            else:
                price_1y_ago = df['Close'].iloc[0]
            car_1y = float(((close_price - price_1y_ago) / price_1y_ago) * 100.0)
            
            # RSI (14)
            rsi = calculate_rsi(df['Close'], period=14)
            rsi_val = rsi.iloc[-1]
            
            # ATR (14)
            atr = calculate_atr(df, period=14)
            atr_val = atr.iloc[-1]
            
            # Relative Strength vs Nifty 50
            rs_outperforming = True
            if nifty_close is not None:
                aligned_nifty = nifty_close.reindex(df.index, method='ffill')
                rs_ratio = df['Close'] / aligned_nifty
                rs_sma20 = rs_ratio.rolling(20).mean()
                rs_sma5 = rs_ratio.rolling(5).mean()
                
                # Check if RS is above its 20-day SMA, and 5-day SMA is rising compared to 2 sessions ago
                if rs_ratio.iloc[-1] <= rs_sma20.iloc[-1] or rs_sma5.iloc[-1] <= rs_sma5.iloc[-3]:
                    rs_outperforming = False
            
            # 2. Trend & Support Filter: Price sustaining above 20-EMA and 50-EMA
            if close_price <= ema20.iloc[-1] or close_price <= ema50.iloc[-1]:
                continue
                
            # 4. DMA Filter: Price must be above all major DMAs (20, 50, 100, 200 DMA)
            if close_price <= dma20_val or close_price <= dma50_val or close_price <= dma100_val or close_price <= dma200_val:
                continue
                
            # 3. Momentum Filter: Bullish EMA Crossover (9-EMA > 21-EMA)
            if ema9.iloc[-1] <= ema21.iloc[-1]:
                continue
                
            # Advanced Filter A: RSI must be in strong but not overbought momentum range (55-75)
            if rsi_val < 55 or rsi_val > 75:
                continue
                
            # Advanced Filter B: Price must not be overextended (Close - EMA20 <= 1.5 * ATR)
            if (close_price - ema20.iloc[-1]) > 1.5 * atr_val:
                continue
                
            # Advanced Filter C: Stock must possess relative strength outperformance
            if not rs_outperforming:
                continue
                
            # Check if crossover is fresh (occurred in the last 5 trading sessions)
            was_below = False
            for i in range(-5, -1):
                if ema9.iloc[i] <= ema21.iloc[i]:
                    was_below = True
                    break
            crossover_type = "fresh" if was_below else "established"
            
            # 4. Volume Action: Daily volume > 10-day Average Volume
            vol_sma10 = df['Volume'].rolling(window=10).mean()
            avg_vol10 = vol_sma10.iloc[-1]
            if volume <= avg_vol10 or avg_vol10 == 0:
                continue
                
            vol_expansion_factor = volume / avg_vol10
            
            passed_stocks.append({
                "symbol": symbol.replace(".NS", ""),
                "close": round(close_price, 2),
                "turnover_cr": round(turnover / 10000000, 2),
                "vol_expansion": round(vol_expansion_factor, 2),
                "crossover_type": crossover_type,
                "high": round(df['High'].iloc[-1], 2),
                "low": round(df['Low'].iloc[-1], 2),
                "rsi": rsi_val,
                "atr": atr_val,
                "dma20": round(dma20_val, 2),
                "dma50": round(dma50_val, 2),
                "dma100": round(dma100_val, 2),
                "dma200": round(dma200_val, 2),
                "dma_aligned": dma_aligned,
                "car_1y": car_1y
            })
            
        except Exception as e:
            # Skip any error-prone symbol silently to ensure main execution finishes
            continue
            
    print(f"Found {len(passed_stocks)} stocks passing primary filters. Fetching Intraday VWAP & Fundamentals...")
    
    if not passed_stocks:
        return []
        
    final_candidates = []
    
    # Step 2: Fetch intraday 15m data and check VWAP
    passed_symbols = [f"{s['symbol']}.NS" for s in passed_stocks]
    try:
        intraday_data = yf.download(passed_symbols, period='1d', interval='15m', group_by='ticker', progress=False)
    except Exception as e:
        print(f"Error fetching intraday data: {e}")
        intraday_data = None
        
    for stock in passed_stocks:
        symbol = stock['symbol']
        ticker_symbol = f"{symbol}.NS"
        
        try:
            # Compute daily VWAP from 15m candles
            vwap = None
            if intraday_data is not None:
                idf = None
                if isinstance(intraday_data.columns, pd.MultiIndex):
                    if ticker_symbol in intraday_data.columns.levels[0]:
                        idf = intraday_data[ticker_symbol].dropna()
                else:
                    # Single ticker fallback
                    idf = intraday_data.dropna()
                
                if idf is not None and not idf.empty:
                    if all(col in idf.columns for col in ['High', 'Low', 'Close', 'Volume']):
                        typical_price_vol = ((idf['High'] + idf['Low'] + idf['Close']) / 3) * idf['Volume']
                        total_vol = idf['Volume'].sum()
                        if total_vol > 0:
                            vwap = typical_price_vol.sum() / total_vol
            
            # Fallback to EOD Typical Price if intraday data is missing
            if vwap is None:
                vwap = (stock['high'] + stock['low'] + stock['close']) / 3
                
            # 5. VWAP Filter: Closing price must be above daily VWAP
            if stock['close'] <= vwap:
                continue
                
            pct_above_vwap = ((stock['close'] - vwap) / vwap) * 100.0
            
            # 6. Quality & Sales Turnover Filter
            # Check yfinance ticker info
            ticker_obj = yf.Ticker(ticker_symbol)
            
            # Default fallback values
            revenue_cr = 0
            market_cap_cr = 0
            
            try:
                # Fetch info dictionary
                info = ticker_obj.info
                # Revenue in INR
                total_revenue = info.get('totalRevenue')
                if total_revenue:
                    revenue_cr = total_revenue / 10000000
                
                market_cap = info.get('marketCap')
                if market_cap:
                    market_cap_cr = market_cap / 10000000
            except Exception:
                pass # Fallback to market cap or basic checks if info fails
                
            # Quality Rule: Exclude operator small caps. Verify Sales > 100Cr OR Market Cap > 500Cr.
            # If info failed or has no data, we fallback to accepting it since it's already in Nifty 500
            # and passed the 10Cr daily turnover filter, which itself guarantees high liquidity.
            if revenue_cr > 0 and revenue_cr < 100:
                # If revenue is explicitly available and less than 100Cr, check market cap
                if market_cap_cr > 0 and market_cap_cr < 500:
                    continue # Exclude
            elif revenue_cr == 0 and market_cap_cr > 0 and market_cap_cr < 500:
                continue # Exclude
                
            # Generate the dynamic technical "Why"
            car_str = f"+{stock['car_1y']:.1f}%" if stock['car_1y'] >= 0 else f"{stock['car_1y']:.1f}%"
            alignment_desc = "bullish DMA alignment (20>50>100>200)" if stock['dma_aligned'] else "sustaining above all key DMAs (20, 50, 100, 200)"
            why_reason = f"Outperforming market (RSI: {stock['rsi']:.1f}, 1Y CAR: {car_str}), closed {pct_above_vwap:.1f}% above VWAP with {alignment_desc} and {stock['vol_expansion']:.1f}x volume expansion."
            
            final_candidates.append({
                "symbol": symbol,
                "close": stock['close'],
                "turnover": stock['turnover_cr'],
                "vol_expansion": stock['vol_expansion'],
                "why": why_reason,
                "dma20": stock['dma20'],
                "dma50": stock['dma50'],
                "dma100": stock['dma100'],
                "dma200": stock['dma200'],
                "dma_aligned": stock['dma_aligned'],
                "car_1y": round(stock['car_1y'], 1),
                "rsi": round(stock['rsi'], 1)
            })
            
        except Exception as e:
            print(f"Error processing final filters for {symbol}: {e}")
            
    # Sort final candidate stocks by volume expansion factor (highest momentum first)
    final_candidates = sorted(final_candidates, key=lambda x: x['vol_expansion'], reverse=True)
    
    # Process through Next-Day Momentum Stock Intelligence Engine
    from momentum_intelligence_engine import process_nextday_stock_intelligence
    enriched_candidates = []
    
    for cand in final_candidates:
        s_data = {
            "symbol": cand["symbol"],
            "Close": cand["close"],
            "Open": cand["close"] * 0.99,
            "High": cand["close"] * 1.01,
            "Low": cand["close"] * 0.98,
            "Volume": int(cand["vol_expansion"] * 1000000),
            "dma20": cand["dma20"],
            "dma50": cand["dma50"],
            "dma100": cand["dma100"],
            "dma200": cand["dma200"],
            "ema9": cand["close"] * 0.99,
            "ema21": cand["dma20"],
            "ema50": cand["dma50"],
            "ema200": cand["dma200"],
            "rsi": cand["rsi"],
            "atr": round(cand["close"] * 0.02, 2),
            "adx": 26.0,
            "rvol": cand["vol_expansion"],
            "car_1y": cand["car_1y"]
        }
        res = process_nextday_stock_intelligence(s_data)
        cand["momentum_intelligence"] = res
        enriched_candidates.append(cand)

    # Save to data/momentum_intelligence.json
    try:
        os.makedirs("data", exist_ok=True)
        m_path = os.path.join("data", "momentum_intelligence.json")
        payload = sanitize_for_json({
            "timestamp": datetime.now().strftime("%d-%b-%Y %I:%M %p"),
            "total_candidates": len(enriched_candidates),
            "candidates": enriched_candidates
        })
        with open(m_path, "w") as f:
            json.dump(payload, f, indent=2, cls=NumpyEncoder)
        print(f"[INFO] Saved Next-Day Momentum Intelligence payload to {m_path}")
    except Exception as e:
        print(f"Warning saving momentum_intelligence.json: {e}")

    return enriched_candidates

def generate_report(stock_data):
    """Compiles the analytical results into a beautiful, ready-to-publish Markdown report."""
    date_str = datetime.now().strftime('%d-%b-%Y')
    
    report = []
    report.append(f"📅 **Daily Stock Momentum & Market Wrap - {date_str}**")
    report.append("\n" + "="*45 + "\n")
    
    # Stock Momentum Screener Section
    report.append("🚀 **Momentum Stocks (3-10% Short-Term Potential Setups)**")
    report.append("Screener Criteria: Daily Turnover > ₹10 Cr | Above 20/50/100/200 DMAs | Volume Expansion | Price > VWAP.\n")
    
    if not stock_data:
        report.append("*No high-probability momentum setups met the strict quality and liquidity criteria today. Staying in cash is also a position.*")
    else:
        # Show top 10 momentum setups sorted by volume expansion
        for idx, stock in enumerate(stock_data[:10], 1):
            report.append(f"{idx}. **NSE: {stock['symbol']}** (Price: ₹{stock['close']})")
            report.append(f"   🔍 *Technical Setup*: {stock['why']}\n")
            
        if len(stock_data) > 10:
            report.append(f"*(Total {len(stock_data)} setups passed filters, displaying top 10 highest-momentum setups ranked by volume expansion)*\n")
            
    report.append("="*45 + "\n")
    
    # Mandatory SEBI Educational Disclaimer
    report.append("⚠️ *Disclaimer: This report is generated via AI for strictly EDUCATIONAL PURPOSES. I am not a SEBI-registered advisor. The setups discussed are technical probabilities, not buy/sell recommendations. Please do your own research.*")
    
    final_report = "\n".join(report)
    return final_report

def send_to_telegram(report, token, chat_id):
    """Sends the formatted report to a Telegram chat/channel using the Telegram Bot API.
    Splits the message automatically if it exceeds Telegram's 4096 character limit.
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    MAX_LENGTH = 4000
    
    if len(report) <= MAX_LENGTH:
        payload = {
            "chat_id": chat_id,
            "text": report,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(url, json=payload, timeout=15)
            if response.status_code == 200:
                print("[INFO] Report sent successfully to Telegram!")
            else:
                print(f"[ERROR] Telegram sending failed: {response.text}")
        except Exception as e:
            print(f"[ERROR] Exception sending to Telegram: {e}")
    else:
        print(f"[INFO] Report length ({len(report)}) exceeds limit. Sending in parts...")
        parts = [report[i:i+MAX_LENGTH] for i in range(0, len(report), MAX_LENGTH)]
        for idx, part in enumerate(parts):
            payload = {
                "chat_id": chat_id,
                "text": f"*Part {idx+1}/{len(parts)}*\n\n" + part,
                "parse_mode": "Markdown"
            }
            try:
                response = requests.post(url, json=payload, timeout=15)
                if response.status_code == 200:
                    print(f"[INFO] Part {idx+1} sent successfully to Telegram!")
                else:
                    print(f"[ERROR] Part {idx+1} failed: {response.text}")
            except Exception as e:
                print(f"[ERROR] Exception sending part {idx+1}: {e}")

def send_to_whatsapp_callmebot(report, phone, apikey):
    """Fallback notification via CallMeBot API."""
    from urllib.parse import quote
    clean_report = report.replace("*", "").replace("#", "")
    encoded_msg = quote(clean_report)
    url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&apikey={apikey}&text={encoded_msg}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            print("[INFO] Successfully sent report to WhatsApp via CallMeBot!")
        else:
            print(f"[ERROR] WhatsApp CallMeBot sending failed: {response.text}")
    except Exception as e:
        print(f"[ERROR] Exception sending to WhatsApp: {e}")

def main():
    print("=========================================")
    print("       MARKETMENTOR AI AUTOMATION        ")
    print("=========================================")
    
    # Fetch data
    nifty_symbols = fetch_nifty500_symbols()
    
    # Run stock momentum analysis
    stock_results = screen_stocks(nifty_symbols)
    
    # Generate report
    report = generate_report(stock_results)
    
    # Save to JSON for Web UI Dashboard
    os.makedirs("data", exist_ok=True)
    evening_data = sanitize_for_json({
        "date": datetime.now().strftime("%d-%b-%Y"),
        "momentum_stocks": stock_results
    })
    try:
        with open("data/evening.json", "w") as jf:
            json.dump(evening_data, jf, indent=2, cls=NumpyEncoder)
        print("[INFO] Successfully saved evening results to data/evening.json")
    except Exception as e:
        print(f"[ERROR] Failed to save evening.json: {e}")
    
    # Save report to file
    report_filename = f"MarketWrap_{datetime.now().strftime('%Y%m%d')}.md"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report)
        
    print("\n=========================================")
    print(f"Report generated successfully: {report_filename}")
    print("=========================================\n")
    print(report)
    
    from telegram_config import get_telegram_credentials
    bot_token, chat_id = get_telegram_credentials()
    if bot_token and chat_id:
        print("\n[BROADCAST] Broadcasting to Telegram...")
        send_to_telegram(report, bot_token, chat_id)

if __name__ == "__main__":
    main()
