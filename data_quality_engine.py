import time
from datetime import datetime, timezone, timedelta

class DataQualityEngine:
    """Central Data Quality Engine V3.0.
    Ensures every data point contains value, timestamp, source, freshness, status, and confidence.
    Statuses: LIVE, FRESH, STALE, MISSING, INVALID, CONFLICTING.
    """

    STATUS_LIVE = "LIVE"
    STATUS_FRESH = "FRESH"
    STATUS_STALE = "STALE"
    STATUS_MISSING = "MISSING"
    STATUS_INVALID = "INVALID"
    STATUS_CONFLICTING = "CONFLICTING"

    @classmethod
    def get_ist_now(cls):
        return datetime.now(timezone(timedelta(hours=5, minutes=30)))

    @classmethod
    def wrap_data_point(cls, value, source="YFinance", max_age_seconds=900, raw_timestamp=None):
        """Wraps any raw data point into a validated Data Quality Object."""
        now_dt = cls.get_ist_now()
        ts_str = now_dt.strftime("%Y-%m-%d %H:%M:%S IST")

        if value is None:
            return {
                "value": "DATA_UNAVAILABLE",
                "timestamp": ts_str,
                "source": source,
                "freshness_seconds": 99999,
                "status": cls.STATUS_MISSING,
                "confidence": 0.0,
                "is_reliable": False
            }

        freshness_seconds = 0
        if raw_timestamp:
            try:
                if isinstance(raw_timestamp, (int, float)):
                    freshness_seconds = int(time.time() - raw_timestamp)
                elif isinstance(raw_timestamp, datetime):
                    freshness_seconds = int((now_dt - raw_timestamp).total_seconds())
            except Exception:
                freshness_seconds = 0

        freshness_seconds = max(0, freshness_seconds)

        if freshness_seconds > max_age_seconds:
            status = cls.STATUS_STALE
            confidence = max(30.0, 100.0 - (freshness_seconds / 60.0))
            is_reliable = False
        elif freshness_seconds <= 60:
            status = cls.STATUS_LIVE
            confidence = 100.0
            is_reliable = True
        else:
            status = cls.STATUS_FRESH
            confidence = 90.0
            is_reliable = True

        return {
            "value": value,
            "timestamp": ts_str,
            "source": source,
            "freshness_seconds": freshness_seconds,
            "status": status,
            "confidence": round(confidence, 1),
            "is_reliable": is_reliable
        }

    @classmethod
    def validate_dataset(cls, data_dict):
        """Validates an entire dataset for trade execution readiness."""
        unreliable_keys = []
        overall_confidence = 100.0

        for key, item in data_dict.items():
            if isinstance(item, dict) and "is_reliable" in item:
                if not item["is_reliable"]:
                    unreliable_keys.append(key)
                overall_confidence = min(overall_confidence, item.get("confidence", 100.0))

        is_passed = len(unreliable_keys) == 0

        return {
            "is_trade_ready": is_passed,
            "overall_confidence": round(overall_confidence, 1),
            "unreliable_keys": unreliable_keys,
            "status": cls.STATUS_LIVE if is_passed else cls.STATUS_STALE
        }

# Helper function
def wrap_data(value, source="YFinance", max_age_seconds=900, raw_timestamp=None):
    return DataQualityEngine.wrap_data_point(value, source, max_age_seconds, raw_timestamp)
