import os
import json
from datetime import datetime, timezone, timedelta

class MCXEventEngine:
    """MCX Event Protection Engine V3.0.
    Tracks high-impact commodity events (EIA Crude Inventory, OPEC meetings, Natural Gas Storage).
    Enforces PRE_EVENT_LOCKOUT_MINUTES and POST_EVENT_COOLDOWN_MINUTES guardrails.
    """

    PRE_EVENT_LOCKOUT_MINUTES = 30
    POST_EVENT_COOLDOWN_MINUTES = 15

    DEFAULT_EVENTS = [
        {
            "event_name": "US EIA Crude Oil Stocks Weekly Report",
            "asset": "CRUDEOIL",
            "weekday": 2,  # Wednesday (0=Mon, 2=Wed)
            "event_time": "20:00",
            "importance": "HIGH",
            "source": "US Energy Information Administration"
        },
        {
            "event_name": "US EIA Natural Gas Storage Report",
            "asset": "NATURALGAS",
            "weekday": 3,  # Thursday
            "event_time": "20:00",
            "importance": "HIGH",
            "source": "US Energy Information Administration"
        }
    ]

    @classmethod
    def get_ist_now(cls):
        return datetime.now(timezone(timedelta(hours=5, minutes=30)))

    @classmethod
    def check_event_risk(cls, asset="CRUDEOIL"):
        """Checks if asset is currently within Pre-Event Lockout or Post-Event Cooldown window."""
        now_dt = cls.get_ist_now()
        current_weekday = now_dt.weekday()
        current_time_str = now_dt.strftime("%H:%M")

        is_blocked = False
        active_event = None

        for ev in cls.DEFAULT_EVENTS:
            if ev["asset"] == asset and ev["weekday"] == current_weekday:
                ev_hour, ev_min = map(int, ev["event_time"].split(":"))
                ev_dt = now_dt.replace(hour=ev_hour, minute=ev_min, second=0, microsecond=0)

                lockout_start = ev_dt - timedelta(minutes=cls.PRE_EVENT_LOCKOUT_MINUTES)
                cooldown_end = ev_dt + timedelta(minutes=cls.POST_EVENT_COOLDOWN_MINUTES)

                if lockout_start <= now_dt <= cooldown_end:
                    is_blocked = True
                    active_event = ev
                    break

        if is_blocked and active_event:
            status = f"⚠️ EVENT RISK: {asset} — Scheduled High-Impact Event ({active_event['event_name']}). NEW TRADES BLOCKED."
            action = "NEW_TRADE_BLOCKED"
        else:
            status = f"🟢 NO EVENT RISK: {asset} trading normal."
            action = "TRADE_ALLOWED"

        return {
            "asset": asset,
            "is_event_risk_active": is_blocked,
            "new_trade_blocked": is_blocked,
            "event_status": status,
            "action": action,
            "active_event": active_event
        }

# Helper function
def check_mcx_event_risk(asset="CRUDEOIL"):
    return MCXEventEngine.check_event_risk(asset)
