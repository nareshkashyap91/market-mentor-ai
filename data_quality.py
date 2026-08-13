import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta, timezone

# Explicit Data Source Constants as required by Master Specification Section 47
LIVE_DATA = "LIVE_DATA"
MOCK_DATA = "MOCK_DATA"

class DataQualityEngine:
    """Institutional Data Quality & Protection Engine.
    Enforces stale data protection, price anomaly filtering, and explicit source tagging.
    """

    @staticmethod
    def get_ist_now():
        ist_tz = timezone(timedelta(hours=5, minutes=30))
        return datetime.now(ist_tz)

    @staticmethod
    def is_market_open():
        now = DataQualityEngine.get_ist_now()
        if now.weekday() >= 5:  # Saturday or Sunday
            return False
        current_time = now.time()
        return time(9, 15) <= current_time <= time(15, 30)

    @staticmethod
    def check_stale_data(timestamp_or_df, max_stale_minutes=15):
        """Verifies if market data is fresh or stale."""
        now = DataQualityEngine.get_ist_now()
        
        last_dt = None
        if isinstance(timestamp_or_df, pd.DataFrame):
            if timestamp_or_df.empty:
                return True, 999.0, "Empty DataFrame provided"
            
            last_idx = timestamp_or_df.index[-1]
            if isinstance(last_idx, pd.Timestamp):
                last_dt = last_idx.to_pydatetime()
            else:
                try:
                    last_dt = pd.to_datetime(last_idx).to_pydatetime()
                except Exception:
                    last_dt = now
        elif isinstance(timestamp_or_df, (datetime, pd.Timestamp)):
            last_dt = timestamp_or_df
        else:
            return False, 0.0, "Fresh Data"

        # Ensure tz-awareness for Comparison
        ist_tz = timezone(timedelta(hours=5, minutes=30))
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=ist_tz)
        else:
            last_dt = last_dt.astimezone(ist_tz)

        # Calculate time difference
        diff = now - last_dt
        stale_minutes = diff.total_seconds() / 60.0

        is_market = DataQualityEngine.is_market_open()
        
        if is_market and stale_minutes > max_stale_minutes:
            return True, round(stale_minutes, 1), f"Data is stale ({stale_minutes:.1f}m old > {max_stale_minutes}m threshold)"
        elif not is_market:
            # Off market session - verify data is from latest trading session
            if (now.date() - last_dt.date()).days > 4:
                return True, round(stale_minutes, 1), "Data is older than 4 days"

        return False, round(max(0.0, stale_minutes), 1), "Fresh Data"

    @staticmethod
    def validate_dataframe(df, is_mock=False):
        """Sanitizes DataFrame, detects price anomalies, gaps, and attaches quality metadata."""
        data_tag = MOCK_DATA if is_mock else LIVE_DATA
        anomalies = []

        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return {
                "is_valid": False,
                "data_type": data_tag,
                "is_stale": True,
                "stale_minutes": 999.0,
                "anomalies": ["DataFrame is empty or None"],
                "clean_rows": 0,
                "status_summary": f"FAILED (Empty Data - {data_tag})"
            }, df

        # Copy to avoid mutating original
        clean_df = df.copy()

        # Handle MultiIndex columns if present
        if isinstance(clean_df.columns, pd.MultiIndex):
            clean_df.columns = clean_df.columns.get_level_values(0)

        # Ensure required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in clean_df.columns]
        if missing_cols:
            return {
                "is_valid": False,
                "data_type": data_tag,
                "is_stale": True,
                "stale_minutes": 999.0,
                "anomalies": [f"Missing required columns: {missing_cols}"],
                "clean_rows": 0,
                "status_summary": f"FAILED (Missing Columns - {data_tag})"
            }, df

        # Clean NaN/Null values
        initial_count = len(clean_df)
        clean_df = clean_df.dropna(subset=['Close'])
        dropped_count = initial_count - len(clean_df)
        if dropped_count > 0:
            anomalies.append(f"Dropped {dropped_count} rows with NaN values")

        # Price Anomaly Checks
        invalid_prices = clean_df[clean_df['Close'] <= 0]
        if len(invalid_prices) > 0:
            anomalies.append(f"Detected {len(invalid_prices)} rows with zero or negative Close price")
            clean_df = clean_df[clean_df['Close'] > 0]

        high_low_violations = clean_df[clean_df['High'] < clean_df['Low']]
        if len(high_low_violations) > 0:
            anomalies.append(f"Detected {len(high_low_violations)} rows where High < Low")
            clean_df = clean_df[clean_df['High'] >= clean_df['Low']]

        # Spike Detection (> 15% 1-bar movement)
        pct_change = clean_df['Close'].pct_change().abs()
        spikes = clean_df[pct_change > 0.15]
        if len(spikes) > 0:
            anomalies.append(f"Detected {len(spikes)} extreme single-bar price spikes (>15%)")

        # Stale Data Check
        is_stale, stale_mins, stale_reason = DataQualityEngine.check_stale_data(clean_df)
        if is_stale:
            anomalies.append(stale_reason)

        is_valid = len(clean_df) > 0 and not is_stale
        status = "PASSED" if is_valid else ("STALE_WARNING" if is_stale else "FAILED")

        report = {
            "is_valid": is_valid,
            "data_type": data_tag,
            "is_stale": is_stale,
            "stale_minutes": stale_mins,
            "anomalies": anomalies,
            "clean_rows": len(clean_df),
            "status_summary": f"{status} ({data_tag} | Freshness: {stale_mins}m)"
        }

        return report, clean_df

# Helper function
def get_data_quality_report(df, is_mock=False):
    report, _ = DataQualityEngine.validate_dataframe(df, is_mock=is_mock)
    return report
