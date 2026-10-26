"""E310 structural negative-control tests; no causal or raw-PDS claim."""
import unittest
from copy import deepcopy

from research.e305_published_themis_time_audit import load
from research.e310_themis_year_aliasing import analyze, exact_rank, run


class ThemisYearAliasing(unittest.TestCase):
    def test_exact_rank_handles_dependence_and_independence(self):
        self.assertEqual(exact_rank([[1, 0, 1], [0, 1, 1], [1, 1, 2]]), 2)
        self.assertEqual(exact_rank([[1, 0], [0, 1]]), 2)
        self.assertEqual(exact_rank([[0, 0], [0, 0]]), 0)
        with self.assertRaises(ValueError):
            exact_rank([[1, 0], [1]])

    def test_published_year_groups_are_disjoint(self):
        result = analyze(load())
        self.assertEqual(result["n_observations"], 24)
        self.assertEqual(result["morning_years"], [26, 28, 29, 30, 31, 32])
        self.assertEqual(result["evening_years"], [33, 34, 35])
        self.assertEqual(result["years_with_both_time_groups"], [])
        self.assertEqual(result["year_only_design_rank"], 9)
        self.assertEqual(result["year_plus_time_design_rank"], 9)
        self.assertFalse(result["time_group_identifiable_conditional_on_year"])

    def test_season_pairs_cannot_resolve_year_aliasing(self):
        result = analyze(load())
        self.assertEqual(result["ten_degree_season_matched_pairs"], 7)
        self.assertEqual(result["pairs_from_different_mars_years"], 7)
        self.assertTrue(all(gap >= 1 for gap in result["paired_mars_year_gaps"]))
        self.assertEqual(len(set(
            result["observationally_equivalent_sse_by_assumed_time_coefficient_k"].values()
        )), 1)

    def test_overlapping_year_restores_design_rank_only(self):
        rows = deepcopy(load())
        evening = next(r for r in rows if r["local_time_h"] >= 12)
        evening["mars_year"] = 32.0
        result = analyze(rows)
        self.assertEqual(result["years_with_both_time_groups"], [32])
        self.assertTrue(result["time_group_identifiable_conditional_on_year"])
        self.assertEqual(result["year_plus_time_design_rank"],
                         result["year_only_design_rank"] + 1)
        self.assertIsNone(
            result["observationally_equivalent_sse_by_assumed_time_coefficient_k"])

    def test_provenance_and_claim_boundaries(self):
        result = run()
        self.assertEqual(result["measurement_status"], "SECONDARY_PUBLISHED_REAL_OBSERVATIONS")
        self.assertEqual(result["e001_known_analogue_recovery"], "NOT YET MEASURED")
        self.assertEqual(result["cross_body_similarity"], "NOT YET PROVEN")
        self.assertEqual(len(result["data_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
