import unittest
import pandas as pd
import numpy as np

from volume_profile_engine import VolumeProfileEngine, get_volume_profile

class TestVolumeProfileEngine(unittest.TestCase):

    def test_volume_profile_calculation(self):
        """Verifies Point of Control (POC), Value Area High (VAH), and Value Area Low (VAL)."""
        np.random.seed(42)
        dates = pd.date_range("2026-08-01", periods=30)
        prices = np.random.normal(loc=24200, scale=100, size=30)
        volumes = np.random.randint(100000, 500000, size=30)

        df = pd.DataFrame({
            'High': prices + 30,
            'Low': prices - 30,
            'Close': prices,
            'Volume': volumes
        }, index=dates)

        vp = VolumeProfileEngine.calculate_volume_profile(df)
        self.assertIn("poc", vp)
        self.assertIn("vah", vp)
        self.assertIn("val", vp)
        self.assertTrue(vp["vah"] >= vp["val"])
        self.assertTrue(vp["val"] <= vp["poc"] <= vp["vah"])

    def test_order_block_detection(self):
        """Verifies Demand and Supply Order Block detection."""
        dates = pd.date_range("2026-08-01", periods=10)
        df = pd.DataFrame({
            'High': [24100, 24150, 24200, 24250, 24300, 24350, 24400, 24450, 24500, 24550],
            'Low': [24000, 24050, 24100, 24150, 24200, 24250, 24300, 24350, 24400, 24450],
            'Close': [24050, 24100, 24150, 24200, 24250, 24300, 24350, 24400, 24450, 24500],
            'Volume': [100000] * 10
        }, index=dates)

        ob = VolumeProfileEngine.detect_order_blocks(df)
        self.assertEqual(ob["demand_zone_min"], 24000.0)
        self.assertEqual(ob["supply_zone_max"], 24550.0)

if __name__ == '__main__':
    unittest.main()
