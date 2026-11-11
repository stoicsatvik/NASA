import math
import unittest

import numpy as np
import pyproj

from experiments.e563_three_way_common_support import (
    build_hirise_crs,
    mola_pixel_centers,
    point_indices,
    summarize_common_support,
)
from experiments.e545_mola_observed_support import make_window, pixel_index


class E563ThreeWaySupportTests(unittest.TestCase):
    def test_mola_pixel_centers_round_trip_to_frozen_pixel_indices(self):
        row, col = pixel_index(18.3995, 77.27025)
        window = make_window(row, col, 33)
        lat, lon = mola_pixel_centers(window)
        center = 16
        self.assertEqual(lat.shape, (33, 33))
        self.assertEqual(lon.shape, (33, 33))
        self.assertAlmostEqual(float(lat[center, center]), 18.40234375, places=10)
        self.assertAlmostEqual(float(lon[center, center]), 77.26953125, places=10)
        self.assertEqual(pixel_index(float(lat[center, center]), float(lon[center, center])), (row, col))

    def test_hi_crs_is_derived_from_pds3_parameters_and_one_metre_scale(self):
        radius_km = 3396.19
        radius_m = radius_km * 1000.0
        pixels_per_degree = 2.0 * math.pi * radius_m / 360.0
        crs, metadata = build_hirise_crs({
            "A_AXIS_RADIUS": str(radius_km),
            "C_AXIS_RADIUS": str(radius_km),
            "CENTER_LATITUDE": "0.0",
            "CENTER_LONGITUDE": "0.0",
            "MAP_RESOLUTION": str(pixels_per_degree),
            "MAP_PROJECTION_TYPE": "EQUIRECTANGULAR",
        })
        self.assertTrue(crs.is_projected)
        self.assertAlmostEqual(metadata["derived_pixel_size_m"], 1.0, places=8)
        self.assertAlmostEqual(metadata["reference_radius_a_m"], radius_m, places=6)

    def test_point_indices_use_containing_pixel_not_nearest_integer(self):
        rows, cols, inside = point_indices(
            np.array([[0.5, 1.5, 2.1]]),
            np.array([[1.5, 0.5, 0.5]]),
            xmin=0.0,
            ymax=2.0,
            pixel_width=1.0,
            pixel_height=1.0,
            width=2,
            height=2,
        )
        np.testing.assert_array_equal(rows, np.array([[0, 1, 1]]))
        np.testing.assert_array_equal(cols, np.array([[0, 1, 2]]))
        np.testing.assert_array_equal(inside, np.array([[True, True, False]]))

    def test_common_support_denominator_excludes_interpolated_mola_bins(self):
        observed = np.array([[True, True, False], [True, False, True]])
        ctx = np.array([[True, True, True], [False, True, True]])
        hi = np.array([[True, False, True], [True, True, True]])
        result = summarize_common_support(observed, ctx, hi)
        self.assertEqual(result["mola_observed_bins"], 4)
        self.assertEqual(result["mola_observed_within_ctx_valid_pixels"], 3)
        self.assertEqual(result["mola_observed_within_hirise_valid_pixels"], 3)
        self.assertEqual(result["three_way_common_valid_point_support"], 2)
        self.assertEqual(result["three_way_fraction_of_observed_mola_bins"], 0.5)
        self.assertTrue(result["support_is_point_center_not_area_fraction"])

    def test_common_support_rejects_shape_mismatch_and_zero_observed_bins(self):
        with self.assertRaises(ValueError):
            summarize_common_support(np.ones((2, 2)), np.ones((2, 1)), np.ones((2, 2)))
        with self.assertRaisesRegex(ValueError, "no MOLA observed-shot bins"):
            summarize_common_support(np.zeros((2, 2)), np.ones((2, 2)), np.ones((2, 2)))

    def test_hi_crs_rejects_incomplete_or_wrong_projection_metadata(self):
        with self.assertRaisesRegex(Exception, "PDS3 label lacks"):
            build_hirise_crs({"MAP_PROJECTION_TYPE": "SIMPLE CYLINDRICAL"})


if __name__ == "__main__":
    unittest.main()
