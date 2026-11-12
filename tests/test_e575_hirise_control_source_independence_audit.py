from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from experiments.e575_hirise_control_source_independence_audit import run

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "research" / "results" / "E575_HIRISE_CONTROL_SOURCE_INDEPENDENCE_AUDIT_20261112.json"


class E575HiRISEControlIndependenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run()

    def test_10_2m_is_ctx_relative_not_absolute(self):
        audit = self.result["control_independence_audit"]
        self.assertTrue(audit["10_2m_is_ctx_relative_p99_alignment"])
        self.assertFalse(audit["10_2m_is_absolute_horizontal_accuracy"])
        self.assertEqual(
            self.result["sources"]["usgs_msr_product"]["facts"]["mosaic_to_ctx_horizontal_alignment_p99_m"],
            10.2,
        )

    def test_internal_dem_and_orthoimage_stats_are_not_ground_control(self):
        audit = self.result["control_independence_audit"]
        self.assertTrue(audit["0_9m_is_internal_individual_dem_alignment"])
        self.assertFalse(audit["0_9m_is_independent_ground_control"])
        self.assertTrue(audit["1m_3m_method_uses_orthoimage_correlation"])
        self.assertFalse(audit["1m_3m_inter_mosaic_values_are_independent_ground_control"])

    def test_general_mola_accuracy_guidance_is_not_product_specific(self):
        source = self.result["sources"]["usgs_hirise_ard_guidance"]
        self.assertEqual(source["facts"]["general_horizontal_accuracy_relative_to_mola_pedr_best_case_m"], 100.0)
        self.assertIn("not a 2025 product-specific residual", source["reference_role"])

    def test_independent_horizontal_control_remains_unmeasured(self):
        audit = self.result["control_independence_audit"]
        claims = self.result["claim_state"]
        self.assertFalse(audit["2025_product_specific_held_out_mola_horizontal_residual_found"])
        self.assertFalse(audit["independent_horizontal_control_for_pinned_2025_dtm_found"])
        self.assertEqual(claims["independent_horizontal_registration"], "NOT YET MEASURED")
        self.assertEqual(claims["route_safety"], "NOT CLAIMED")

    def test_mola_is_independent_but_too_coarse_for_10m_validation(self):
        audit = self.result["control_independence_audit"]
        guidance = self.result["sources"]["usgs_hirise_ard_guidance"]["facts"]
        self.assertTrue(audit["mola_pedr_is_an_independent_sensor_family"])
        self.assertFalse(audit["mola_pedr_horizontal_support_sufficient_for_10m_validation"])
        self.assertEqual(guidance["mola_shot_footprint_approx_m"], 100.0)
        self.assertIn("too coarse to validate a 10.2 m residual", self.result["next_gate"])

    def test_cli_writes_parseable_json_with_a_real_newline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "receipt.json"
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "experiments.e575_hirise_control_source_independence_audit",
                    "--out",
                    str(output),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = output.read_text(encoding="utf-8")
            self.assertTrue(payload.endswith("\n"))
            self.assertEqual(json.loads(payload), self.result)

    def test_challenge_ranking_remains_conditional(self):
        selection = self.result["challenge_selection"]
        self.assertGreater(selection["martian_map_11_score"], selection["modis_viirs_9_score"])
        self.assertGreater(selection["modis_viirs_9_score"], selection["planetary_analog_10_score"])
        self.assertFalse(selection["challenge_locked"])
        self.assertIn("no numeric score change", selection["ranking_state"])

    def test_committed_receipt_matches_source_audit(self):
        with RECEIPT.open(encoding="utf-8") as handle:
            receipt = json.load(handle)
        self.assertEqual(receipt, self.result)


if __name__ == "__main__":
    unittest.main()
