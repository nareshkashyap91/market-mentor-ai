import re
import json
import math
import requests
from datetime import datetime, timezone, timedelta

class GEXEngine:
    """Real Gamma Exposure (GEX) Analytics Engine for NIFTY.

    Data source: Groww's server-rendered NIFTY option chain page
    (https://groww.in/options/nifty). The full strike-wise chain — including
    REAL open interest, real greeks (gamma, IV, delta) and the live spot — is
    embedded in the page's __NEXT_DATA__ JSON, so plain `requests` can read it
    (no JavaScript, no login). This works from IPs where nseindia.com is
    blocked, which makes it pipeline-safe for GitHub Actions runners.

    GEX math (per strike, documented so the numbers are auditable):
        call_gex_rupees = gamma_ce * oi_ce * lot_size * spot^2 / 100
        put_gex_rupees  = gamma_pe * oi_pe * lot_size * spot^2 / 100
        net_gex_strike  = call_gex - put_gex            (puts count negative)
        NET GEX (₹ Cr)  = sum(net_gex_strike) / 1e7

    The /100 scaling expresses the exposure per 1% spot move (the standard
    dollar-gamma convention). Calls contribute positive dealer gamma, puts
    negative; a POSITIVE net GEX regime suppresses volatility (mean reversion /
    pinning), a NEGATIVE regime amplifies it (trending / volatile moves).

    Provenance contract: live computation is only claimed when the real chain
    was fetched; otherwise the payload falls back to clearly-flagged
    placeholders. The `pinning_probability` is always a disclosed heuristic
    (derived from live IV / GEX / days-to-expiry — never a market-sourced
    probability) and is listed in `modeled_components`.
    """

    GROWW_URL = "https://groww.in/options/nifty"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    IST_TZ = timezone(timedelta(hours=5, minutes=30))

    # Flagged placeholder values (used only when the real chain is unreachable)
    PLACEHOLDER = {
        "is_simulated": True,
        "data_source": "ANALYTICAL_MODEL_PLACEHOLDER (Groww chain unreachable — values are illustrative, not live dealer positioning)",
    }

    @classmethod
    def fetch_groww_nifty_chain(cls):
        """Fetches the real NIFTY option chain (nearest expiry) from Groww.

        Returns dict {contracts, lot_size, current_expiry, expiry_dates, spot}
        or None on failure. Contracts carry strikePrice (paise), ce/pe with
        liveData (oi, ltp) and greeks (gamma, iv, delta, theta, pop).
        """
        try:
            resp = requests.get(cls.GROWW_URL, headers=cls.HEADERS, timeout=20)
            if resp.status_code != 200:
                print(f"[INFO] GEX: Groww chain page unavailable (HTTP {resp.status_code})")
                return None
            text = resp.text

            m = re.search(r'<script id="__NEXT_DATA__"[^>]*>', text)
            if not m:
                print("[INFO] GEX: Groww page has no __NEXT_DATA__ block (layout change?)")
                return None
            start = m.end()
            end = text.find("</script>", start)
            data = json.loads(text[start:end])

            pp = data.get("props", {}).get("pageProps", {})
            if pp.get("ssrError"):
                print(f"[INFO] GEX: Groww SSR error: {str(pp['ssrError'])[:120]}")
                return None
            d = pp.get("data", {})
            oc = d.get("optionChain", {})
            contracts = oc.get("optionContracts", [])
            agg = oc.get("aggregatedDetails", {}) or {}
            if not contracts:
                print("[INFO] GEX: Groww chain returned no contracts")
                return None

            lot_size = agg.get("lotSize") or 65
            current_expiry = agg.get("currentExpiry")
            expiry_dates = agg.get("expiryDates", [])

            live = (d.get("company", {}) or {}).get("liveData", {}) or {}
            spot = live.get("ltp") or live.get("close")

            # Strikes come in paise (2295000 == 22950.00); normalize to rupees.
            norm = []
            for c in contracts:
                strike = (c.get("strikePrice") or 0) / 100.0
                ce, pe = c.get("ce") or {}, c.get("pe") or {}
                ce_ld, pe_ld = ce.get("liveData") or {}, pe.get("liveData") or {}
                ce_g, pe_g = ce.get("greeks") or {}, pe.get("greeks") or {}
                norm.append({
                    "strike": strike,
                    "ce_oi": ce_ld.get("oi") or 0,
                    "ce_ltp": ce_ld.get("ltp"),
                    "ce_gamma": ce_g.get("gamma"),
                    "ce_iv": ce_g.get("iv"),
                    "pe_oi": pe_ld.get("oi") or 0,
                    "pe_ltp": pe_ld.get("ltp"),
                    "pe_gamma": pe_g.get("gamma"),
                    "pe_iv": pe_g.get("iv"),
                })

            if spot is None:
                # Last-resort spot estimate: strike with the deepest combined OI.
                best = max(norm, key=lambda r: (r["ce_oi"] or 0) + (r["pe_oi"] or 0))
                spot = best["strike"]
                print("[WARN] GEX: spot unavailable from Groww — approximated by max-OI strike")

            return {
                "contracts": norm,
                "lot_size": lot_size,
                "current_expiry": current_expiry,
                "expiry_dates": expiry_dates,
                "spot": float(spot),
            }
        except Exception as e:
            print(f"[INFO] GEX: Groww chain fetch failed: {e}")
            return None

    @staticmethod
    def _dte(expiry_str):
        """Days to expiry (calendar days) from a 'YYYY-MM-DD' string."""
        if not expiry_str:
            return None
        try:
            exp = datetime.strptime(expiry_str, "%Y-%m-%d").date()
            return (exp - datetime.now(GEXEngine.IST_TZ).date()).days
        except ValueError:
            return None

    @classmethod
    def compute_gex_metrics(cls, chain):
        """Pure computation of GEX analytics from the fetched chain.

        Returns a payload dict for the dashboard, or raises ValueError when
        the chain has no usable gamma data.
        """
        contracts = chain["contracts"]
        lot = chain["lot_size"]
        spot = chain["spot"]
        expiry = chain.get("current_expiry")
        dte = cls._dte(expiry)

        # If Groww ever omits greeks, approximate gamma via Black-Scholes from
        # IV so the engine degrades gracefully (flagged as modeled below).
        missing_gamma = [c for c in contracts if c["ce_gamma"] is None and c["pe_gamma"] is None]
        gamma_was_modeled = bool(missing_gamma)

        def bs_gamma(spot, strike, iv_pct, dte_days, is_call):
            """Black-Scholes gamma approximation (per unit)."""
            if not iv_pct or iv_pct <= 0 or dte_days is None or dte_days < 0:
                return None
            T = max(dte_days, 0.5) / 365.0
            sigma = iv_pct / 100.0
            if sigma <= 0 or spot <= 0 or strike <= 0:
                return None
            d1 = (math.log(spot / strike) + 0.5 * sigma * sigma * T) / (sigma * math.sqrt(T))
            return math.exp(-0.5 * d1 * d1) / (spot * sigma * math.sqrt(T) * math.sqrt(2 * math.pi))

        strike_rows = []
        total_call_cr = 0.0
        total_put_cr = 0.0
        total_ce_oi = 0
        total_pe_oi = 0
        for c in contracts:
            strike = c["strike"]
            g_ce = c["ce_gamma"]
            if g_ce is None and c["ce_iv"] is not None and dte is not None:
                g_ce = bs_gamma(spot, strike, c["ce_iv"], dte, True)
            g_pe = c["pe_gamma"]
            if g_pe is None and c["pe_iv"] is not None and dte is not None:
                g_pe = bs_gamma(spot, strike, c["pe_iv"], dte, False)
            g_ce = g_ce or 0.0
            g_pe = g_pe or 0.0

            call_cr = g_ce * (c["ce_oi"] or 0) * lot * spot * spot / 100.0 / 1e7
            put_cr = g_pe * (c["pe_oi"] or 0) * lot * spot * spot / 100.0 / 1e7

            total_call_cr += call_cr
            total_put_cr += put_cr
            total_ce_oi += c["ce_oi"] or 0
            total_pe_oi += c["pe_oi"] or 0
            strike_rows.append({
                "strike": strike,
                "net_gex_cr": call_cr - put_cr,
                "abs_gex_cr": abs(call_cr - put_cr),
            })

        net_gex_cr = total_call_cr - total_put_cr

        if not strike_rows or (total_call_cr == 0 and total_put_cr == 0):
            raise ValueError("no usable gamma/OI data in chain")

        # Zero-gamma flip level: cumulative net GEX (low strike -> high) crossing 0.
        strike_rows.sort(key=lambda r: r["strike"])
        cum = 0.0
        flip_level = None
        prev = None
        for row in strike_rows:
            before = cum
            cum += row["net_gex_cr"]
            if prev is not None and before != 0 and (before < 0) != (cum < 0):
                flip_level = round((prev["strike"] + row["strike"]) / 2.0, 1)
            prev = row
        if flip_level is None and cum < 0:
            # Whole chain negative — flip sits above the top strike.
            flip_level = None  # reported as N/A, never fabricated

        # Pinning target: strike with the largest absolute GEX concentration.
        pin_row = max(strike_rows, key=lambda r: r["abs_gex_cr"])
        pin_strike = pin_row["strike"]
        pin_side = "CALL" if pin_row["net_gex_cr"] >= 0 else "PUT"

        # ATM IV (nearest strike to spot, averaged across sides) for expected move.
        atm = min(strike_rows, key=lambda r: abs(r["strike"] - spot))["strike"]
        atm_rows = [c for c in contracts if c["strike"] == atm]
        ivs = []
        if atm_rows:
            a = atm_rows[0]
            for iv in (a["ce_iv"], a["pe_iv"]):
                if iv and iv > 0:
                    ivs.append(iv)
        atm_iv = round(sum(ivs) / len(ivs), 2) if ivs else None

        # Expected move till expiry (1 sigma, in points) from ATM IV.
        expected_move = None
        if atm_iv and dte is not None:
            expected_move = round(spot * (atm_iv / 100.0) * math.sqrt(max(dte, 0.5) / 365.0), 1)

        # Regime classification
        if net_gex_cr >= 0:
            regime = "🟢 POSITIVE GAMMA (VOLATILITY DAMPENED / STABLE)"
        else:
            regime = "🔴 NEGATIVE GAMMA (VOLATILITY SPIKE RISK)"
        if flip_level is not None:
            regime += f" | FLIP ₹{flip_level:,.0f}"

        # Pinning probability — DISCLOSED HEURISTIC (not market-sourced):
        # stronger when expiry is near and spot is close to the max-GEX strike
        # relative to the IV-implied expected move.
        pin_prob_str = "N/A"
        if expected_move and expected_move > 0:
            distance = abs(spot - pin_strike)
            proximity = max(0.0, 1.0 - distance / expected_move)
            dte_factor = 1.0 / (1.0 + 0.35 * max((dte or 1) - 1, 0))
            magnitude = min(1.0, pin_row["abs_gex_cr"] / max(abs(net_gex_cr), 1.0))
            prob = 45 + 40 * proximity * dte_factor * (0.6 + 0.4 * magnitude)
            prob = max(5.0, min(88.0, prob))
            pin_prob_str = (f"{prob:.0f}% (heuristic: spot ₹{spot:,.0f} vs pin ₹{pin_strike:,.0f}, "
                            f"{dte}d to expiry, exp. move ±₹{expected_move:,.0f})")

        pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi else None

        payload = {
            "timestamp": datetime.now(cls.IST_TZ).strftime("%d-%b-%Y %I:%M %p"),
            "net_gex_crores": round(net_gex_cr, 1),
            "total_call_gex_crores": round(total_call_cr, 1),
            "total_put_gex_crores": round(total_put_cr, 1),
            "gex_regime": regime,
            "zero_gamma_flip_level": flip_level,
            "max_gex_strike": pin_strike,
            "max_gex_strike_side": pin_side,
            "pinning_probability": pin_prob_str,
            "spot": spot,
            "expiry_date": expiry,
            "days_to_expiry": dte,
            "atm_iv": atm_iv,
            "expected_move_till_expiry": expected_move,
            "total_call_oi": total_ce_oi,
            "total_put_oi": total_pe_oi,
            "pcr": pcr,
            "is_simulated": False,
            "simulated_components": [],
            "modeled_components": (["pinning_probability (heuristic from live IV/GEX/DTE — not market-sourced)"] +
                                   (["per-strike gamma (Black-Scholes approximation — Groww greeks missing on some strikes)"]
                                    if gamma_was_modeled else [])),
            "data_source": f"GROWW_LIVE (server-rendered NIFTY chain, nearest expiry {expiry}, lot {lot})",
        }
        return payload

    @classmethod
    def get_gex_analytics(cls, breadth_bullish=None):
        """Full GEX analytics with honest fallback to flagged placeholders."""
        chain = cls.fetch_groww_nifty_chain()
        if chain is not None:
            try:
                payload = cls.compute_gex_metrics(chain)
                print(f"[INFO] GEX: REAL gamma exposure computed — net ₹{payload['net_gex_crores']:,.0f} Cr, "
                      f"pin ₹{payload['max_gex_strike']:,.0f}, expiry {payload['expiry_date']}")
                return payload
            except ValueError as e:
                print(f"[INFO] GEX: chain fetched but not usable ({e}) — falling back")

        # Fallback: clearly-flagged illustrative values (same as pre-upgrade block).
        bullish = True if breadth_bullish is None else breadth_bullish
        return {
            "timestamp": datetime.now(cls.IST_TZ).strftime("%d-%b-%Y %I:%M %p"),
            "net_gex_crores": +4250.0 if bullish else -1850.0,
            "gex_regime": ("🟢 POSITIVE GAMMA (VOLATILITY DAMPENED / STABLE)" if bullish
                           else "🔴 NEGATIVE GAMMA (VOLATILITY SPIKE RISK)"),
            "zero_gamma_flip_level": None,
            "max_gex_strike": None,
            "pinning_probability": "N/A (live chain unavailable)",
            "is_simulated": True,
            "simulated_components": ["gamma_exposure_analytics (Groww chain unreachable — illustrative values)"],
            "modeled_components": [],
            "data_source": cls.PLACEHOLDER["data_source"],
        }

# Helper function
def get_gex_analytics(breadth_bullish=None):
    return GEXEngine.get_gex_analytics(breadth_bullish)

if __name__ == "__main__":
    out = get_gex_analytics()
    print(json.dumps(out, indent=2, ensure_ascii=False))
