import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research.e212_lola_mola_scale_gate import pixel_km, tile_std

class ScaleGateTests(unittest.TestCase):
    def test_pixel_ratio_and_equal_distance(self):
        moon, mars = pixel_km(1737.4)[0], pixel_km(3389.5)[0]
        self.assertAlmostEqual(mars / moon, 3389.5 / 1737.4)
        self.assertLess(abs(4 * moon - 2 * mars) / (4 * moon), 0.03)

    def test_longitude_width_shrinks_at_high_latitude(self):
        _, equator = pixel_km(1737.4, 0)
        _, near_pole = pixel_km(1737.4, 85)
        self.assertLess(near_pole, 0.1 * equator)

    def test_mask_excludes_missing_and_low_coverage(self):
        grid = np.array([[1., 2., 100., 101.], [3., 4., 102., 103.], [5., 6., 104., 105.], [7., 8., 106., 107.]])
        mask = np.ones_like(grid, dtype=bool)
        mask[0, 0] = False
        mask[0:2, 2:4] = False
        result = tile_std(grid, mask, 2)
        self.assertEqual(result.size, 3)
        self.assertAlmostEqual(result[0], np.std([2., 3., 4.]))

    def test_bad_shapes_fail_closed(self):
        with self.assertRaises(ValueError):
            tile_std(np.zeros((3, 4)), np.ones((3, 4), bool), 2)
        with self.assertRaises(ValueError):
            tile_std(np.zeros((4, 4)), np.ones((2, 4), bool), 2)

if __name__ == "__main__":
    unittest.main()
