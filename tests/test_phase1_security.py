import os
import json
import tempfile
from datetime import datetime, time as dt_time
from zoneinfo import ZoneInfo
import pytest

from telegram_config import (
    is_market_open,
    is_post_market_momentum_window,
    send_deduplicated_telegram_alert,
    load_nse_holidays,
    send_admin_pipeline_alert,
    KOLKATA_TZ
)
from atomic_io import atomic_write_json, safe_read_json
import intraday_screener
import options_screener

def test_nse_holidays_loaded():
    holidays, comm_evening = load_nse_holidays()
    assert len(holidays) > 0
    assert "2026-01-26" in holidays  # Republic Day
    assert "2026-10-02" in holidays  # Gandhi Jayanti
    assert "2026-03-04" in comm_evening  # Holi evening commodity session

def test_is_market_open_equity_normal_hours():
    # Normal Tuesday at 10:30 AM IST (2026-10-13)
    dt_open = datetime(2026, 10, 13, 10, 30, tzinfo=KOLKATA_TZ)
    assert is_market_open("EQ", dt_open) is True

    # Before market open: 08:30 AM IST
    dt_early = datetime(2026, 10, 13, 8, 30, tzinfo=KOLKATA_TZ)
    assert is_market_open("EQ", dt_early) is False

    # After market close: 16:00 IST
    dt_late = datetime(2026, 10, 13, 16, 0, tzinfo=KOLKATA_TZ)
    assert is_market_open("EQ", dt_late) is False

def test_is_market_open_commodity_hours():
    # Normal Tuesday at 20:00 (8:00 PM) IST
    dt_night = datetime(2026, 10, 13, 20, 0, tzinfo=KOLKATA_TZ)
    assert is_market_open("EQ", dt_night) is False
    assert is_market_open("COMM", dt_night) is True

    # Past midnight / 23:45 IST
    dt_past_comm = datetime(2026, 10, 13, 23, 45, tzinfo=KOLKATA_TZ)
    assert is_market_open("COMM", dt_past_comm) is False

def test_is_market_open_commodity_evening_holiday():
    # Holi holiday (2026-03-04) - Equity closed all day, MCX open evening 17:00 - 23:30
    dt_morning_holi = datetime(2026, 3, 4, 11, 0, tzinfo=KOLKATA_TZ)
    assert is_market_open("EQ", dt_morning_holi) is False
    assert is_market_open("COMM", dt_morning_holi) is False

    dt_evening_holi = datetime(2026, 3, 4, 18, 0, tzinfo=KOLKATA_TZ)
    assert is_market_open("EQ", dt_evening_holi) is False
    assert is_market_open("COMM", dt_evening_holi) is True

def test_is_market_open_weekend():
    # Saturday at 11:00 AM IST (2026-10-17)
    dt_sat = datetime(2026, 10, 17, 11, 0, tzinfo=KOLKATA_TZ)
    assert is_market_open("EQ", dt_sat) is False
    assert is_market_open("COMM", dt_sat) is False

    # Sunday at 14:00 IST (2026-10-18)
    dt_sun = datetime(2026, 10, 18, 14, 0, tzinfo=KOLKATA_TZ)
    assert is_market_open("EQ", dt_sun) is False
    assert is_market_open("COMM", dt_sun) is False

def test_is_market_open_holiday():
    # Republic day: Monday 2026-01-26 at 11:00 AM IST
    dt_holiday = datetime(2026, 1, 26, 11, 0, tzinfo=KOLKATA_TZ)
    assert is_market_open("EQ", dt_holiday) is False

def test_post_market_momentum_window():
    # Normal Tuesday at 17:00 (5:00 PM) IST
    dt_5pm = datetime(2026, 10, 13, 17, 0, tzinfo=KOLKATA_TZ)
    assert is_post_market_momentum_window(dt_5pm) is True

    # Normal Tuesday at 15:00 (3:00 PM) IST -> False
    dt_3pm = datetime(2026, 10, 13, 15, 0, tzinfo=KOLKATA_TZ)
    assert is_post_market_momentum_window(dt_3pm) is False

    # Weekend at 17:00 IST -> False
    dt_sat_5pm = datetime(2026, 10, 17, 17, 0, tzinfo=KOLKATA_TZ)
    assert is_post_market_momentum_window(dt_sat_5pm) is False

def test_atomic_write_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        target_path = os.path.join(tmpdir, "data", "test.json")
        sample_data = {"test_key": "valid_value", "number": 42}
        
        written_path = atomic_write_json(target_path, sample_data)
        assert os.path.exists(written_path)
        assert not os.path.exists(f"{target_path}.tmp")

        loaded = safe_read_json(target_path)
        assert loaded == sample_data

def test_screeners_routed_with_eq_segment(monkeypatch):
    calls = []
    def mock_send(message, bot_token=None, chat_id=None, force=False, min_interval_seconds=600, segment="EQ", alert_type="AUTO"):
        msg = message
        calls.append({"segment": segment, "force": force})
        return True

    monkeypatch.setattr("telegram_config.send_deduplicated_telegram_alert", mock_send)
    monkeypatch.setattr("intraday_screener.send_deduplicated_telegram_alert", mock_send)
    monkeypatch.setattr("options_screener.send_deduplicated_telegram_alert", mock_send)

    intraday_screener.send_to_telegram("Test message")
    options_screener.send_to_telegram("Test options message")

    assert len(calls) == 2
    assert calls[0]["segment"] == "EQ"
    assert calls[1]["segment"] == "EQ"

def test_admin_pipeline_alert_bypasses_market_hours(monkeypatch):
    calls = []
    def mock_send(message, bot_token=None, chat_id=None, force=False, min_interval_seconds=600, segment="EQ", alert_type="AUTO"):
        msg = message
        calls.append({"segment": segment, "force": force, "msg": msg})
        return True

    monkeypatch.setattr("telegram_config.send_deduplicated_telegram_alert", mock_send)
    monkeypatch.setattr("telegram_config.get_telegram_credentials", lambda admin=False: ("mock_token", "mock_chat"))

    res = send_admin_pipeline_alert("Test Pipeline Alert", "Failure details", is_failure=True)
    assert res is True
    assert len(calls) == 1
    assert calls[0]["segment"] == "ADMIN"
    assert calls[0]["force"] is True
    assert "🚨" in calls[0]["msg"]
