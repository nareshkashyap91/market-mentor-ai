import unittest
import os
from chart_plotter_engine import ChartPlotterEngine, generate_and_send_chart

class TestChartPlotterEngine(unittest.TestCase):

    def test_plot_stock_chart(self):
        """Verifies HD Technical Chart PNG image generation."""
        res, path = ChartPlotterEngine.plot_stock_chart(symbol="NIFTY_TEST")
        self.assertTrue(res)
        self.assertTrue(os.path.exists(path))
        self.assertTrue(path.endswith(".png"))

    def test_generate_and_send_helper(self):
        """Verifies combined chart generator helper."""
        info = generate_and_send_chart(symbol="BHEL_TEST")
        self.assertEqual(info["status"], "SUCCESS")
        self.assertTrue(os.path.exists(info["image_path"]))

if __name__ == '__main__':
    unittest.main()
