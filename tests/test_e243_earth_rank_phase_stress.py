"""Deterministic E243 mathematical and synthetic controls."""
import unittest

import numpy as np

from research.e242_earth_sampling_aliasing import plane_detrended_std
from research.e243_earth_rank_phase_stress import (
    _compare, checkerboard_mode_2x2, rank_audit,
)


class E243Controls(unittest.TestCase):
    def test_exact_checkerboard_identity(self):
        rng = np.random.default_rng(243)
        for _ in range(200):
            z = rng.normal(size=(2, 2)) * 1000
            self.assertAlmostEqual(
                plane_detrended_std(z), checkerboard_mode_2x2(z), places=9
            )

    def test_large_planar_relief_is_annihilated(self):
        y, x = np.indices((2, 2))
        z = 100000 + 20000*x - 50000*y
        self.assertEqual(checkerboard_mode_2x2(z), 0)
        self.assertLess(plane_detrended_std(z), 1e-9)
        self.assertGreater(np.ptp(z), 50000)

    def test_checkerboard_mode_and_offset(self):
        z = np.array([[5., 1.], [2., 10.]])
        self.assertAlmostEqual(checkerboard_mode_2x2(z), 3.0)
        self.assertAlmostEqual(checkerboard_mode_2x2(z+1e6), 3.0)

    def test_exhaustive_independent_phase_accounting(self):
        y, x = np.indices((64, 80))
        a = 120*np.sin(x/9)*np.cos(y/13) + 2*x
        b = 40*np.sin(x/8)*np.cos(y/11) + 3*y
        result = rank_audit(a, b)
        self.assertEqual(set(result), {
            "plane_detrended_relief_sd_m", "raw_elevation_range_m"
        })
        for metric in result.values():
            for n in ("2", "4", "8", "16"):
                row = metric["grid_results"][n]
                self.assertEqual(sum(row["matched_phase_counts"].values()), 16)
                self.assertEqual(sum(row["independent_phase_counts"].values()), 256)
                self.assertIn(row["block_mean_rank"], ("same", "reversed", "tie"))

    def test_compare_tie_and_reverse(self):
        self.assertEqual(_compare(5, 3, 1), "same")
        self.assertEqual(_compare(3, 5, 1), "reversed")
        self.assertEqual(_compare(3, 3, 1), "tie")
        self.assertEqual(_compare(3, 5, -1), "same")
        with self.assertRaises(ValueError):
            _compare(float("nan"), 2, 1)

    def test_invalid_arrays_fail_closed(self):
        with self.assertRaises(ValueError):
            rank_audit(np.ones((8, 8)), np.ones((8, 8)))
        with self.assertRaises(ValueError):
            rank_audit(np.ones((64, 64)), np.ones((64, 64)))
        with self.assertRaises(ValueError):
            checkerboard_mode_2x2(np.ones((3, 3)))


if __name__ == "__main__":
    unittest.main()
