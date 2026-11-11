import unittest

from experiments.e552_hirise_nodata_missingness_audit import analyze, all_nodata_sha256


class E552NodataMissingnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = analyze()

    def test_cross_receipt_all_nodata_digest_reproduces(self):
        self.assertTrue(self.result["all_nodata_digest_reproduced"])
        self.assertEqual(
            all_nodata_sha256(
                self.result["source"]["nodata_value"],
                tuple(self.result["source"]["sample_shape"]),
            ),
            self.result["source"]["all_nodata_window_sha256"],
        )

    def test_three_unsupported_windows_are_all_nodata(self):
        self.assertEqual(self.result["all_nodata_window_count"], 3)
        self.assertEqual(
            self.result["unsupported_patch_ids"],
            ["x15_y15", "x50_y85", "x85_y85"],
        )

    def test_six_measured_windows_remain_distinct_from_all_nodata(self):
        self.assertEqual(self.result["full_common_support_window_count"], 6)
        self.assertEqual(self.result["unresolved_window_count"], 0)

    def test_missingness_cause_is_not_overclaimed(self):
        self.assertEqual(self.result["claim_state"]["cause_of_nodata"], "NOT DETERMINED")
        self.assertIn("descriptive", self.result["spatial_missingness"]["interpretation"])

    def test_e551_inference_remains_conditional(self):
        self.assertIn("CONDITIONAL", self.result["claim_state"]["E551_exchangeability"])
        self.assertEqual(
            self.result["claim_state"]["spatial_gradient"],
            "NOT SUPPORTED BY E551 SIX-PATCH EXACT NULL",
        )


if __name__ == "__main__":
    unittest.main()
