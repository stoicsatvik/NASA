"""Deterministic controls for E511, without external downloads."""
import math
import unittest
from research.e511_window_sensitivity import gradient, nearest, windows, audit


class WindowSensitivityControls(unittest.TestCase):
    def setUp(self):
        self.patch = [[float(i * 5 + j) for j in range(5)] for i in range(5)]

    def test_nine_windows_and_center(self):
        result = windows(self.patch)
        self.assertEqual(len(result), 9)
        self.assertEqual(result[4], [[6., 7., 8.], [11., 12., 13.], [16., 17., 18.]])

    def test_reject_wrong_shape(self):
        with self.assertRaises(ValueError):
            windows([[0., 1.], [2., 3.]])

    def test_constant_offset_invariant(self):
        for n in (3, 5):
            patch = [row[:n] for row in self.patch[:n]]
            self.assertAlmostEqual(gradient(patch, 'earth', 20),
                                   gradient([[v + 1000 for v in row] for row in patch], 'earth', 20))

    def test_flat_gradient_zero(self):
        self.assertEqual(gradient([[5] * 5 for _ in range(5)], 'mola', 0), 0)

    def test_bad_nonfinite(self):
        bad = [row[:] for row in self.patch]
        bad[0][0] = math.nan
        with self.assertRaises(ValueError):
            gradient(bad, 'lola', 0)

    def test_tie_break_deterministic(self):
        self.assertEqual(nearest(1, {'z': 0, 'a': 2}), 'a')

    def test_no_false_e001_on_invalid_counts(self):
        lola = {'pixel_index_tiles': [{'values_km': self.patch}] * 5}
        mola = {'pixel_index_tiles': [{'topography_m': self.patch,
                                      'ground_return_counts': [[0] * 5 for _ in range(5)]}] * 5}
        earth = {'sites': {n: {'elevation_m': self.patch, 'center_lat_lon_deg': [20, 76]}
                           for n in ('A', 'B', 'C')}}
        with self.assertRaisesRegex(ValueError, 'zero-shot'):
            audit(lola, mola, earth)


if __name__ == '__main__':
    unittest.main()
