import os
import sys
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

from data_quality import DataQualityEngine, get_data_quality_report, LIVE_DATA, MOCK_DATA
from market_regime import MarketRegimeEngine, get_market_regime_analysis

class TestPhase1DataQualityAndRegime(unittest.TestCase):

    def setUp(self):
        # Create a synthetic 15-minute DataFrame for testing
        dates = pd.date_range(end=datetime.now(), periods=50, freq='15min')
        np.random.seed(42)
        close_prices = 24000.0 + np.cumsum(np.random.randn(50) * 10)
        
        self.sample_df = pd.DataFrame({
            'Open': close_prices - 5,
            'High': close_prices + 15,
            'Low': close_prices - 15,
            'Close': close_prices,
            'Volume': np.random.randint(1000, 50000, size=50)
        }, index=dates)

    def test_live_vs_mock_tagging(self):
        """Verifies explicit LIVE_DATA vs MOCK_DATA tagging."""
        report_live, _ = DataQualityEngine.validate_dataframe(self.sample_df, is_mock=False)
        self.assertEqual(report_live['data_type'], LIVE_DATA)

        report_mock, _ = DataQualityEngine.validate_dataframe(self.sample_df, is_mock=True)
        self.assertEqual(report_mock['data_type'], MOCK_DATA)

    def test_data_validation_clean_data(self):
        """Verifies DataQualityEngine passes clean data."""
        report, clean_df = DataQualityEngine.validate_dataframe(self.sample_df, is_mock=True)
        self.assertTrue(isinstance(clean_df, pd.DataFrame))
        self.assertEqual(len(clean_df), len(self.sample_df))
        self.assertEqual(report['clean_rows'], 50)

    def test_data_validation_missing_columns(self):
        """Verifies DataQualityEngine catches missing columns."""
        bad_df = pd.DataFrame({'Close': [24000, 24100]})
        report, _ = DataQualityEngine.validate_dataframe(bad_df, is_mock=True)
        self.assertFalse(report['is_valid'])
        self.assertTrue(any('Missing required columns' in a for a in report['anomalies']))

    def test_adx_calculation(self):
        """Verifies ADX Trend Intensity calculation."""
        adx_val, intensity = MarketRegimeEngine.calculate_adx(self.sample_df)
        self.assertTrue(isinstance(adx_val, float))
        self.assertTrue(0.0 <= adx_val <= 100.0)
        self.assertIn(intensity, ["STRONG TREND", "MODERATE TREND", "WEAK / SIDEWAYS"])

    def test_market_regime_analysis(self):
        """Verifies Market Regime Engine outputs all required quantitative metrics."""
        regime = get_market_regime_analysis(self.sample_df, vix_val=14.2, pcr=1.1, is_mock=True)
        
        self.assertIn('regime', regime)
        self.assertIn('adx', regime)
        self.assertIn('trend_intensity', regime)
        self.assertIn('volatility_percentile', regime)
        self.assertIn('confidence_score', regime)
        self.assertEqual(regime['data_type'], MOCK_DATA)
        self.assertTrue(20.0 <= regime['confidence_score'] <= 100.0)

if __name__ == '__main__':
    unittest.main()
