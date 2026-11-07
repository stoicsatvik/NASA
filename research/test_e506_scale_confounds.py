import unittest
from e506_scale_confounds import features, nearest, audit


class ScaleConfoundsTests(unittest.TestCase):
    def test_flat_patch_zero_gradient(self):
        f = features([[10.0] * 5 for _ in range(5)], 'earth', 19.5)
        self.assertEqual(f['median_dimensionless_gradient'], 0)
        self.assertEqual(f['median_abs_adjacent_m'], 0)

    def test_equal_pixel_steps_have_different_physical_gradients(self):
        patch = [[float(j) for j in range(5)] for _ in range(5)]
        e = features(patch, 'earth', 0)
        l = features(patch, 'lola', 0)
        m = features(patch, 'mola', 0)
        self.assertEqual(e['median_abs_adjacent_m'], l['median_abs_adjacent_m'])
        self.assertEqual(l['median_abs_adjacent_m'], m['median_abs_adjacent_m'])
        self.assertGreater(e['median_dimensionless_gradient'], l['median_dimensionless_gradient'])
        self.assertGreater(l['median_dimensionless_gradient'], m['median_dimensionless_gradient'])

    def test_latitude_changes_east_west_scale_only(self):
        patch = [[float(j) for j in range(5)] for _ in range(5)]
        a = features(patch, 'lola', 0)
        b = features(patch, 'lola', 60)
        self.assertEqual(a['north_spacing_km'], b['north_spacing_km'])
        self.assertAlmostEqual(a['east_spacing_km'] / b['east_spacing_km'], 2)

    def test_invalid_geometry_rejected(self):
        with self.assertRaises(ValueError):
            features([[1.0] * 4 for _ in range(5)], 'earth', 0)
        with self.assertRaises(ValueError):
            features([[1.0] * 5 for _ in range(5)], 'earth', 90)

    def test_nearest_tie_is_deterministic(self):
        self.assertEqual(nearest({'v': 1}, {'z': {'v': 2}, 'a': {'v': 0}}, 'v'), 'a')

    def test_zero_shot_mola_rejected(self):
        patch = [[1] * 5 for _ in range(5)]
        lola = {'pixel_index_tiles': [{'values_km': patch}]}
        mola = {'pixel_index_tiles': [{'topography_m': patch, 'ground_return_counts': [[0] * 5 for _ in range(5)]}]}
        earth = {'sites': {'control': {'elevation_m': patch, 'center_lat_lon_deg': [0, 0]}}}
        with self.assertRaisesRegex(ValueError, 'zero-shot'):
            audit(lola, mola, earth)


if __name__ == '__main__':
    unittest.main()
