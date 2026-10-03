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

    Exit-code contract (honest reporting):
      - Returns [] when every step succeeded  -> process exits 0 -> GitHub Actions run is GREEN.
      - Returns a non-empty failure list      -> process exits 1 -> run is RED and the user is
        notified that dashboard data is incomplete/stale. The workflow's commit step runs
        `if: always()`, so whatever payloads DID refresh still get pushed to the dashboard.
    """

    TOTAL_STEPS = 11

    @classmethod
    def run_master_pipeline(cls, auto_git_push=False):
        now = get_ist_now()
        failures = []
        print("==========================================================================")
        print("     MARKET MENTOR AI — MASTER UNIFIED DATA PIPELINE EXECUTION ENGINE     ")
        print("==========================================================================")
        print(f"Timestamp: {now.strftime('%d-%b-%Y %I:%M:%S %p')} (IST)")
        print("--------------------------------------------------------------------------")

        python_exec = sys.executable

        def run_subprocess(script_name, step_label):
            """Run a pipeline step as a subprocess; track honest pass/fail status."""
            try:
                result = subprocess.run([python_exec, script_name], check=False)
                if result.returncode != 0:
                    failures.append(f"{step_label} (exit code {result.returncode})")
                    print(f"[FAIL] {step_label} exited with code {result.returncode}")
                else:
                    print(f"[OK] {step_label} completed.")
            except Exception as e:
                failures.append(f"{step_label} ({e})")
                print(f"[FAIL] {step_label} could not be executed: {e}")

        def run_imported(step_label, func):
            """Run an in-process pipeline step; track honest pass/fail status."""
            try:
                func()
                print(f"[OK] {step_label} completed.")
            except Exception as e:
                failures.append(f"{step_label} ({e})")
                print(f"[FAIL] {step_label} raised: {e}")

        # 1. Live NSE Option Chain Fetcher
        print(f"\n[1/{cls.TOTAL_STEPS}] Fetching Live NSE Option Chain (Nifty & Bank Nifty)...")
        try:
            from nse_option_chain_fetcher import NSEOptionChainFetcher
            run_imported("Live NSE Option Chain", NSEOptionChainFetcher.export_live_option_chain)
        except Exception as e:
            failures.append(f"Live NSE Option Chain (import failed: {e})")
            print(f"[FAIL] Live Option Chain step: {e}")

        # 2. AI Options Quant Engine & Greeks
        print(f"\n[2/{cls.TOTAL_STEPS}] Executing AI Options Quant & Regime Engine...")
        run_subprocess("ai_options_quant.py", "AI Options Quant & Regime Engine")

        # 3. Intraday Breakout Screener
        print(f"\n[3/{cls.TOTAL_STEPS}] Executing Intraday Breakout & VWAP Screener...")
        run_subprocess("intraday_screener.py", "Intraday Breakout & VWAP Screener")

        # 4. Stock Momentum Screener
        print(f"\n[4/{cls.TOTAL_STEPS}] Executing Stock Momentum & Swing Screener...")
        run_subprocess("screener.py", "Stock Momentum & Swing Screener")

        # 5. Sector Rotation & Relative Strength Heatmap
        print(f"\n[5/{cls.TOTAL_STEPS}] Executing Sector Rotation & Relative Strength Heatmap...")
        try:
            from sector_rotation_engine import SectorRotationEngine
            run_imported("Sector Rotation & RS Heatmap", SectorRotationEngine.export_sector_json)
        except Exception as e:
            failures.append(f"Sector Rotation (import failed: {e})")
            print(f"[FAIL] Sector Rotation step: {e}")

        # 6. AI Trade Journal & Performance Tracker
        print(f"\n[6/{cls.TOTAL_STEPS}] Exporting AI Trade Journal Analytics & SQLite Log...")
        try:
            from ai_trade_journal import AITradeJournalEngine
            run_imported("AI Trade Journal & SQLite Log", AITradeJournalEngine.export_journal_json)
        except Exception as e:
            failures.append(f"Trade Journal (import failed: {e})")
            print(f"[FAIL] Trade Journal step: {e}")

        # 7. MCX Commodity Protection Engine
        print(f"\n[7/{cls.TOTAL_STEPS}] Executing MCX Commodity Protection Engine (Crude & NatGas)...")
        run_subprocess("mcx_commodity_engine.py", "MCX Commodity Protection Engine")

        # 8. ML Dynamic Target & Stop-Loss Optimizer
        print(f"\n[8/{cls.TOTAL_STEPS}] Executing ML Dynamic Target & Stop-Loss Optimizer...")
        try:
            from ml_target_sl_optimizer import MLTargetSLOptimizer
            run_imported("ML Target & SL Optimizer", MLTargetSLOptimizer.export_ml_optimizer_json)
        except Exception as e:
            failures.append(f"ML Target Optimizer (import failed: {e})")
            print(f"[FAIL] ML Target Optimizer step: {e}")

        # 9. Portfolio Risk-Parity & Auto-Rebalancing Screener
        print(f"\n[9/{cls.TOTAL_STEPS}] Executing Portfolio Risk-Parity & Auto-Rebalancing Screener...")
        try:
            from portfolio_rebalancer import PortfolioRebalancerEngine
            run_imported("Portfolio Risk-Parity Rebalancer", PortfolioRebalancerEngine.export_portfolio_json)
        except Exception as e:
            failures.append(f"Portfolio Rebalancer (import failed: {e})")
            print(f"[FAIL] Portfolio Rebalancer step: {e}")

        # 10. Morning Pre-Market & 15m ORB High-Conviction Momentum Validator
        print(f"\n[10/{cls.TOTAL_STEPS}] Executing Morning Momentum Validation & Signal Dispatcher...")
        try:
            from morning_momentum_validator import MorningMomentumValidatorEngine
            run_imported("Morning Momentum Validator", MorningMomentumValidatorEngine.export_and_broadcast_morning_signals)
        except Exception as e:
            failures.append(f"Morning Momentum Validator (import failed: {e})")
            print(f"[FAIL] Morning Momentum Validator step: {e}")

        # 11. MTF SMC Market Structure & Order Block Radar Engine
        print(f"\n[11/{cls.TOTAL_STEPS}] Executing MTF SMC Market Structure & Order Block Radar...")
        try:
            from smc_liquidity_sweep_engine import SMCLiquiditySweepEngine
            run_imported("MTF SMC Market Structure Radar", SMCLiquiditySweepEngine.export_smc_json)
        except Exception as e:
            failures.append(f"MTF SMC Market Structure (import failed: {e})")
            print(f"[FAIL] MTF SMC Market Structure step: {e}")

        # ---------------- Honest pipeline summary ----------------
        print("\n==========================================================================")
        if failures:
            print(f"  [WARNING] Pipeline finished with {len(failures)}/{cls.TOTAL_STEPS} FAILED steps:")
            for f_name in failures:
                print(f"    - {f_name}")
            print("  Dashboard data is INCOMPLETE or STALE for the affected tabs.")
            print("  Check the Actions log above for each [FAIL] line to diagnose.")
        else:
            print(f"  [SUCCESS] All {cls.TOTAL_STEPS} Market Mentor AI V8.0 steps refreshed in 1 pass!")
        print("==========================================================================")

        # Single Git Push (Optional / Enabled in Automated Schedulers)
        if auto_git_push:
            try:
                print("\n[SYNC] Syncing updated data to GitHub & Vercel Dashboard in 1 commit...")
                commit_msg = "Master Unified Pipeline Auto-Update [skip ci]"
                if failures:
                    commit_msg = f"Master Unified Pipeline Auto-Update ({len(failures)} steps failed) [skip ci]"
                subprocess.run(["git", "add", "data/*.json"], check=False)
                subprocess.run(["git", "commit", "-m", commit_msg], check=False)
                subprocess.run(["git", "push"], check=False)
                print("[SYNC] GitHub & Vercel Dashboard synced!")
            except Exception as e:
                print(f"[WARN] Git push skipped: {e}")

        return failures

def main():
    auto_push = "--push" in sys.argv
    failures = MasterDataFetcher.run_master_pipeline(auto_git_push=auto_push)
    if failures:
        # Non-zero exit -> GitHub Actions marks this run RED so stale/incomplete
        # data is visible instead of silently shipping as "fresh".
        print(f"\n[EXIT 1] {len(failures)} pipeline step(s) failed — marking this run as failed.")
        sys.exit(1)
    print("\n[EXIT 0] All pipeline steps completed successfully.")

if __name__ == '__main__':
    main()
