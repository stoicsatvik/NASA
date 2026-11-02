"""Deterministic controls for E513 MOLA coordinate/gradient audit."""
import math
import unittest
from e513_mola_latitude_audit import mola_center, median_abs_gradient, audit

class E513Tests(unittest.TestCase):
    def test_upper_left_center(self):
        self.assertEqual(mola_center(0, 0), (89.875, .125))

    def test_last_pixel_center(self):
        self.assertEqual(mola_center(719, 1439), (-89.875, 359.875))

    def test_sample_latitude(self):
        self.assertEqual(mola_center(90, 720), (67.375, 180.125))

    def test_index_bounds(self):
        for pair in [(-1, 0), (720, 0), (0, 1440), (1.5, 0)]:
            with self.assertRaises(ValueError): mola_center(*pair)

    def test_datum_offset_invariant(self):
        p = [[float(i + 3*j) for j in range(5)] for i in range(5)]
        a = median_abs_gradient(p, 'mola', 44.875)
        b = median_abs_gradient([[v+4000 for v in row] for row in p], 'mola', 44.875)
        self.assertAlmostEqual(a, b)

    def test_flat_zero_and_nonfinite_rejected(self):
        self.assertEqual(median_abs_gradient([[1.]*5 for _ in range(5)], 'earth', 20), 0)
        p = [[1.]*5 for _ in range(5)];p[0][0]=math.nan
        with self.assertRaises(ValueError): median_abs_gradient(p, 'mola', 0)

    def test_zero_shot_fail_closed(self):
        p = [[1.]*5 for _ in range(5)]
        m = {'shape':[720,1440],'pixel_index_tiles':[{'center_row_col':[90,720], 'topography_m':p,'ground_return_counts':[[0]*5 for _ in range(5)]}]*5}
        e = {'sites':{k:{'elevation_m':p,'center_lat_lon_deg':[20,76]} for k in ['A','B','C']}}
        with self.assertRaisesRegex(ValueError,'zero-shot'): audit(m,e)

if __name__ == '__main__': unittest.main()
