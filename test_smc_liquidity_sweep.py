import unittest
from smc_liquidity_sweep_engine import SMCLiquiditySweepEngine, get_smc_liquidity_analysis

class TestSMCLiquiditySweepEngine(unittest.TestCase):

    def test_upper_liquidity_sweep(self):
        """Verifies Upper Liquidity Sweep detection (retail buy bait rejection)."""
        res = get_smc_liquidity_analysis(close=418.0, open_p=416.0, high=425.0, low=415.0, orb_high=420.0, orb_low=410.0)
        self.assertEqual(res["smc_status"], "SMC UPPER LIQUIDITY SWEEP DETECTED (RETAIL BUY BAIT)")
        self.assertFalse(res["is_valid_setup"])
        self.assertEqual(res["smc_signal"], "BEARISH REVERSAL")

    def test_institutional_order_block_breakout(self):
        """Verifies Institutional Order Block Genuine Breakout."""
        res = get_smc_liquidity_analysis(close=423.0, open_p=418.0, high=425.0, low=417.0, orb_high=420.0, orb_low=410.0, rvol=1.8)
        self.assertEqual(res["smc_status"], "INSTITUTIONAL ORDER BLOCK BREAKOUT (GENUINE EXPANSION)")
        self.assertTrue(res["is_valid_setup"])

if __name__ == '__main__':
    unittest.main()
