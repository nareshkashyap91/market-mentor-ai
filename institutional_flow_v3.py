import requests

class InstitutionalFlowV3Engine:
    """Institutional Flow & Options Positioning Proxy Engine V3.0.
    Preserves FII Cash, DII Cash, Futures Long Ratio.
    Calculates INSTITUTIONAL_FLOW_SCORE and OPTIONS_POSITIONING_BIAS using probabilistic POSITIONING_PROXY terminology.
    """

    @classmethod
    def analyze_institutional_flow(cls, fii_cash_cr=1850.0, dii_cash_cr=1240.0, fii_futures_long_ratio=62.5, pcr=1.15):
        """Analyzes institutional money flow and returns POSITIONING_PROXY bias."""
        total_net_cr = fii_cash_cr + dii_cash_cr

        # Institutional Flow Score (0 to 100)
        base_score = 50.0
        if fii_cash_cr > 1000.0: base_score += 20.0
        elif fii_cash_cr < -1000.0: base_score -= 20.0

        if dii_cash_cr > 500.0: base_score += 10.0
        if fii_futures_long_ratio >= 60.0: base_score += 10.0

        inst_flow_score = round(max(0.0, min(100.0, base_score)), 1)

        # Options Positioning Bias Classification
        if pcr >= 1.2 and fii_cash_cr > 0:
            positioning_bias = "BULLISH"
            proxy_summary = "Institutional cash accumulation proxy aligned with bullish PCR (> 1.2)."
        elif pcr <= 0.8 and fii_cash_cr < 0:
            positioning_bias = "BEARISH"
            proxy_summary = "Institutional cash distribution proxy aligned with bearish PCR (< 0.8)."
        elif (fii_cash_cr > 0 and dii_cash_cr < 0) or (pcr < 0.9 and fii_cash_cr > 0):
            positioning_bias = "CONFLICTED"
            proxy_summary = "Divergence between FII cash flow and option positioning proxy."
        else:
            positioning_bias = "NEUTRAL"
            proxy_summary = "Balanced institutional positioning proxy."

        return {
            "fii_cash_net_cr": fii_cash_cr,
            "dii_cash_net_cr": dii_cash_cr,
            "total_net_cr": total_net_cr,
            "fii_futures_long_ratio": fii_futures_long_ratio,
            "pcr": pcr,
            "institutional_flow_score": inst_flow_score,
            "options_positioning_bias": positioning_bias,
            "positioning_proxy_summary": proxy_summary
        }

# Helper function
def get_institutional_flow_v3(fii_cash_cr=1850.0, dii_cash_cr=1240.0, fii_futures_long_ratio=62.5, pcr=1.15):
    return InstitutionalFlowV3Engine.analyze_institutional_flow(fii_cash_cr, dii_cash_cr, fii_futures_long_ratio, pcr)
