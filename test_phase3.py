import os
import sys
import unittest
from datetime import date

from expected_move import ExpectedMoveEngine, get_expected_move

class TestPhase3ExpectedMoveAndDTE(unittest.TestCase):

    def test_thursday_expiry_resolution(self):
        """Verifies next Thursday expiry resolution."""
        # Test Monday date (2026-08-10) -> Thursday (2026-08-13)
        monday = date(2026, 8, 10)
        thursday = ExpectedMoveEngine.get_next_expiry_date(monday)
        self.assertEqual(thursday, date(2026, 8, 13))

    def test_dte_calculation(self):
        """Verifies DTE calculation."""
        current = date(2026, 8, 10)
        expiry = date(2026, 8, 13)
        dte = ExpectedMoveEngine.calculate_dte(expiry, current)
        self.assertEqual(dte, 3.0)

    def test_expected_move_formula(self):
        """Verifies 1-Sigma and 2-Sigma Expected Move calculation."""
        spot = 24500.0
        iv = 0.15 # 15%
        dte = 7.0

        em = get_expected_move(spot, iv, dte)
        
        self.assertIn("em_1sigma_pts", em)
        self.assertIn("em_2sigma_pts", em)
        self.assertIn("range_1sigma", em)
        self.assertIn("range_2sigma", em)

        # 2-Sigma points should be exactly double 1-Sigma points
        self.assertAlmostEqual(em["em_2sigma_pts"], em["em_1sigma_pts"] * 2.0, places=2)
        
        # Lower 1-Sigma should be spot - em_1sigma_pts
        self.assertAlmostEqual(em["range_1sigma"][0], round(spot - em["em_1sigma_pts"], 2), places=2)
        self.assertAlmostEqual(em["range_1sigma"][1], round(spot + em["em_1sigma_pts"], 2), places=2)

if __name__ == '__main__':
    unittest.main()
