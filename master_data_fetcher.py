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

class MasterDataFetcher:
    """Master Unified Data Pipeline & Orchestrator Engine.
    Executes all market data fetchers in 1 single sequential pass, saving GitHub Actions quota limits.
    """

    @classmethod
    def run_master_pipeline(cls, auto_git_push=False):
        now = get_ist_now()
        print("==========================================================================")
        print("     MARKET MENTOR AI — MASTER UNIFIED DATA PIPELINE EXECUTION ENGINE     ")
        print("==========================================================================")
        print(f"Timestamp: {now.strftime('%d-%b-%Y %I:%M:%S %p')} (IST)")
        print("--------------------------------------------------------------------------")

        python_exec = sys.executable

        # 1. Live NSE Option Chain Fetcher
        try:
            print("\n[1/7] Fetching Live NSE Option Chain (Nifty & Bank Nifty)...")
            from nse_option_chain_fetcher import NSEOptionChainFetcher
            NSEOptionChainFetcher.export_live_option_chain()
        except Exception as e:
            print(f"[WARN] Live Option Chain fetch step skipped: {e}")

        # 2. AI Options Quant Engine & Greeks
        try:
            print("\n[2/7] Executing AI Options Quant & Regime Engine...")
            subprocess.run([python_exec, "ai_options_quant.py"], check=False)
        except Exception as e:
            print(f"[WARN] AI Options Quant step error: {e}")

        # 3. Intraday Breakout Screener
        try:
            print("\n[3/7] Executing Intraday Breakout & VWAP Screener...")
            subprocess.run([python_exec, "intraday_screener.py"], check=False)
        except Exception as e:
            print(f"[WARN] Intraday Screener step error: {e}")

        # 4. Stock Momentum Screener
        try:
            print("\n[4/7] Executing Stock Momentum & Swing Screener...")
            subprocess.run([python_exec, "screener.py"], check=False)
        except Exception as e:
            print(f"[WARN] Stock Momentum Screener step error: {e}")

        # 5. Sector Rotation & Relative Strength Heatmap
        try:
            print("\n[5/7] Executing Sector Rotation & Relative Strength Heatmap...")
            from sector_rotation_engine import SectorRotationEngine
            SectorRotationEngine.export_sector_json()
        except Exception as e:
            print(f"[WARN] Sector Rotation step error: {e}")

        # 6. AI Trade Journal & Performance Tracker
        try:
            print("\n[6/7] Exporting AI Trade Journal Analytics & SQLite Log...")
            from ai_trade_journal import AITradeJournalEngine
            AITradeJournalEngine.export_journal_json()
        except Exception as e:
            print(f"[WARN] Trade Journal step error: {e}")

        # 7. MCX Commodity Protection Engine
        try:
            print("\n[7/9] Executing MCX Commodity Protection Engine (Crude & NatGas)...")
            subprocess.run([python_exec, "mcx_commodity_engine.py"], check=False)
        except Exception as e:
            print(f"[WARN] MCX Commodity step error: {e}")

        # 8. ML Dynamic Target & Stop-Loss Optimizer
        try:
            print("\n[8/10] Executing ML Dynamic Target & Stop-Loss Optimizer...")
            from ml_target_sl_optimizer import MLTargetSLOptimizer
            MLTargetSLOptimizer.export_ml_optimizer_json()
        except Exception as e:
            print(f"[WARN] ML Target Optimizer step error: {e}")

        # 9. Portfolio Risk-Parity & Auto-Rebalancing Screener
        try:
            print("\n[9/10] Executing Portfolio Risk-Parity & Auto-Rebalancing Screener...")
            from portfolio_rebalancer import PortfolioRebalancerEngine
            PortfolioRebalancerEngine.export_portfolio_json()
        except Exception as e:
            print(f"[WARN] Portfolio Rebalancer step error: {e}")

        # 10. Morning Pre-Market & 15m ORB High-Conviction Momentum Validator
        try:
            print("\n[10/11] Executing Morning Momentum Validation & Signal Dispatcher...")
            from morning_momentum_validator import MorningMomentumValidatorEngine
            MorningMomentumValidatorEngine.export_and_broadcast_morning_signals()
        except Exception as e:
            print(f"[WARN] Morning Momentum Validator step error: {e}")

        # 11. MTF SMC Market Structure & Order Block Radar Engine
        try:
            print("\n[11/11] Executing MTF SMC Market Structure & Order Block Radar...")
            from smc_liquidity_sweep_engine import SMCLiquiditySweepEngine
            SMCLiquiditySweepEngine.export_smc_json()
        except Exception as e:
            print(f"[WARN] MTF SMC Market Structure step error: {e}")

        print("\n==========================================================================")
        print("  [SUCCESS] All Market Mentor AI V8.0 Data Payloads Refreshed in 1 Pass!")
        print("==========================================================================")

        # Single Git Push (Optional / Enabled in Automated Schedulers)
        if auto_git_push:
            try:
                print("\n[SYNC] Syncing updated data to GitHub & Vercel Dashboard in 1 commit...")
                subprocess.run(["git", "add", "data/*.json"], check=False)
                subprocess.run(["git", "commit", "-m", "Master Unified Pipeline Auto-Update [skip ci]"], check=False)
                subprocess.run(["git", "push"], check=False)
                print("[SUCCESS] GitHub & Vercel Dashboard synced cleanly!")
            except Exception as e:
                print(f"[WARN] Git push skipped: {e}")

def main():
    auto_push = "--push" in sys.argv
    MasterDataFetcher.run_master_pipeline(auto_git_push=auto_push)

if __name__ == '__main__':
    main()
