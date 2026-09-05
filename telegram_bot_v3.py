class TelegramBotV3Engine:
    """Telegram Intelligence Engine V3.0.
    Formats professional A+ / A trade alerts, mandatory WHY NOT TRADE explanations, and services expanded V3 command registry.
    """

    COMMANDS_V3 = {
        "/status": "Returns live Market Status, Regime & Data Health.",
        "/market": "Returns Nifty & BankNifty live market matrix.",
        "/signals": "Returns A/A+ active trade signals.",
        "/watchlist": "Returns Top 5 Next-Day Momentum Watchlist.",
        "/risk": "Returns Risk Cockpit, Daily PnL & Circuit Breaker status.",
        "/positions": "Returns Active Paper Positions & Open PnL.",
        "/performance": "Returns Win Rate, Profit Factor & Expectancy by Strategy.",
        "/regime": "Returns Centralized 10-Regime Analysis & ADX Intensity.",
        "/options": "Returns Options Delta-based Spreads & Expected Move.",
        "/mcx": "Returns live Crude Oil & NatGas Options Spreads.",
        "/morning": "Returns 9:30 AM Live Breakout Confirmation (Confirmed vs Rejected).",
        "/pause": "Pauses automated trading alerts for the session.",
        "/resume": "Resumes automated trading alerts for the session.",
        "/report": "Generates daily performance intelligence report.",
        "/help": "Displays all available Telegram V3 commands."
    }

    @classmethod
    def format_pro_trade_alert(cls, gate_res, explanation_res, sl=412.0, t1=432.0, t2=442.0, risk_pct=1.0, rr_ratio=2.2):
        """Formats V3 Professional Telegram A/A+ Trade Alert."""
        sym = gate_res["symbol"]
        direction = gate_res["direction"]
        score = gate_res["trade_score"]
        grade = gate_res["grade"]
        strat = gate_res["strategy"]
        confirmations = gate_res.get("confirmations", [])

        lines = [
            "━━━━━━━━━━━━━━━━━━",
            "🧠 *MARKET MENTOR AI*",
            "━━━━━━━━━━━━━━━━━━\n",
            f"🔥 *{grade} INTRADAY SETUP*\n",
            f"*SYMBOL:* `{sym}`",
            f"*DIRECTION:* `{direction}`",
            f"*SCORE:* `{score:.0f}/100` (`{grade}` Grade)\n",
            f"*REGIME:* `TRENDING BULLISH`",
            f"*STRATEGY:* `{strat}`\n",
            f"*ENTRY:* `₹{sl * 1.025:.2f}`",
            f"*SL:* `₹{sl:.2f}`",
            f"*TARGET 1:* `₹{t1:.2f}`",
            f"*TARGET 2:* `₹{t2:.2f}`",
            f"*R:R:* `1 : {rr_ratio:.1f}`",
            f"*RISK:* `{risk_pct:.1f}%` Capital Risk\n",
            "*CONFIRMATIONS:*"
        ]

        for c in confirmations:
            lines.append(f"✅ {c}")

        lines.append("\n⚠️ *RISKS:*")
        lines.append("• Nearby resistance zone")
        lines.append("• Overall market breadth volatility")

        lines.append(f"\n*INVALIDATION:* 5m candle close below ₹{sl:.2f}")
        lines.append(f"\n🤖 *AI DECISION:* 🟢 TRADE {direction.upper()}")
        lines.append("*Confidence:* `HIGH`")

        return "\n".join(lines)

    @classmethod
    def format_why_not_trade_alert(cls, symbol, reasons):
        """Formats V3 Mandatory WHY NOT TRADE Telegram Alert."""
        lines = [
            "⚪ *NO TRADE ALERT*",
            "━━━━━━━━━━━━━━━━━━",
            f"*SYMBOL:* `{symbol}`\n",
            "*REASON(S):*"
        ]
        for r in reasons:
            lines.append(f"❌ {r}")

        lines.append("\n🤖 *AI DECISION:* ⚪ NO TRADE")
        lines.append("💡 *Purpose:* Prevents overtrading and capital loss.")
        return "\n".join(lines)

# Helper function
def format_trade_alert_v3(gate_res, explanation_res):
    return TelegramBotV3Engine.format_pro_trade_alert(gate_res, explanation_res)
