import io
import os
import sys
import json
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from mftool import Mftool

# Ensure terminal outputs emojis correctly on Windows
sys.stdout.reconfigure(encoding='utf-8')

def send_to_telegram(message, bot_token, chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # Telegram message limit is 4096 characters. Split if needed.
    if len(message) <= 4000:
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        try:
            res = requests.post(url, json=payload, timeout=15)
            if res.status_code == 200:
                print("[INFO] Weekly Mutual Fund Report sent successfully to Telegram!")
            else:
                print(f"[ERROR] Telegram failed: {res.text}")
        except Exception as e:
            print(f"[ERROR] Exception sending to Telegram: {e}")
    else:
        print(f"[INFO] Report length ({len(message)}) exceeds limit. Sending in parts...")
        parts = [message[i:i+3800] for i in range(0, len(message), 3800)]
        for idx, part in enumerate(parts):
            payload = {"chat_id": chat_id, "text": f"*Part {idx+1}/{len(parts)}*\n\n" + part, "parse_mode": "Markdown"}
            try:
                requests.post(url, json=payload, timeout=15)
            except Exception as e:
                print(f"[ERROR] Exception sending part {idx+1}: {e}")

def calculate_cagr(start_nav, end_nav, years):
    if start_nav <= 0 or end_nav <= 0 or years <= 0:
        return None
    cagr = ((end_nav / start_nav) ** (1 / years) - 1) * 100
    return round(cagr, 2)

def analyze_mutual_funds():
    print("--- Processing Weekly Mutual Fund CAGR Rankings ---")
    mf = Mftool()
    
    selected_schemes = {
        "Large Cap": [
            {"code": "120586", "name": "ICICI Prudential Large Cap Fund - Direct Growth"},
            {"code": "119598", "name": "SBI Large Cap Fund - Direct Growth"},
            {"code": "118834", "name": "Mirae Asset Large Cap Fund - Direct Growth"}
        ],
        "Mid Cap": [
            {"code": "120186", "name": "Kotak Emerging Equity Fund - Direct Growth"},
            {"code": "127042", "name": "Motilal Oswal Midcap Fund - Direct Growth"},
            {"code": "118989", "name": "HDFC Mid-Cap Opportunities Fund - Direct Growth"}
        ],
        "Small Cap": [
            {"code": "120828", "name": "Quant Small Cap Fund - Direct Growth"},
            {"code": "118778", "name": "Nippon India Small Cap Fund - Direct Growth"},
            {"code": "125497", "name": "SBI Small Cap Fund - Direct Growth"}
        ],
        "Flexi Cap": [
            {"code": "120847", "name": "Quant Flexi Cap Fund - Direct Growth"},
            {"code": "119063", "name": "HDFC Flexi Cap Fund - Direct Growth"},
            {"code": "122639", "name": "Parag Parikh Flexi Cap Fund - Direct Growth"}
        ]
    }
    
    results = {}
    
    for category, schemes in selected_schemes.items():
        print(f"Analyzing {category} Mutual Funds...")
        category_results = []
        
        for scheme in schemes:
            code = scheme["code"]
            name = scheme["name"]
            
            try:
                hist = mf.get_scheme_historical_nav(code, as_Dataframe=True)
                if hist is not None and not hist.empty:
                    hist['nav'] = pd.to_numeric(hist['nav'], errors='coerce')
                    hist.index = pd.to_datetime(hist.index, format='%d-%m-%Y')
                    hist = hist.sort_index()
                    
                    latest_row = hist.iloc[-1]
                    latest_nav = float(latest_row['nav'])
                    latest_date = hist.index[-1]
                    
                    def get_nav_years_ago(years):
                        target_date = latest_date - pd.DateOffset(years=years)
                        idx = hist.index.get_indexer([target_date], method='nearest')[0]
                        return float(hist.iloc[idx]['nav'])
                    
                    nav_1y = get_nav_years_ago(1)
                    nav_3y = get_nav_years_ago(3)
                    nav_5y = get_nav_years_ago(5)
                    nav_10y = get_nav_years_ago(10)
                    
                    cagr_1y = calculate_cagr(nav_1y, latest_nav, 1)
                    cagr_3y = calculate_cagr(nav_3y, latest_nav, 3)
                    cagr_5y = calculate_cagr(nav_5y, latest_nav, 5)
                    cagr_10y = calculate_cagr(nav_10y, latest_nav, 10)
                    
                    category_results.append({
                        "name": name,
                        "cagr_1y": cagr_1y,
                        "cagr_3y": cagr_3y,
                        "cagr_5y": cagr_5y,
                        "cagr_10y": cagr_10y,
                        "latest_nav": latest_nav,
                        "latest_date": latest_date.strftime("%d-%b-%Y"),
                        "why": f"Consistently compounding at {cagr_3y}% over the medium term, demonstrating robust downside protection and portfolio quality."
                    })
            except Exception as e:
                print(f"[WARNING] Could not fetch data for MF scheme {code} ({name}): {e}")
                
        category_results.sort(key=lambda x: x['cagr_3y'] if x['cagr_3y'] is not None else -999, reverse=True)
        results[category] = category_results
        
    return results

def main():
    print("=========================================")
    print("  MARKETMENTOR WEEKLY MUTUAL FUND ENGINE ")
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
        except Exception as e:
            print(f"[WARNING] Could not parse config.json: {e}")

    mf_results = analyze_mutual_funds()
    
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    date_str = datetime.now(ist_tz).strftime("%d-%b-%Y")
    
    # Save to data/mutual_funds.json
    os.makedirs("data", exist_ok=True)
    json_path = os.path.join("data", "mutual_funds.json")
    
    payload = {
        "date": date_str,
        "mutual_funds": mf_results
    }
    
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"[INFO] Saved mutual fund data to {json_path}")

    # Build Telegram Report Message
    msg = f"🏆 **WEEKLY MUTUAL FUND WEALTH COMPOUNDING REPORT**\n"
    msg += f"📅 **Date**: {date_str}\n"
    msg += f"Ranked by historical Direct Growth CAGR returns. Ideal for long-term SIP wealth creation.\n\n"
    
    category_emojis = {
        "Large Cap": "🏆 Large Cap (Stable Leaders)",
        "Mid Cap": "🚀 Mid Cap (High Growth)",
        "Small Cap": "🌟 Small Cap (Maximum Alpha)",
        "Flexi Cap": "🛡️ Flexi Cap (Dynamic Asset Allocation)"
    }
    
    for cat, funds in mf_results.items():
        header = category_emojis.get(cat, cat)
        msg += f"### {header}\n"
        for idx, f in enumerate(funds):
            msg += (
                f"{idx+1}. **{f['name']}**\n"
                f"   📈 *CAGR*: 1Y: **{f['cagr_1y']}%** | 3Y: **{f['cagr_3y']}%** | 5Y: **{f['cagr_5y']}%** | 10Y: **{f['cagr_10y']}%**\n"
                f"   🔍 *NAV*: ₹{f['latest_nav']} ({f['latest_date']})\n\n"
            )
            
    msg += "⚠️ *Disclaimer: For educational purposes only. Past returns do not guarantee future performance.*"

    if tg_token and tg_chat_id:
        send_to_telegram(msg, tg_token, tg_chat_id)

if __name__ == '__main__':
    main()
