import unittest
from e510_spatial_null import audit, gradient, nearest, shuffled
import random


class E510Controls(unittest.TestCase):
    def test_flat_patch_has_zero_gradient(self):
        self.assertEqual(gradient([[7.0] * 5 for _ in range(5)], 'earth', 20), 0)

    def test_shuffling_preserves_histogram(self):
        p = [[5 * i + j for j in range(5)] for i in range(5)]
        q = shuffled(p, random.Random(2))
        self.assertEqual(sorted(sum(p, [])), sorted(sum(q, [])))
        self.assertNotEqual(p, q)

    def test_ties_are_deterministic(self):
        self.assertEqual(nearest(1, {'z': 2, 'a': 0}), 'a')

    def test_null_is_deterministic(self):
        p = [[float(i * 5 + j) for j in range(5)] for i in range(5)]
        l = {'pixel_index_tiles': [{'values_km': p}]}
        m = {'pixel_index_tiles': [{'topography_m': p, 'ground_return_counts': [[1] * 5 for _ in range(5)]}]}
        e = {'sites': {'a': {'elevation_m': p, 'center_lat_lon_deg': [20, 75]},
                       'b': {'elevation_m': [[v * 2 for v in row] for row in p], 'center_lat_lon_deg': [20, 75]}}}
        self.assertEqual(audit(l, m, e, repeats=11, seed=8), audit(l, m, e, repeats=11, seed=8))

    def test_zero_shot_rejected(self):
        p = [[1] * 5 for _ in range(5)]
        l = {'pixel_index_tiles': [{'values_km': p}]}
        m = {'pixel_index_tiles': [{'topography_m': p, 'ground_return_counts': [[0] * 5 for _ in range(5)]}]}
        e = {'sites': {'a': {'elevation_m': p, 'center_lat_lon_deg': [0, 0]},
                       'b': {'elevation_m': p, 'center_lat_lon_deg': [0, 0]}}}
        with self.assertRaisesRegex(ValueError, 'zero-shot'):
            audit(l, m, e)

    def test_invalid_repeats_rejected(self):
        with self.assertRaises(ValueError):
            audit({}, {}, {}, repeats=0)


if __name__ == '__main__':
    unittest.main()
