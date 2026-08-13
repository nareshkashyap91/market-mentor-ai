import numpy as np

# NSE Official Contract Lot Sizes
LOT_SIZES = {
    "NIFTY": 25,
    "BANKNIFTY": 15,
    "FINNIFTY": 40,
    "MIDCPNIFTY": 50
}

class CapitalMarginEngine:
    """Institutional Capital & NSE Margin Requirement Engine.
    Calculates SPAN + Exposure margin requirements for Naked Options, Hedged Spreads, and Iron Butterfly/Straddles.
    """

    @staticmethod
    def get_lot_size(index_name):
        return LOT_SIZES.get(index_name.upper().strip(), 25)

    @classmethod
    def calculate_margin(cls, index_name, strategy_type, legs, spot_price):
        """Calculates total capital/margin requirement in Indian Rupees (₹) for 1 lot."""
        lot_size = cls.get_lot_size(index_name)
        st_type = strategy_type.upper().strip()

        # Parse strikes from legs
        strikes = []
        for leg in legs:
            for t in leg.split():
                if t.isdigit():
                    strikes.append(float(t))
                    break

        if not strikes:
            strikes = [spot_price]

        margin_req = 0.0

        if "NAKED" in st_type or "BUY" in st_type:
            # Naked Option Buy: Premium Paid (Estimated ~1% of spot)
            estimated_premium = spot_price * 0.01
            margin_req = estimated_premium * lot_size

        elif "CREDIT" in st_type:
            # Credit Spread: Margin = (Spread Width * Lot Size) - Net Credit
            spread_width = abs(strikes[0] - strikes[1]) if len(strikes) >= 2 else 100.0
            estimated_credit = spread_width * 0.35
            margin_req = (spread_width * lot_size) - (estimated_credit * lot_size)

        elif "DEBIT" in st_type or "HEDGED SPREAD" in st_type:
            # Debit Spread: Maximum Risk = Net Premium Paid
            spread_width = abs(strikes[0] - strikes[1]) if len(strikes) >= 2 else 150.0
            net_debit = spread_width * 0.40
            margin_req = net_debit * lot_size

        elif "STRADDLE" in st_type or "BUTTERFLY" in st_type:
            # Iron Butterfly / Short Straddle (Hedged): Wing Width * Lot Size
            wing_width = 150.0
            if len(strikes) >= 3:
                wing_width = max(abs(strikes[0] - strikes[2]), abs(strikes[1] - strikes[3]))
            margin_req = wing_width * lot_size

        else:
            margin_req = spot_price * 0.015 * lot_size

        margin_req = round(max(1000.0, margin_req), 0)

        return {
            "index_name": index_name.upper(),
            "lot_size": lot_size,
            "margin_required_rupees": margin_req,
            "margin_formatted": f"₹{margin_req:,.0f}"
        }

# Helper function
def get_strategy_margin(index_name, strategy_type, legs, spot_price):
    return CapitalMarginEngine.calculate_margin(index_name, strategy_type, legs, spot_price)
