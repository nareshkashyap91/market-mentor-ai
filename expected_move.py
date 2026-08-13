import math
from datetime import datetime, date, timedelta, timezone

class ExpectedMoveEngine:
    """Institutional Options Expected Move & DTE Calculator.
    Calculates 1-Sigma (68.3%) and 2-Sigma (95.4%) expected price movement ranges based on Implied Volatility.
    """

    @staticmethod
    def get_ist_today():
        ist_tz = timezone(timedelta(hours=5, minutes=30))
        return datetime.now(ist_tz).date()

    @classmethod
    def get_next_expiry_date(cls, current_date=None):
        """Resolves the next upcoming Thursday expiry date for Indian index options."""
        if current_date is None:
            current_date = cls.get_ist_today()

        # Thursday is weekday 3 (0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday)
        days_until_thursday = (3 - current_date.weekday()) % 7
        if days_until_thursday == 0:
            # Today is Thursday
            return current_date

        return current_date + timedelta(days=days_until_thursday)

    @classmethod
    def calculate_dte(cls, expiry_date=None, current_date=None):
        """Calculates Days To Expiration (DTE). Minimum 0.5 days on expiry day."""
        if current_date is None:
            current_date = cls.get_ist_today()
        if expiry_date is None:
            expiry_date = cls.get_next_expiry_date(current_date)

        days = (expiry_date - current_date).days
        return max(0.5, float(days))

    @classmethod
    def calculate_expected_move(cls, spot, iv, dte_days=None):
        """Calculates 1-Sigma (68.3%) and 2-Sigma (95.4%) Expected Move points and price boundaries."""
        if spot <= 0 or iv <= 0:
            return {
                "dte_days": 7.0,
                "em_1sigma_pts": 0.0,
                "em_2sigma_pts": 0.0,
                "range_1sigma": [spot, spot],
                "range_2sigma": [spot, spot],
                "em_pct": 0.0
            }

        if dte_days is None:
            dte_days = cls.calculate_dte()

        # Expected Move Formula: Spot * IV * sqrt(DTE / 365)
        em_1sigma = spot * iv * math.sqrt(dte_days / 365.0)
        em_2sigma = em_1sigma * 2.0

        upper_1s = round(spot + em_1sigma, 2)
        lower_1s = round(spot - em_1sigma, 2)
        upper_2s = round(spot + em_2sigma, 2)
        lower_2s = round(spot - em_2sigma, 2)

        em_pct = round((em_1sigma / spot) * 100.0, 2)

        return {
            "dte_days": round(dte_days, 1),
            "em_1sigma_pts": round(em_1sigma, 2),
            "em_2sigma_pts": round(em_2sigma, 2),
            "em_pct": em_pct,
            "range_1sigma": [lower_1s, upper_1s],
            "range_2sigma": [lower_2s, upper_2s],
            "summary_str": f"±{em_1sigma:.1f} pts (₹{lower_1s:.0f} - ₹{upper_1s:.0f})"
        }

# Helper function
def get_expected_move(spot, iv, dte_days=None):
    return ExpectedMoveEngine.calculate_expected_move(spot, iv, dte_days)
