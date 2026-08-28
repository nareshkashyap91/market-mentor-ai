import os
import sys
import time
import subprocess
from datetime import datetime, timezone, timedelta

def get_ist_now():
    return datetime.now(timezone(timedelta(hours=5, minutes=30)))

def is_market_open():
    now = get_ist_now()
    # Monday = 0, Sunday = 6
    if now.weekday() >= 5:
        return False
    market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_start <= now <= market_end

def run_pulse():
    print(f"\n========================================================")
    print(f"🚀 RUNNING LOCAL AI OPTIONS QUANT ENGINE & TELEGRAM PULSE")
    print(f"🕒 Time: {get_ist_now().strftime('%Y-%m-%d %H:%M:%S')} (IST)")
    print(f"========================================================")
    
    python_exec = sys.executable
    
    try:
        print("[1/2] Executing ai_options_quant.py...")
        subprocess.run([python_exec, "ai_options_quant.py"], check=True)
    except Exception as e:
        print(f"[ERROR] Failed to run ai_options_quant.py: {e}")
        
    try:
        print("[2/2] Executing intraday_screener.py...")
        subprocess.run([python_exec, "intraday_screener.py"], check=True)
    except Exception as e:
        print(f"[ERROR] Failed to run intraday_screener.py: {e}")
        
    # Auto-push to GitHub/Vercel
    try:
        print("[SYNC] Pushing updated JSON data to GitHub...")
        subprocess.run(["git", "add", "data/*.json"], check=False)
        subprocess.run(["git", "commit", "-m", "Local Scheduler Auto-Update [skip ci]"], check=False)
        subprocess.run(["git", "push"], check=False)
        print("[SUCCESS] Data synced to GitHub & Vercel!")
    except Exception as e:
        print(f"[WARN] Git push skipped/failed: {e}")

def main():
    print("========================================================")
    print("      MARKET MENTOR AI - LOCAL AUTOMATED SCHEDULER      ")
    print("========================================================")
    print("This script runs 15-minute scans & Telegram alerts 100% FREE!")
    print("No GitHub Actions quota limit required.")
    print("--------------------------------------------------------")
    
    # Run once immediately on launch
    run_pulse()
    
    interval_seconds = 15 * 60  # 15 minutes
    
    while True:
        now = get_ist_now()
        print(f"\n[IDLE] Waiting for next 15-minute scan cycle... (Current IST: {now.strftime('%H:%M:%S')})")
        
        for remaining in range(interval_seconds, 0, -1):
            mins, secs = divmod(remaining, 60)
            sys.stdout.write(f"\r⏱ Next scan in: {mins:02d}:{secs:02d} | Ctrl+C to stop ")
            sys.stdout.flush()
            time.sleep(1)
            
        run_pulse()

if __name__ == '__main__':
    main()
