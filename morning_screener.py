import io
import os
import sys
import json
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime

# Ensure terminal outputs emojis correctly on Windows
sys.stdout.reconfigure(encoding='utf-8')

def get_gift_nifty():
    """Scrapes GIFT Nifty data from NiftyTrader NEXT_DATA state."""
    url = 'https://www.niftytrader.in/gift-nifty-live'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            text = response.text
            idx = text.find('id="__NEXT_DATA__"')
            if idx != -1:
                start = text.find('{', idx)
                end = text.find('</script>', start)
                data = json.loads(text[start:end])
                props = data.get('props', {})
                pageProps = props.get('pageProps', {})
                gift_data = pageProps.get('initialGiftData', {})
                
                # Extract details
                price = gift_data.get('last_trade_price')
                prev_close = gift_data.get('close')
                change = gift_data.get('change_value')
                change_pct = gift_data.get('change_per')
                
                if price is not None:
                    return {
                        "price": float(price),
                        "prev_close": float(prev_close) if prev_close else None,
                        "change": float(change) if change is not None else 0.0,
                        "change_pct": float(change_pct) if change_pct is not None else 0.0
                    }
    except Exception as e:
        print(f"[WARNING] Failed to fetch GIFT Nifty details: {e}")
    return None

def fetch_yfinance_quote(ticker):
    """Fetches EOD or near-real-time price and percent change for a ticker."""
    try:
        df = yf.download(ticker, period='5d', interval='1d', progress=False)
        if not df.empty:
            # Handle MultiIndex
            if isinstance(df.columns, pd.MultiIndex):
                close = df['Close'][ticker].dropna()
                open_val = df['Open'][ticker].dropna()
            else:
                close = df['Close'].dropna()
                open_val = df['Open'].dropna()
                
            if len(close) >= 2:
                latest_close = close.iloc[-1]
                prev_close = close.iloc[-2]
                change = latest_close - prev_close
                pct_change = (change / prev_close) * 100
                return round(latest_close, 2), round(pct_change, 2)
            elif len(close) == 1:
                # If only 1 day available, calculate change from open
                latest_close = close.iloc[-1]
                latest_open = open_val.iloc[-1]
                change = latest_close - latest_open
                pct_change = (change / latest_open) * 100 if latest_open != 0 else 0
                return round(latest_close, 2), round(pct_change, 2)
    except Exception as e:
        print(f"[WARNING] Error fetching ticker {ticker}: {e}")
    return None, None

