"""E242 synthetic controls; no synthetic data presented as Earth measurements."""
import unittest
import numpy as np
from research.e242_earth_sampling_aliasing import audit, block_means, plane_detrended_std, point_sample

class E242Controls(unittest.TestCase):
    def test_plane_has_zero_relief(self):
        y, x = np.indices((64, 80))
        plane = 30 + 2*x - 4*y
        self.assertLess(plane_detrended_std(plane), 1e-10)
        for n in (2, 4, 8, 16):
            self.assertLess(plane_detrended_std(block_means(plane, n)), 1e-10)

    def test_constant_offset_does_not_change_metrics(self):
        y, x = np.indices((64, 64))
        z = 2*np.sin(x/8) + np.cos(y/7) + x/3
        a, b = audit(z), audit(z+1000)
        self.assertAlmostEqual(a["high_resolution"]["detrended_relief_sd_m"],
                               b["high_resolution"]["detrended_relief_sd_m"], places=9)
        for n in (2, 4, 8, 16):
            k = f"grid_{n}x{n}"
            self.assertAlmostEqual(a[k]["block_mean_fraction_of_high_res"],
                                   b[k]["block_mean_fraction_of_high_res"], places=9)

    def test_high_frequency_checkerboard_is_lost_in_block_means(self):
        y, x = np.indices((64, 64))
        z = ((x+y)%2)*2-1
        self.assertGreater(plane_detrended_std(z), 0.9)
        for n in (2, 4, 8, 16):
            self.assertAlmostEqual(plane_detrended_std(block_means(z, n)), 0.0, places=12)

    def test_sampling_phase_is_explicit_and_bounded(self):
        z = np.arange(64*64).reshape(64, 64)
        self.assertEqual(point_sample(z, 4, .125, .125).shape, (4, 4))
        self.assertFalse(np.array_equal(point_sample(z, 4, .125, .125),
                                        point_sample(z, 4, .875, .875)))
        for args in ((-.1, .5), (1., .5), (.5, float("nan"))):
            with self.assertRaises(ValueError):
                point_sample(z, 4, *args)

    def test_fail_closed_on_invalid_data(self):
        with self.assertRaises(ValueError): audit(np.ones((4, 4)))
        with self.assertRaises(ValueError): audit(np.ones((64, 64)))
        with self.assertRaises(ValueError): audit(np.full((64, 64), np.nan))
        with self.assertRaises(ValueError): block_means(np.ones((2, 2)), 4)

if __name__ == "__main__":
    unittest.main()
