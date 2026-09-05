import os
from chart_plotter_engine import ChartPlotterEngine
from telegram_bot_v3 import TelegramBotV3Engine

class TradeDecisionPipeline:
    """5-Stage Decision Pipeline:
    TradeDecision ➔ AI Radar ➔ Trade Card ➔ Chart ➔ Telegram
    """

    RADARS = ["MOMENTUM_RADAR", "ORB_RADAR", "VWAP_RADAR", "LIQUIDITY_RADAR", "OPTIONS_RADAR", "MCX_RADAR"]

    @classmethod
    def execute_pipeline(cls, symbol, direction, strategy_name, gate_res, explanation_res,
                         sl=412.0, t1=432.0, t2=442.0, bot_token=None, chat_id=None):
        """Executes the complete 5-stage pipeline."""
        
        # Stage 1: TradeDecision
        decision = gate_res.get("decision", "NO_TRADE")
        is_trade_allowed = gate_res.get("is_gate_passed", False)
        
        # Stage 2: AI Radar Assignment
        if "ORB" in strategy_name.upper():
            radar = "ORB_RADAR"
        elif "VWAP" in strategy_name.upper():
            radar = "VWAP_RADAR"
        elif "SWEEP" in strategy_name.upper() or "LIQUIDITY" in strategy_name.upper():
            radar = "LIQUIDITY_RADAR"
        elif "OPTIONS" in strategy_name.upper() or "SPREAD" in strategy_name.upper():
            radar = "OPTIONS_RADAR"
        elif "MCX" in strategy_name.upper() or "CRUDE" in strategy_name.upper():
            radar = "MCX_RADAR"
        else:
            radar = "MOMENTUM_RADAR"

        # Stage 3: Trade Card
        trade_card = {
            "symbol": symbol,
            "direction": direction,
            "decision": decision,
            "radar": radar,
            "grade": gate_res.get("grade", "A+"),
            "score": gate_res.get("trade_score", 91.0),
            "strategy": strategy_name,
            "entry": round(sl * 1.025, 2),
            "sl": sl,
            "target_1": t1,
            "target_2": t2,
            "risk_pct": 1.0,
            "rr_ratio": round((t1 - (sl * 1.025)) / max(0.1, ((sl * 1.025) - sl)), 1),
            "confirmations": gate_res.get("confirmations", ["15m Trend", "VWAP", "RVOL"]),
            "ai_rationale": explanation_res.get("why_this_stock", "High-probability setup.")
        }

        # Stage 4: Chart Generation
        chart_success, chart_path = ChartPlotterEngine.plot_stock_chart(symbol=symbol)

        # Stage 5: Telegram Dispatch
        telegram_status = "SKIPPED"
        if is_trade_allowed:
            card_text = TelegramBotV3Engine.format_pro_trade_alert(gate_res, explanation_res, sl=sl, t1=t1, t2=t2)
            if bot_token and chat_id and os.path.exists(chart_path):
                ChartPlotterEngine.send_chart_to_telegram(bot_token, chat_id, chart_path, caption=card_text)
                telegram_status = "SENT"
        else:
            reasons = gate_res.get("reasons", ["Trade gate criteria not satisfied."])
            card_text = TelegramBotV3Engine.format_why_not_trade_alert(symbol, reasons)
            telegram_status = "NO_TRADE_LOGGED"

        return {
            "stage_1_decision": decision,
            "stage_2_radar": radar,
            "stage_3_trade_card": trade_card,
            "stage_4_chart_path": chart_path,
            "stage_5_telegram_status": telegram_status,
            "is_trade_allowed": is_trade_allowed
        }

# Helper function
def run_trade_decision_pipeline(symbol, direction, strategy_name, gate_res, explanation_res, sl=412.0, t1=432.0, t2=442.0):
    return TradeDecisionPipeline.execute_pipeline(symbol, direction, strategy_name, gate_res, explanation_res, sl, t1, t2)
