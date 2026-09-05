import os
import sys
import time
import subprocess
from datetime import datetime, timezone, timedelta

# Fix Windows console UTF-8 encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def get_ist_now():
    return datetime.now(timezone(timedelta(hours=5, minutes=30)))

def is_mcx_open():
    now = get_ist_now()
    if now.weekday() >= 5:
        return False
    mcx_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
    mcx_end = now.replace(hour=23, minute=30, second=0, microsecond=0)
    return mcx_start <= now <= mcx_end

def run_pulse():
    now = get_ist_now()
    print(f"\n========================================================")
    print(f"RUNNING LOCAL AI OPTIONS QUANT ENGINE & TELEGRAM PULSE")
    print(f"Time: {now.strftime('%Y-%m-%d %H:%M:%S')} (IST)")
    print(f"========================================================")
    
    if now.weekday() >= 5:
        print("⏸️ [MARKET CLOSED] Today is WEEKEND (Saturday/Sunday). Auto-scans & Intraday notifications are PAUSED.")
        print("💡 Tip: Send /status or /mcx on Telegram anytime for on-demand analysis.")
        return

    python_exec = sys.executable
    
    try:
        print("[MASTER] Executing master_data_fetcher.py (Single Pass Unified Data Pipeline)...")
        subprocess.run([python_exec, "master_data_fetcher.py", "--push"], check=True)
    except Exception as e:
        print(f"[ERROR] Failed to run master_data_fetcher.py: {e}")

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
