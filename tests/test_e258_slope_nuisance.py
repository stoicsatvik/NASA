"""E258 slope-nuisance controls: not a planetary analogue benchmark."""
import unittest

import numpy as np

from research.e242_earth_sampling_aliasing import plane_detrended_std
from research.e247_common_lag_terrain import lag_contrast
from research.e258_slope_nuisance import audit, planar_tilt, SLOPES_M_PER_KM


class E258Controls(unittest.TestCase):
    def test_plane_tilt_is_not_roughness(self):
        flat = np.full((64, 64), 2000.0)
        tilted = planar_tilt(flat, 10.0, -20.0)
        self.assertAlmostEqual(plane_detrended_std(tilted), 0.0, places=8)
        self.assertGreater(lag_contrast(tilted)["combined_rms_m"], 0)
        self.assertAlmostEqual(float(tilted.mean()), 2000.0, places=8)

    def test_residual_is_invariant_for_nonlinear_terrain(self):
        y, x = np.indices((64, 80), dtype=float)
        terrain = 50 * np.sin(x / 7) + 20 * np.cos(y / 5) + 1.5 * x
        original = plane_detrended_std(terrain)
        for east, north in ((5, 0), (0, 40), (-20, 10)):
            self.assertAlmostEqual(
                plane_detrended_std(planar_tilt(terrain, east, north)),
                original, places=8,
            )

    def test_exhaustive_registration_counts(self):
        y, x = np.indices((64, 80), dtype=float)
        a = 30 * np.sin(x / 7) + 2 * y
        b = 80 * np.cos(y / 9) + 4 * x
        result = audit(a, b)
        self.assertEqual(result["scenario_count"], 2 * 4 * len(SLOPES_M_PER_KM))
        for scenario in result["synthetic_tilt_scenarios"]:
            for n in ("2", "4", "8", "16"):
                self.assertEqual(sum(scenario["grid_rank_vs_original_dense"][n].values()), 256)
            self.assertLess(scenario["detrended_relief_change_m"], 1e-8)

    def test_invalid_inputs_fail_closed(self):
        for bad in (np.ones((1, 5)), np.array([[1.0, np.nan], [2.0, 3.0]])):
            with self.assertRaises(ValueError):
                planar_tilt(bad, 1, 2)
        with self.assertRaises(ValueError):
            planar_tilt(np.ones((4, 4)), float("inf"), 0)
        with self.assertRaises(ValueError):
            audit(np.ones((8, 8)), np.ones((8, 8)))


if __name__ == "__main__":
    unittest.main()
