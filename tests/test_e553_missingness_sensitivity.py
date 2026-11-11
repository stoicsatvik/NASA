import unittest

from experiments.e553_missingness_sensitivity import (
    analyze,
    load_payload,
    quantile_grid,
)
import numpy as np


class E553Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = analyze(levels=3)

    def test_frozen_e550_coverage_is_six_of_nine(self):
        payload = load_payload()
        self.assertEqual(len(payload["patches"]), 9)
        self.assertEqual(
            [p["patch_id"] for p in payload["patches"] if p["common_valid_cells"] == 0],
            ["x15_y15", "x50_y85", "x85_y85"],
        )

    def test_quantile_grid_uses_only_six_measured_values(self):
        values = np.array([-5.013924693674653, -3.152290503237964,
                           -2.727160244659899, -2.4269258962831373,
                           -1.5152992918465316, 2.4249066823599605])
        grid = quantile_grid(values, levels=3)
        self.assertAlmostEqual(grid[0], float(values.min()), places=12)
        self.assertAlmostEqual(grid[1], float(np.median(values)), places=12)
        self.assertAlmostEqual(grid[2], float(values.max()), places=12)

    def test_three_level_grid_runs_exact_nine_factorial_nulls(self):
        envelope = self.result["sensitivity_envelope"]
        self.assertEqual(envelope["completion_scenarios"], 27)
        self.assertEqual(envelope["permutations_per_scenario"], 362880)
        self.assertEqual(envelope["total_exact_permutation_evaluations"], 27 * 362880)

    def test_missingness_can_change_conditional_null_outcome(self):
        summary = self.result["summary"]
        self.assertEqual(summary["both_statistics_significant_completion_count"], 2)
        self.assertGreater(summary["exact_r2_p_value_range"][1], 0.9)
        self.assertLess(summary["exact_r2_p_value_range"][0], 0.05)
        self.assertLess(summary["exact_gradient_p_value_range"][0], 0.05)

    def test_hypothetical_completions_are_not_promoted_to_measurements(self):
        self.assertFalse(self.result["sensitivity_envelope"]["hypothetical_values_are_measurements"])
        self.assertEqual(self.result["claim_state"]["nine_position_spatial_gradient"],
                         "NOT IDENTIFIABLE; THREE POSITIONS UNSUPPORTED")
        self.assertIn("not a probability", self.result["limitations"][1])


if __name__ == "__main__":
    unittest.main()
