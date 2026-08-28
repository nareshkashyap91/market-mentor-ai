import unittest
from momentum_intelligence_engine import (
    MomentumDataValidator,
    TrendEngine,
    MomentumRvolEngine,
    RelativeStrengthEngine,
    MomentumDualScorer
)

class TestNextDayMomentumPhase1(unittest.TestCase):

    def test_data_validation(self):
        """Verifies Data Validation Layer checks."""
        valid_data = {
            'Close': 420.0, 'Open': 415.0, 'High': 425.0, 'Low': 412.0, 'Volume': 5000000,
            'dma20': 400.0, 'dma50': 380.0, 'dma100': 350.0, 'dma200': 320.0,
            'ema9': 415.0, 'ema21': 405.0, 'ema50': 385.0, 'ema200': 325.0,
            'rsi': 65.0, 'atr': 12.0, 'adx': 28.0, 'rvol': 2.1
        }
        val_res = MomentumDataValidator.validate_stock_data(valid_data)
        self.assertTrue(val_res["is_valid"])
        self.assertEqual(val_res["status"], "PASSED")

        # Missing field test
        invalid_data = valid_data.copy()
        del invalid_data['rsi']
        val_res_invalid = MomentumDataValidator.validate_stock_data(invalid_data)
        self.assertFalse(val_res_invalid["is_valid"])
        self.assertEqual(val_res_invalid["status"], "DATA UNAVAILABLE")

    def test_trend_classification(self):
        """Verifies Trend Engine DMA alignment and classification."""
        res = TrendEngine.classify_trend(
            close=420.0, dma20=400.0, dma50=380.0, dma100=350.0, dma200=320.0,
            ema9=415.0, ema21=405.0, ema50=385.0, ema200=325.0
        )
        self.assertEqual(res["trend_classification"], "STRONG BULLISH TREND")
        self.assertTrue(res["dma_aligned"])
        self.assertTrue(res["above_all_dmas"])

    def test_momentum_and_rvol_classification(self):
        """Verifies Momentum & RVOL Engine multi-indicator classification."""
        res = MomentumRvolEngine.classify_momentum(rsi=65.0, adx=28.0, price_change_pct=2.5, rvol=2.1)
        self.assertEqual(res["momentum_classification"], "VERY STRONG")
        self.assertIn("Exceptional", res["rvol_label"])
        self.assertIn("Accumulation Proxy", res["pv_relationship"])

    def test_relative_strength(self):
        """Verifies Relative Strength calculation against NIFTY 50."""
        res = RelativeStrengthEngine.calculate_relative_strength(stock_return_1y=84.8, nifty_return_1y=15.2)
        self.assertEqual(res["rs_classification"], "VERY STRONG")
        self.assertTrue(res["outperforming_nifty"])

    def test_dual_scoring_engine(self):
        """Verifies Dual Scoring Engine (Momentum Score vs Trade Setup Score)."""
        trend = TrendEngine.classify_trend(420, 400, 380, 350, 320, 415, 405, 385, 325)
        mom = MomentumRvolEngine.classify_momentum(65, 28, 2.5, 2.1)
        rs = RelativeStrengthEngine.calculate_relative_strength(84.8, 15.2)

        scores = MomentumDualScorer.calculate_scores(trend, mom, rs, extension_penalty=15)
        self.assertTrue(scores["momentum_quality_score"] > scores["trade_setup_score"])
        self.assertEqual(scores["extension_penalty"], 15)

if __name__ == '__main__':
    unittest.main()
