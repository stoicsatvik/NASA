from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from experiments.e576_hrsc_independent_control_admissibility import run

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "research" / "results" / "E576_HRSC_INDEPENDENT_CONTROL_ADMISSIBILITY_20261112.json"


class E576HRSCControlAdmissibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run()

    def test_hrsc_absolute_control_is_mola_gcp_controlled(self):
        source = self.result["sources"]["li_jiang_2023"]
        self.assertEqual(source["facts"]["control_source"], "MOLA PEDR ground-control points")
        self.assertEqual(source["facts"]["calibration_gcp_count"], 476)
        self.assertEqual(source["facts"]["overlapping_mola_point_count"], 125749)

    def test_best_hrsc_accuracy_fails_the_10m_scale_gate(self):
        derived = self.result["derived_screening"]
        self.assertEqual(derived["best_hrsc_calibration_accuracy_m"], 144.61)
        self.assertEqual(derived["best_hrsc_validation_accuracy_m"], 178.716)
        self.assertGreater(derived["calibration_scale_ratio_to_10_2m"], 14.0)
        self.assertFalse(derived["ratios_are_formal_uncertainty_comparisons"])

    def test_validation_values_are_all_far_above_target_scale(self):
        values = [
            value
            for orbit in self.result["sources"]["li_jiang_2023"]["facts"]["validation_horizontal_accuracy_m"].values()
            for value in orbit.values()
        ]
        self.assertEqual(len(values), 6)
        self.assertTrue(all(value > 10.2 for value in values))

    def test_2020_comparison_uses_hirise_reference_not_independent_control(self):
        source = self.result["sources"]["kirk_fergason_2020"]
        self.assertEqual(source["facts"]["reference_dataset"], "mosaicked HiRISE DTM")
        self.assertIsNone(source["facts"]["independent_absolute_control_residual_m"])
        self.assertTrue(self.result["admissibility"]["kirk_2020_uses_hirise_as_reference"])
        self.assertFalse(self.result["admissibility"]["kirk_2020_supplies_independent_absolute_control"])

    def test_horizontal_resolution_is_not_absolute_accuracy(self):
        facts = self.result["sources"]["kirk_fergason_2020"]["facts"]
        self.assertEqual(facts["horizontal_resolution_pixels"], [10, 20])
        self.assertEqual(facts["typical_dtm_ground_sample_distance_pixels"], [3, 5])
        self.assertFalse(self.result["admissibility"]["hrsc_admissible_for_10m_horizontal_validation"])

    def test_claims_and_challenge_selection_remain_conservative(self):
        claims = self.result["claim_state"]
        self.assertEqual(claims["independent_horizontal_registration"], "NOT YET MEASURED")
        self.assertEqual(claims["known_site_recovery"], "NOT YET MEASURED")
        self.assertEqual(claims["route_safety"], "NOT CLAIMED")
        selection = self.result["challenge_selection"]
        self.assertFalse(selection["challenge_locked"])
        self.assertFalse(selection["score_changed"])

    def test_cli_receipt_is_parseable_and_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "receipt.json"
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "experiments.e576_hrsc_independent_control_admissibility",
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

    def test_committed_receipt_matches_runner(self):
        with RECEIPT.open(encoding="utf-8") as handle:
            self.assertEqual(json.load(handle), self.result)


if __name__ == "__main__":
    unittest.main()
