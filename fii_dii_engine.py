import os
import re
import requests
import html as html_lib
from datetime import datetime, timezone, timedelta

class FIIDIIEngine:
    """Institutional FII / DII Big Money Flow Analytics Engine.

    Real data sources, tried in order (all free):
      1. NSE official APIs (fiidiiTrade + participantOI) — the primary source,
         but NSE aggressively blocks many IPs (datacenter ranges included).
         Cash figures are published post-close (~7 PM IST), so during market
         hours the latest row is the PREVIOUS session's flow.
      2. Economic Times FII/DII pages (server-rendered HTML tables) — works
         from IPs that NSE blocks. Gives net cash flow (day / 7d / 30d) and
         FII index futures & options net positioning (₹ Cr).

    Provenance contract: every payload carries `is_simulated`, `data_source`
    and `simulated_components`. Live data is only claimed when a fetch actually
    succeeded, and the `as_of_date` of the underlying figures is always surfaced.
    """

    NSE_HOME_URL = "https://www.nseindia.com"
    NSE_FII_DII_URL = "https://www.nseindia.com/api/fiidiiTrade"
    NSE_PARTICIPANT_OI_URL = "https://www.nseindia.com/api/participantOI"
    ET_FII_DII_URL = "https://economictimes.indiatimes.com/markets/fii-dii-activity"
    ET_FII_FNO_URL = "https://economictimes.indiatimes.com/markets/fii-dii-activity/fii-fno"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }

    IST_TZ = timezone(timedelta(hours=5, minutes=30))

    # Fallback placeholder values — used ONLY when every real source fails.
    # These are illustrative numbers, never real institutional flow.
    FALLBACK_FII_CASH_NET = 1850.50
    FALLBACK_DII_CASH_NET = 1240.20

    # ------------------------------------------------------------------ #
    # Source 1: NSE official APIs (blocked on many IPs, tried first)     #
    # ------------------------------------------------------------------ #

    @classmethod
    def create_nse_session(cls):
        session = requests.Session()
        session.headers.update(cls.HEADERS)
        try:
            res = session.get(cls.NSE_HOME_URL, timeout=10)
            if res.status_code == 200:
                return session
        except Exception as e:
            print(f"[WARN] FII/DII: failed to initialize NSE session cookies: {e}")
        return session

    @staticmethod
    def _parse_cr(value):
        """NSE sends values like '1,332.12' (₹ Crores) as strings. Robustly -> float."""
        if value is None:
            return None
        try:
            cleaned = str(value).replace(",", "").strip()
            if not cleaned or cleaned == "-":
                return None
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_contracts(value):
        """participantOI sends contract counts like '72,415' as strings. -> int."""
        if value is None:
            return None
        try:
            cleaned = str(value).replace(",", "").strip()
            if not cleaned or cleaned == "-":
                return None
            return int(float(cleaned))
        except (ValueError, TypeError):
            return None

    @classmethod
    def _latest_row_by_date(cls, rows):
        def row_date(r):
            try:
                return datetime.strptime(r.get("date", ""), "%d-%b-%Y")
            except ValueError:
                return datetime.min
        return max(rows, key=row_date)

    @classmethod
    def fetch_nse_fii_dii_cash(cls, session):
        """NSE fiidiiTrade -> latest FII/DII cash-market net flows (₹ Cr), or None."""
        try:
            session.headers.update({
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Referer": "https://www.nseindia.com/reports/fii-dii",
                "X-Requested-With": "XMLHttpRequest"
            })
            resp = session.get(cls.NSE_FII_DII_URL, timeout=12)
            if resp.status_code != 200:
                print(f"[INFO] FII/DII: NSE fiidiiTrade unavailable (HTTP {resp.status_code})")
                return None
            rows = resp.json().get("data", [])
            if not rows:
                print("[INFO] FII/DII: NSE fiidiiTrade returned no data rows")
                return None
            latest = cls._latest_row_by_date(rows)
            fii_net = cls._parse_cr(latest.get("fiiNetValue"))
            dii_net = cls._parse_cr(latest.get("diiNetValue"))
            if fii_net is None and dii_net is None:
                print("[INFO] FII/DII: NSE fiidiiTrade latest row had no parseable net values")
                return None
            return {
                "source": "NSE_LIVE",
                "as_of_date": latest.get("date"),
                "fii_net_cr": fii_net if fii_net is not None else 0.0,
                "dii_net_cr": dii_net if dii_net is not None else 0.0,
                "fii_7d_cr": None, "dii_7d_cr": None,
                "fii_30d_cr": None, "dii_30d_cr": None,
            }
        except Exception as e:
            print(f"[INFO] FII/DII: NSE fiidiiTrade fetch failed: {e}")
            return None

    @classmethod
    def fetch_nse_participant_oi(cls, session):
        """NSE participantOI -> FII index futures/options OI positioning, or None."""
        try:
            session.headers.update({
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Referer": "https://www.nseindia.com/reports/fii-dii",
                "X-Requested-With": "XMLHttpRequest"
            })
            resp = session.get(cls.NSE_PARTICIPANT_OI_URL, timeout=12)
            if resp.status_code != 200:
                print(f"[INFO] FII/DII: NSE participantOI unavailable (HTTP {resp.status_code})")
                return None
            rows = resp.json().get("data", [])
            if not rows:
                return None
            latest = cls._latest_row_by_date(rows)
            fut_long = cls._parse_contracts(latest.get("Fii_Index_Fut_Long"))
            fut_short = cls._parse_contracts(latest.get("Fii_Index_Fut_Short"))
            opt_long = cls._parse_contracts(latest.get("Fii_Index_Opt_Long"))
            opt_short = cls._parse_contracts(latest.get("Fii_Index_Opt_Short"))
            result = {"fut_long": fut_long, "fut_short": fut_short, "fut_long_pct": None,
                      "opt_long": opt_long, "opt_short": opt_short, "opt_bias": None}
            if fut_long is not None and fut_short is not None and (fut_long + fut_short) > 0:
                result["fut_long_pct"] = round(fut_long * 100.0 / (fut_long + fut_short), 1)
            if opt_long is not None and opt_short is not None:
                if opt_long > opt_short:
                    result["opt_bias"] = f"NET LONG INDEX OPTIONS ({opt_long:,} vs {opt_short:,} contracts)"
                elif opt_short > opt_long:
                    result["opt_bias"] = f"NET SHORT INDEX OPTIONS ({opt_long:,} vs {opt_short:,} contracts)"
                else:
                    result["opt_bias"] = f"BALANCED INDEX OPTIONS ({opt_long:,} each side)"
            return result
        except Exception as e:
            print(f"[INFO] FII/DII: NSE participantOI fetch failed: {e}")
            return None

    # ------------------------------------------------------------------ #
    # Source 2: Economic Times HTML tables (works from NSE-blocked IPs)  #
    # ------------------------------------------------------------------ #

    @classmethod
    def _et_session(cls):
        session = requests.Session()
        session.headers.update({
            "User-Agent": cls.HEADERS["User-Agent"],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        return session

    @staticmethod
    def _et_normalize_date(raw):
        """'1st Oct 2026' -> '01-Oct-2026'. Returns None if unparseable."""
        if not raw:
            return None
        cleaned = re.sub(r"(\d{1,2})(st|nd|rd|th)", r"\1", raw.strip())
        for fmt in ("%d %b %Y", "%d %B %Y"):
            try:
                return datetime.strptime(cleaned, fmt).strftime("%d-%b-%Y")
            except ValueError:
                continue
        return None

    @classmethod
    def fetch_et_fii_dii(cls):
        """ET FII/DII overview page -> net cash flow for day / 7d / 30d (₹ Cr), or None."""
        try:
            session = cls._et_session()
            resp = session.get(cls.ET_FII_DII_URL, timeout=15)
            if resp.status_code != 200:
                print(f"[INFO] FII/DII: ET overview page unavailable (HTTP {resp.status_code})")
                return None
            t = html_lib.unescape(resp.text)

            m = re.search(r"As on ([^<]{5,40})<", t)
            as_of = cls._et_normalize_date(m.group(1)) if m else None

            def section_nets(segment):
                out = {}
                for label, key in (("FII Cash Activity", "fii"), ("DII Cash Activity", "dii")):
                    j = segment.find(label)
                    if j == -1:
                        out[key] = None
                        continue
                    window = segment[j: j + 3000]
                    nums = re.findall(r">(-?[\d,]+(?:\.\d+)?)<", window)
                    out[key] = cls._parse_cr(nums[0]) if nums else None
                return out

            # Page order: current-day table, then "For Last 7 days", then 30 days.
            split7 = t.find("For Last 7 days")
            split30 = t.find("For Last 30 days")
            day_seg = t[: split7] if split7 != -1 else t
            week_seg = t[split7: split30] if (split7 != -1 and split30 != -1) else ""
            month_seg = t[split30: split30 + 8000] if split30 != -1 else ""

            day = section_nets(day_seg)
            week = section_nets(week_seg)
            month = section_nets(month_seg)

            if day.get("fii") is None and day.get("dii") is None:
                print("[INFO] FII/DII: ET page parsed but no day figures found (layout change?)")
                return None
            return {
                "source": "ET_MARKETS",
                "as_of_date": as_of,
                "fii_net_cr": day.get("fii") if day.get("fii") is not None else 0.0,
                "dii_net_cr": day.get("dii") if day.get("dii") is not None else 0.0,
                "fii_7d_cr": week.get("fii"),
                "dii_7d_cr": week.get("dii"),
                "fii_30d_cr": month.get("fii"),
                "dii_30d_cr": month.get("dii"),
            }
        except Exception as e:
            print(f"[INFO] FII/DII: ET overview fetch failed: {e}")
            return None

    @classmethod
    def fetch_et_fii_fno(cls):
        """ET FII F&O page -> FII index futures / options net positioning (₹ Cr), or None."""
        try:
            session = cls._et_session()
            resp = session.get(cls.ET_FII_FNO_URL, timeout=15)
            if resp.status_code != 200:
                print(f"[INFO] FII/DII: ET F&O page unavailable (HTTP {resp.status_code})")
                return None
            t = html_lib.unescape(resp.text)
            m = re.search(r"As on ([^<]{5,40})<", t)
            as_of = cls._et_normalize_date(m.group(1)) if m else None

            def first_value(label):
                j = t.find(label)
                if j == -1:
                    return None
                nums = re.findall(r">(-?[\d,]+(?:\.\d+)?)<", t[j: j + 3000])
                return cls._parse_cr(nums[0]) if nums else None

            fut_net = first_value("FII-Index Future")
            opt_net = first_value("FII-Index Option")
            if fut_net is None and opt_net is None:
                print("[INFO] FII/DII: ET F&O page parsed but no positioning found (layout change?)")
                return None
            return {"as_of_date": as_of, "fut_net_cr": fut_net, "opt_net_cr": opt_net}
        except Exception as e:
            print(f"[INFO] FII/DII: ET F&O fetch failed: {e}")
            return None

    # ------------------------------------------------------------------ #
    # Unified flow payload                                               #
    # ------------------------------------------------------------------ #

    @classmethod
    def get_fii_dii_flow(cls):
        """Builds the institutional flow payload from the best available source.

        Source priority: NSE official APIs -> Economic Times tables -> clearly
        flagged simulated placeholders. NSE/ET publish post-close, so during
        market hours `as_of_date` is the previous session — always surfaced.
        """
        now_str = datetime.now(cls.IST_TZ).strftime("%d-%b-%Y %I:%M %p")
        today_str = datetime.now(cls.IST_TZ).strftime("%d-%b-%Y")

        # --- Cash flow: NSE first, then ET ---
        nse_session = cls.create_nse_session()
        cash = cls.fetch_nse_fii_dii_cash(nse_session)
        cash_source = "NSE_LIVE (fiidiiTrade)"
        if cash is None:
            cash = cls.fetch_et_fii_dii()
            cash_source = "ET_MARKETS (fii-dii-activity page)" if cash else None

        # --- F&O positioning: NSE participantOI first, then ET ---
        poi = cls.fetch_nse_participant_oi(nse_session)
        fno = None
        fno_source = "NSE_LIVE (participantOI)"
        if poi is None or poi.get("fut_long_pct") is None:
            fno = cls.fetch_et_fii_fno()
            if fno is not None and (fno.get("fut_net_cr") is not None or fno.get("opt_net_cr") is not None):
                fno_source = "ET_MARKETS (fii-fno page)"
            elif poi is not None:
                fno_source = "NSE_LIVE (participantOI)"
            else:
                fno_source = None
        if poi is None and fno is None:
            fno_source = None

        simulated_components = []   # only entries where FABRICATED placeholder values ship
        unavailable_components = []  # metrics honestly omitted (no source reachable)

        if cash is not None:
            fii_cash_net = cash["fii_net_cr"]
            dii_cash_net = cash["dii_net_cr"]
            as_of_date = cash.get("as_of_date") or today_str
            if cash.get("fii_7d_cr") is not None:
                fii_7d, dii_7d = cash.get("fii_7d_cr"), cash.get("dii_7d_cr")
                fii_30d, dii_30d = cash.get("fii_30d_cr"), cash.get("dii_30d_cr")
            else:
                fii_7d = dii_7d = fii_30d = dii_30d = None
        else:
            fii_cash_net = cls.FALLBACK_FII_CASH_NET
            dii_cash_net = cls.FALLBACK_DII_CASH_NET
            as_of_date = today_str
            fii_7d = dii_7d = fii_30d = dii_30d = None
            simulated_components.append("fii_dii_cash_flow (NSE & ET both unreachable — placeholder ₹ Cr values)")

        # Futures long ratio: only real when NSE participantOI worked.
        if poi is not None and poi.get("fut_long_pct") is not None:
            fii_fut_ratio = poi["fut_long_pct"]
        else:
            fii_fut_ratio = None
            unavailable_components.append("fii_futures_long_ratio (no source reachable — omitted, not fabricated)")

        # Options bias: NSE contracts if available, else derived from ET net value.
        if poi is not None and poi.get("opt_bias"):
            fii_opt_bias = poi["opt_bias"]
        elif fno is not None and fno.get("opt_net_cr") is not None:
            v = fno["opt_net_cr"]
            fii_opt_bias = (f"NET LONG INDEX OPTIONS (+₹{v:,.0f} Cr premium)"
                            if v >= 0 else f"NET SHORT INDEX OPTIONS (-₹{abs(v):,.0f} Cr premium)")
        else:
            fii_opt_bias = "UNAVAILABLE (no live FII options positioning feed)"
            unavailable_components.append("fii_options_bias (no source reachable)")

        total_net = fii_cash_net + dii_cash_net

        # Sentiment scale (graded on REAL ₹ Cr magnitudes when live).
        # Labels carry the real story when flows diverge (e.g. heavy FII selling
        # absorbed by DII buying is NOT plain "bullish").
        if (fii_cash_net > 1000 and dii_cash_net > 500) or total_net >= 2000:
            sentiment = "EXTREMELY BULLISH (INSTITUTIONAL ACCUMULATION)"
            score = 92
        elif total_net >= 500:
            sentiment = "BULLISH (DII ABSORPTION OF FII SELLING)" if (fii_cash_net < 0 and dii_cash_net > 0) else "BULLISH"
            score = 75
        elif total_net > -500:
            sentiment = "NEUTRAL / MIXED"
            score = 50
        elif (fii_cash_net < -1000 and dii_cash_net < -500) or total_net <= -2000:
            sentiment = "EXTREMELY BEARISH (INSTITUTIONAL DISTRIBUTION)"
            score = 15
        else:
            sentiment = "BEARISH"
            score = 35

        # Honest dating: if the flow data is from a previous session (normal
        # during market hours — published post-close), say so explicitly.
        as_of_note = f" (as of {as_of_date})" if as_of_date != today_str else ""
        if as_of_note:
            print(f"[INFO] FII/DII flows are from the previous session ({as_of_date}) — published post-close")

        def fmt_cr(v):
            return f"{'-' if v < 0 else '+'}₹{abs(v):,.0f} Cr"

        payload = {
            "timestamp": now_str,
            "as_of_date": as_of_date,
            "fii_cash_net_cr": round(fii_cash_net, 2),
            "dii_cash_net_cr": round(dii_cash_net, 2),
            "total_net_cr": round(total_net, 2),
            "fii_futures_long_ratio": fii_fut_ratio,
            "fii_options_bias": fii_opt_bias,
            "institutional_sentiment": sentiment,
            "institutional_score": score,
            "formatted_summary": (f"FII: {fmt_cr(fii_cash_net)} | "
                                  f"DII: {fmt_cr(dii_cash_net)} | "
                                  f"Net: {fmt_cr(total_net)}{as_of_note}"),
            "is_simulated": bool(simulated_components),
            "simulated_components": simulated_components,
            "unavailable_components": unavailable_components,
            "data_source": (f"{cash_source} + {fno_source}" if (cash and not simulated_components)
                            else ("PARTIAL_FALLBACK (cash flow live from " + str(cash_source) + ")"
                                  if cash else "SIMULATED_PLACEHOLDER (all sources unreachable)")),
        }

        # Extra real detail when available (dashboard / Telegram context)
        if cash is not None:
            if fii_7d is not None or dii_7d is not None:
                payload["fii_cash_net_7d_cr"] = fii_7d
                payload["dii_cash_net_7d_cr"] = dii_7d
            if fii_30d is not None or dii_30d is not None:
                payload["fii_cash_net_30d_cr"] = fii_30d
                payload["dii_cash_net_30d_cr"] = dii_30d
        if poi is not None:
            payload["fii_fut_long_contracts"] = poi["fut_long"]
            payload["fii_fut_short_contracts"] = poi["fut_short"]
        if fno is not None:
            payload["fii_index_futures_net_cr"] = fno.get("fut_net_cr")
            payload["fii_index_options_net_cr"] = fno.get("opt_net_cr")
            payload["fno_as_of_date"] = fno.get("as_of_date")

        return payload

    @classmethod
    def validate_smart_money_breakout(cls, stock_symbol, is_long_signal=True):
        """Validates if a stock breakout signal is confirmed by FII/DII Big Money flow."""
        flow = cls.get_fii_dii_flow()
        total_net = flow["total_net_cr"]

        if is_long_signal and total_net > 0:
            status = "CONFIRMED BY FII/DII BUYING (SMART MONEY ACCUMULATION)"
            is_valid = True
        elif is_long_signal and total_net < -1500:
            status = "RETAIL TRAP RISK (HEAVY FII SELLING IN MARKET)"
            is_valid = False
        else:
            status = "NEUTRAL INSTITUTIONAL FLOW"
            is_valid = True

        return {
            "stock_symbol": stock_symbol,
            "is_valid": is_valid,
            "smart_money_status": status,
            "institutional_summary": flow["formatted_summary"],
            "as_of_date": flow.get("as_of_date"),
            "is_simulated": flow.get("is_simulated", True),
        }

# Helper function
def get_institutional_flow():
    return FIIDIIEngine.get_fii_dii_flow()
