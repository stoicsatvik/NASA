import unittest
from experiments.e551_patch_spatial_null import analyze


class E551PatchSpatialNullTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = analyze()

    def test_preserves_three_unsupported_grid_positions(self):
        self.assertEqual(self.result["grid_positions"], 9)
        self.assertEqual(self.result["measured_patches"], 6)
        self.assertEqual(self.result["unsupported_patches"], ["x15_y15", "x50_y85", "x85_y85"])
        self.assertFalse(self.result["summary"]["all_nine_positions_measured"])

    def test_exact_permutation_space_is_complete(self):
        self.assertEqual(self.result["exact_permutation"]["permutations"], 720)

    def test_spatial_plane_is_not_significant_under_patch_level_null(self):
        null = self.result["exact_permutation"]
        self.assertAlmostEqual(self.result["observed_plane"]["r2_descriptive"], 0.5843077228043018, places=10)
        self.assertAlmostEqual(null["p_r2_ge_observed"], 0.24444444444444444, places=12)
        self.assertAlmostEqual(null["p_slope_norm_ge_observed"], 0.15, places=12)

    def test_sign_test_and_missingness_are_not_overstated(self):
        sign = self.result["sign_test"]
        self.assertEqual((sign["negative"], sign["positive"]), (5, 1))
        self.assertAlmostEqual(sign["two_sided_p"], 0.21875, places=12)
        self.assertIn("spatially informative missingness remains unresolved", self.result["exact_permutation"]["exchangeability_boundary"])

    def test_leave_one_patch_out_is_reported_for_every_patch(self):
        loo = self.result["leave_one_patch_out"]
        self.assertEqual(len(loo), 6)
        self.assertAlmostEqual(min(x["r2_descriptive"] for x in loo), 0.10693105003706926, places=10)
        self.assertAlmostEqual(max(x["r2_descriptive"] for x in loo), 0.9145172763086398, places=10)

    def test_claim_ceiling_is_preserved(self):
        state = self.result["claim_state"]
        self.assertEqual(state["cross_body_similarity"], "NOT YET PROVEN")
        self.assertEqual(state["known_site_recovery"], "NOT YET MEASURED")
        self.assertEqual(state["route_safety"], "NOT CLAIMED")


if __name__ == "__main__":
    unittest.main()
