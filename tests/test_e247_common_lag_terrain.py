"""E247 deterministic controls for fixed physical-lag contrast."""
import unittest
import numpy as np
from research.e247_common_lag_terrain import lag_contrast, audit


class E247Controls(unittest.TestCase):
    def test_flat_and_offset_invariant(self):
        z = np.full((2, 2), 1000.)
        self.assertEqual(lag_contrast(z)["combined_rms_m"], 0)
        self.assertEqual(lag_contrast(z + 1e6)["combined_rms_m"], 0)

    def test_planar_gradient_is_not_roughness(self):
        y, x = np.indices((2, 2))
        z = 1000 + 30*x + 40*y
        v = lag_contrast(z)
        self.assertAlmostEqual(v["east_west_rms_m"], 30)
        self.assertAlmostEqual(v["north_south_rms_m"], 40)
        self.assertAlmostEqual(v["combined_rms_m"], np.sqrt(1250))
        self.assertEqual(v["horizontal_pairs"], 2)
        self.assertEqual(v["vertical_pairs"], 2)

    def test_offset_and_sign_invariance(self):
        rng = np.random.default_rng(247)
        for n in (2, 4, 8, 16):
            z = rng.normal(size=(n, n)) * 200
            v = lag_contrast(z)
            self.assertAlmostEqual(v["combined_rms_m"], lag_contrast(-z+3000)["combined_rms_m"], places=9)
            self.assertEqual(v["horizontal_pairs"], n * (n-n//2))
            self.assertAlmostEqual(v["lag_fraction_x"], 0.5)

    def test_exact_independent_scenario_counts(self):
        y, x = np.indices((64, 80))
        a = 100*np.sin(x/8) + 2*y
        b = 50*np.cos(y/9) + 3*x
        results = audit(a, b)
        self.assertEqual(len(results), 3)
        for metric in results.values():
            for n in ("2", "4", "8", "16"):
                row = metric["grid_results"][n]
                self.assertEqual(sum(row["independent_phase_counts"].values()), 256)
                self.assertIn(row["block_mean_rank"], ("same", "reversed", "tie"))
                self.assertEqual(row["nominal_lag_km"], 15)

    def test_invalid_inputs_fail_closed(self):
        for bad in (np.ones((1, 5)), np.array([[1., float("nan")],[3.,4.]])):
            with self.assertRaises(ValueError):
                lag_contrast(bad)
        with self.assertRaises(ValueError):
            audit(np.ones((8, 8)), np.ones((8, 8)))
        with self.assertRaises(ValueError):
            audit(np.ones((64, 64)), np.ones((64, 64)))


if __name__ == "__main__":
    unittest.main()
