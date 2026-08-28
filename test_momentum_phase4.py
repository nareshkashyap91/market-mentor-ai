import unittest
from momentum_intelligence_engine import (
    MarketRegimeAdapter,
    SignalLifecycleManager,
    AIExplanationSynthesizer,
    process_nextday_stock_intelligence
)

class TestNextDayMomentumPhase4(unittest.TestCase):

    def test_market_regime_adapter(self):
        """Verifies Market Regime Adapter scores."""
        bullish = MarketRegimeAdapter.adapt_setup_for_regime({"regime": "🟢 BULLISH_TRENDING", "confidence_score": 80.0})
        self.assertEqual(bullish["market_alignment_score"], 10)

        bearish = MarketRegimeAdapter.adapt_setup_for_regime({"regime": "🔴 BEARISH_DOWNTREND", "confidence_score": 40.0})
        self.assertEqual(bearish["market_alignment_score"], 3)

    def test_signal_lifecycle_manager(self):
        """Verifies Signal Lifecycle status resolution."""
        invalidated = SignalLifecycleManager.resolve_status(is_no_trade=True, setup_score=85, extension_status="NORMAL")
        self.assertEqual(invalidated, "INVALIDATED")

        watchlist = SignalLifecycleManager.resolve_status(is_no_trade=False, setup_score=85, extension_status="HIGHLY EXTENDED")
        self.assertEqual(watchlist, "WATCHLIST")

        wait = SignalLifecycleManager.resolve_status(is_no_trade=False, setup_score=85, extension_status="NORMAL")
        self.assertEqual(wait, "WAIT")

    def test_master_pipeline_processor(self):
        """Verifies full master pipeline execution."""
        sample_stock = {
            'symbol': 'BHEL', 'Close': 420.0, 'Open': 415.0, 'High': 425.0, 'Low': 412.0, 'Volume': 5000000,
            'dma20': 400.0, 'dma50': 380.0, 'dma100': 350.0, 'dma200': 320.0,
            'ema9': 415.0, 'ema21': 405.0, 'ema50': 385.0, 'ema200': 325.0,
            'rsi': 65.0, 'atr': 10.0, 'adx': 28.0, 'rvol': 2.1, 'high_52w': 420.0, 'low_52w': 220.0,
            'vwap': 416.0, 'car_1y': 84.8
        }

        res = process_nextday_stock_intelligence(sample_stock)

        self.assertEqual(res["symbol"], "BHEL")
        self.assertTrue(res["momentum_quality_score"] >= 80.0)
        self.assertEqual(res["status"], "WAIT")
        self.assertIn("entry_plan", res)
        self.assertIn("risk_plan", res)
        self.assertIn("position_sizing", res)
        self.assertIn("scenarios", res)
        self.assertIn("ai_explanation", res)

if __name__ == '__main__':
    unittest.main()
