import unittest

from e542_jezero_stack_compatibility import (
    DATASETS,
    build_result,
    contains_bbox,
    intersection_bbox,
    mola_local_pixel_spacing_m,
    spherical_bbox_area_km2,
    validate_bbox,
)


class TestE542JezeroStack(unittest.TestCase):
    def test_mola_tile_contains_both_jezero_envelopes(self):
        mola = DATASETS["mola_128ppd"]["bbox"]
        self.assertTrue(contains_bbox(mola, DATASETS["ctx_trn_2020"]["bbox"]))
        self.assertTrue(contains_bbox(mola, DATASETS["hirise_msr_2025"]["bbox"]))

    def test_ctx_and_hirise_have_a_nonempty_envelope_intersection(self):
        overlap = intersection_bbox(
            DATASETS["ctx_trn_2020"]["bbox"],
            DATASETS["hirise_msr_2025"]["bbox"],
        )
        self.assertEqual(overlap, [77.1605, 18.211, 77.38, 18.588])

    def test_overlap_envelope_area_is_reproducible(self):
        overlap = intersection_bbox(
            DATASETS["ctx_trn_2020"]["bbox"],
            DATASETS["hirise_msr_2025"]["bbox"],
        )
        self.assertAlmostEqual(spherical_bbox_area_km2(overlap), 275.8827284418, places=8)

    def test_hirise_2025_is_only_partially_inside_ctx_trn(self):
        self.assertFalse(
            contains_bbox(
                DATASETS["ctx_trn_2020"]["bbox"],
                DATASETS["hirise_msr_2025"]["bbox"],
            )
        )

    def test_reference_radius_differences_are_explicit(self):
        mola = DATASETS["mola_128ppd"]["radius_m"]
        ctx = DATASETS["ctx_trn_2020"]["radius_m"]
        science = DATASETS["ctx_science_investigation_2021"]["radius_m"]
        self.assertEqual(ctx - mola, 190.0)
        self.assertEqual(science - ctx, -30.0)

    def test_resolution_ratios_are_23_15_20_and_463(self):
        mola = DATASETS["mola_128ppd"]["resolution_m"]
        ctx = DATASETS["ctx_trn_2020"]["resolution_m"]
        hirise = DATASETS["hirise_msr_2025"]["resolution_m"]
        self.assertAlmostEqual(mola / ctx, 23.15)
        self.assertEqual(ctx / hirise, 20.0)
        self.assertEqual(mola / hirise, 463.0)

    def test_mola_local_spacing_is_anisotropic_at_overlap_centroid(self):
        overlap = intersection_bbox(
            DATASETS["ctx_trn_2020"]["bbox"],
            DATASETS["hirise_msr_2025"]["bbox"],
        )
        latitude = (overlap[1] + overlap[3]) / 2
        spacing = mola_local_pixel_spacing_m(
            latitude, DATASETS["mola_128ppd"]["resolution_m"]
        )
        self.assertAlmostEqual(latitude, 18.3995, places=6)
        self.assertAlmostEqual(spacing["east_west_m"], 439.3308687348, places=8)
        self.assertAlmostEqual(spacing["north_south_m"], 463.0, places=12)

        scale = build_result()["scale"]
        self.assertAlmostEqual(
            scale["mola_local_to_ctx_resolution_ratio_at_overlap_centroid"]["east_west"],
            21.9665434367,
            places=8,
        )
        self.assertAlmostEqual(
            scale["mola_local_to_ctx_resolution_ratio_at_overlap_centroid"]["north_south"],
            23.15,
            places=12,
        )
        self.assertAlmostEqual(
            scale["mola_local_to_hirise_resolution_ratio_at_overlap_centroid"]["east_west"],
            439.3308687348,
            places=8,
        )
        self.assertAlmostEqual(
            scale["mola_local_to_hirise_resolution_ratio_at_overlap_centroid"]["north_south"],
            463.0,
            places=12,
        )

    def test_mola_local_spacing_is_equatorial_and_latitude_symmetric(self):
        equator = mola_local_pixel_spacing_m(0.0)
        north = mola_local_pixel_spacing_m(18.3995)
        south = mola_local_pixel_spacing_m(-18.3995)
        self.assertAlmostEqual(equator["east_west_m"], 463.0, places=12)
        self.assertAlmostEqual(equator["north_south_m"], 463.0, places=12)
        self.assertAlmostEqual(north["east_west_m"], south["east_west_m"], places=12)
        self.assertAlmostEqual(north["north_south_m"], south["north_south_m"], places=12)

    def test_mola_local_spacing_rejects_invalid_latitudes_and_spacing(self):
        for latitude in (True, 90.01, float("nan")):
            with self.assertRaises(ValueError):
                mola_local_pixel_spacing_m(latitude)
        for spacing in (True, 0.0, -1.0, float("inf")):
            with self.assertRaises(ValueError):
                mola_local_pixel_spacing_m(18.3995, spacing)

    def test_science_investigation_extension_is_not_default_reference(self):
        notes = " ".join(DATASETS["ctx_science_investigation_2021"]["notes"]).lower()
        self.assertIn("significant pixel offsets from hrsc", notes)
        self.assertIn("without independent registration", notes)

    def test_mola_interpolation_caveat_is_preserved(self):
        notes = " ".join(DATASETS["mola_128ppd"]["notes"]).lower()
        self.assertIn("interpolated", notes)
        self.assertIn("55%", notes)
        self.assertIn("12 km", notes)

    def test_2025_hirise_alignment_is_not_overstated(self):
        hirise = DATASETS["hirise_msr_2025"]
        self.assertEqual(hirise["alignment_p93_m"], 6.0)
        self.assertEqual(hirise["alignment_p99_m"], 10.2)
        self.assertEqual(hirise["stereo_pairs_completed"], 8)
        self.assertEqual(hirise["stereo_pairs_planned"], 10)

    def test_claim_ceiling_remains_metadata_only(self):
        ceiling = build_result()["evidence_ceiling"]
        self.assertFalse(ceiling["raw_raster_bytes_ingested"])
        self.assertFalse(ceiling["pixel_values_inspected"])
        self.assertFalse(ceiling["mola_local_counts_sampled"])
        self.assertEqual(ceiling["known_site_recovery"], "NOT YET MEASURED")

    def test_boolean_bbox_coordinate_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_bbox([True, 0, 1, 2])


if __name__ == "__main__":
    unittest.main()