def send_to_telegram(report, bot_token, chat_id):
    """Sends the formatted morning report to Telegram, splitting if necessary."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # Telegram limit is 4096. We split at 4000 for safety.
    if len(report) <= 4000:
        payload = {
            "chat_id": chat_id,
            "text": report,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(url, json=payload, timeout=15)
            if response.status_code == 200:
                print("[INFO] Successfully sent report to Telegram!")
            else:
                print(f"[ERROR] Telegram sending failed: {response.text}")
        except Exception as e:
            print(f"[ERROR] Exception sending to Telegram: {e}")
    else:
        # Split logic
        lines = report.split("\n")
        chunks = []
        current_chunk = []
        current_length = 0
        for line in lines:
            if current_length + len(line) + 1 > 4000:
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_length = len(line)
            else:
                current_chunk.append(line)
                current_length += len(line) + 1
        if current_chunk:
            chunks.append("\n".join(current_chunk))
            
        print(f"[INFO] Report length ({len(report)}) exceeds limit. Sending in {len(chunks)} parts...")
        for idx, chunk in enumerate(chunks, 1):
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "Markdown"
            }
            try:
                response = requests.post(url, json=payload, timeout=15)
                if response.status_code == 200:
                    print(f"[INFO] Part {idx} sent successfully to Telegram!")
                else:
                    print(f"[ERROR] Part {idx} sending failed: {response.text}")
            except Exception as e:
                print(f"[ERROR] Exception sending Part {idx}: {e}")

def main():
    print("=========================================")
    print("      MARKETMENTOR MORNING ENGINE        ")
    print("=========================================")
    
    # 1. Fetch GIFT Nifty Data
    print("Fetching GIFT Nifty status...")
    gift = get_gift_nifty()
    
    # 2. Fetch Global Indices
    print("Fetching global market indicators...")
    sp500_price, sp500_pct = fetch_yfinance_quote("^GSPC")
    dow_price, dow_pct = fetch_yfinance_quote("^DJI")
    nas_price, nas_pct = fetch_yfinance_quote("^IXIC")
    nikkei_price, nikkei_pct = fetch_yfinance_quote("^N225")
    hangseng_price, hangseng_pct = fetch_yfinance_quote("^HSI")
    
    # 3. Fetch Commodities & Yields
    crude_price, crude_pct = fetch_yfinance_quote("BZ=F")
    gold_price, gold_pct = fetch_yfinance_quote("GC=F")
    dxy_price, dxy_pct = fetch_yfinance_quote("DX-Y.NYB")
    bond_price, bond_pct = fetch_yfinance_quote("^TNX")
    
    # 4. Fetch Nifty Spot
    nifty_price, nifty_pct = fetch_yfinance_quote("^NSEI")
    
    # Calculate pre-market sentiment
    sentiment_emoji = "⚖️"
    sentiment_text = "Flat / Neutral Open"
    gap_desc = "implied flat opening"
    
    if gift and gift['change'] is not None:
        change_val = gift['change']
        if change_val > 30:
            sentiment_emoji = "🟢"
            sentiment_text = "Bullish Gap Up"
            gap_desc = f"implied Gap Up opening of ~{abs(int(change_val))} points"
        elif change_val < -30:
            sentiment_emoji = "🔴"
            sentiment_text = "Bearish Gap Down"
            gap_desc = f"implied Gap Down opening of ~{abs(int(change_val))} points"
        else:
            gap_desc = f"implied flat opening (~{int(change_val)} points)"
            
    # Calculate Pivot Levels for Nifty Spot (Support/Resistance)
    s1, s2, r1, r2 = None, None, None, None
    try:
        nifty_hist = yf.download("^NSEI", period='2d', interval='1d', progress=False)
        if len(nifty_hist) >= 1:
            # Handle MultiIndex
            if isinstance(nifty_hist.columns, pd.MultiIndex):
                high = nifty_hist['High']['^NSEI'].iloc[-1]
                low = nifty_hist['Low']['^NSEI'].iloc[-1]
                close = nifty_hist['Close']['^NSEI'].iloc[-1]
            else:
                high = nifty_hist['High'].iloc[-1]
                low = nifty_hist['Low'].iloc[-1]
                close = nifty_hist['Close'].iloc[-1]
                
            pivot = (high + low + close) / 3
            r1 = (2 * pivot) - low
            s1 = (2 * pivot) - high
            r2 = pivot + (high - low)
            s2 = pivot - (high - low)
    except Exception as e:
        print(f"[WARNING] Could not compute Pivot levels: {e}")

    # Build dynamic insights
    insights = []
    if gift and gift['change_pct'] > 0.4:
        insights.append("- 🚀 **GIFT Nifty Cues**: Solid global cues indicate strong morning demand. Keep stop-losses trailed.")
    elif gift and gift['change_pct'] < -0.4:
        insights.append("- ⚠️ **Global Selling**: Negative pressure in offshore markets might trigger panic selling. Avoid rushing into morning longs.")
        
    if crude_pct and crude_pct > 1.5:
        insights.append(f"- 🛢️ **Crude Pressure**: Brent crude jumped +{crude_pct}%. Watch Paint, Tyre, and Oil Marketing Companies for pressure.")
    elif crude_pct and crude_pct < -1.5:
        insights.append(f"- 🟢 **Crude Cooling**: Drop in Brent Crude is positive for domestic input costs.")
        
    if dxy_price and dxy_price > 104.5:
        insights.append(f"- 💵 **Strong Dollar**: US Dollar Index (DXY) is elevated at {dxy_price}, which can cause FII capital outflows.")
        
    if sp500_pct and sp500_pct > 0.8:
        insights.append("- 🇺🇸 **Wall Street Rally**: S&P 500 closed strong, providing positive wind for IT and global sectors.")
    elif sp500_pct and sp500_pct < -0.8:
        insights.append("- 📉 **Wall Street Slide**: US market closed weak, caution advised for global index trackers.")
        
    if not insights:
        insights.append("- ⚖️ **Mixed Cues**: Global cues are neutral. Focus on stock-specific setups and watch index key levels.")

    # 5. Format Morning Report
    date_str = datetime.now().strftime('%d-%b-%Y')
    report = []
    report.append(f"📅 **Pre-Market Update & Global Clues - {date_str}**")
    report.append("\n" + "="*45 + "\n")
    
    # GIFT Nifty
    report.append(f"{sentiment_emoji} **GIFT Nifty Open Signal**")
    if gift:
        report.append(f"- **GIFT Nifty Price**: `{gift['price']:.1f}` ({gift['change']:+.1f} | {gift['change_pct']:+.2f}%)")
        report.append(f"- **Implied Open**: {sentiment_text} ({gap_desc})")
    else:
        report.append("- **GIFT Nifty Price**: `N/A` (Data connection offline)")
        report.append("- **Implied Open**: Neutral/Flat Open (Using Spot index clues)")
    report.append("\n" + "="*45 + "\n")
    
    # Global Markets
    report.append("🌎 **Global Indices (EOD / Live)**")
    if dow_price:
        report.append(f"- **US markets (Dow)**: `{dow_price:.1f}` ({dow_pct:+.2f}%)")
    if sp500_price:
        report.append(f"- **US markets (S&P 500)**: `{sp500_price:.1f}` ({sp500_pct:+.2f}%)")
    if nas_price:
        report.append(f"- **US markets (Nasdaq)**: `{nas_price:.1f}` ({nas_pct:+.2f}%)")
    if nikkei_price:
        report.append(f"- **Japan (Nikkei 225)**: `{nikkei_price:.1f}` ({nikkei_pct:+.2f}%)")
    if hangseng_price:
        report.append(f"- **Hong Kong (Hang Seng)**: `{hangseng_price:.1f}` ({hangseng_pct:+.2f}%)")
    report.append("\n" + "="*45 + "\n")
    
    # Macro Indicators
    report.append("📊 **Macro, Currencies & Commodities**")
    if crude_price:
        report.append(f"- **Brent Crude Oil**: `${crude_price:.2f}` ({crude_pct:+.2f}%)")
    if gold_price:
        report.append(f"- **Gold Futures**: `${gold_price:.1f}` ({gold_pct:+.2f}%)")
    if dxy_price:
        report.append(f"- **US Dollar Index (DXY)**: `{dxy_price:.2f}` ({dxy_pct:+.2f}%)")
    if bond_price:
        report.append(f"- **US 10Y Bond Yield**: `{bond_price:.2f}%` ({bond_pct:+.2f}%)")
    report.append("\n" + "="*45 + "\n")
    
    # Trading levels
    report.append("🔍 **Nifty 50 Key Pivot Levels**")
    if nifty_price:
        report.append(f"- **Nifty 50 Previous Close**: `{nifty_price:.2f}` ({nifty_pct:+.2f}%)")
    if s1 and r1:
        report.append(f"- **Resistance Levels**: R1: `{r1:.1f}` | R2: `{r2:.1f}`")
        report.append(f"- **Support Levels**: S1: `{s1:.1f}` | S2: `{s2:.1f}`")
    report.append("\n" + "="*45 + "\n")
    
    # Pre-Market Action Insights
    report.append("💡 **Pre-Market Action Strategy**")
    report.extend(insights)
    report.append("\n" + "="*45 + "\n")
    
    # Disclaimer
    report.append("⚠️ *Disclaimer: For educational purposes only. Intraday trading holds risk. Consult a SEBI registered advisor.*")
    
    final_report = "\n".join(report)
    print(final_report)
    
    # Save to JSON for Web UI Dashboard
    os.makedirs("data", exist_ok=True)
    morning_data = {
        "date": datetime.now().strftime("%d-%b-%Y"),
        "gift_nifty": {
            "price": gift["price"] if gift else None,
            "prev_close": gift["prev_close"] if gift else None,
            "change": gift["change"] if gift else 0.0,
            "change_pct": gift["change_pct"] if gift else 0.0,
            "open_signal": gap_desc if gift else "Flat Open"
        },
        "global_indices": [
            {"name": "Dow Jones", "price": dow_price, "change_pct": dow_pct},
            {"name": "S&P 500", "price": sp500_price, "change_pct": sp500_pct},
            {"name": "Nasdaq", "price": nas_price, "change_pct": nas_pct},
            {"name": "Nikkei 225", "price": nikkei_price, "change_pct": nikkei_pct},
            {"name": "Hang Seng", "price": hangseng_price, "change_pct": hangseng_pct}
        ],
        "macro": [
            {"name": "Brent Crude Oil", "price": crude_price, "change_pct": crude_pct},
            {"name": "Gold Futures", "price": gold_price, "change_pct": gold_pct},
            {"name": "Dollar Index (DXY)", "price": dxy_price, "change_pct": dxy_pct},
            {"name": "US 10Y Bond Yield", "price": bond_price, "change_pct": bond_pct}
        ],
        "nifty_pivots": {
            "close": nifty_price,
            "pct_change": nifty_pct,
            "r1": r1,
            "r2": r2,
            "s1": s1,
            "s2": s2
        },
        "insights": insights
    }
    
    try:
        with open("data/morning.json", "w") as jf:
            json.dump(morning_data, jf, indent=2)
        print("[INFO] Successfully saved morning pre-market clues to data/morning.json")
    except Exception as e:
        print(f"[ERROR] Failed to save morning.json: {e}")
    
    # 6. Broadcast report to Telegram
    env_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    env_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if env_token and env_chat_id:
        print("\n[BROADCAST] Broadcasting morning report to Telegram via Environment Variables...")
        send_to_telegram(final_report, env_token, env_chat_id)
    else:
        config_file = "config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as cf:
                    config = json.load(cf)
                
                tg = config.get("telegram", {})
                if tg.get("enabled", False):
                    print("\n[BROADCAST] Broadcasting morning report to Telegram...")
                    send_to_telegram(final_report, tg.get("bot_token"), tg.get("chat_id"))
            except Exception as e:
                print(f"\n[WARNING] Failed to load config or broadcast: {e}")

if __name__ == '__main__':
    main()
