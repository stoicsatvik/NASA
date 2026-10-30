"""Offline E411 tests. These validate arithmetic and index consistency only."""
import unittest

from research.e411_challenge_validation_ablation import audit, frozen_e193_inputs


class ChallengeAuditTests(unittest.TestCase):
    def test_prior_literal_inputs_are_unchanged(self):
        c, w = frozen_e193_inputs()
        self.assertEqual(len(c), 14)
        self.assertEqual(len(w), 7)
        self.assertEqual(str(sum(w)), "1.00")

    def test_index_detects_missing_lunar_navigator(self):
        r = audit()
        self.assertEqual(r["index_title_count"], 14)
        self.assertEqual(r["matched_prior_aliases"], 13)
        self.assertEqual(r["missing_from_prior"], ["Lunar Landing Site Navigator"])
        self.assertEqual(r["stale_prior_names"], ["CLPS lunar browser"])

    def test_original_ranking_reproduces(self):
        r = audit()
        self.assertEqual(r["base_analogue_rank"], 5)
        self.assertEqual(r["base_analogue_score"], "4.59")
        self.assertEqual(r["base_best_competitor"], "MODIS/VIIRS hotspots")
        self.assertEqual(r["base_best_competitor_score"], "5.43")
        self.assertEqual(r["gap_to_best_competitor"], "0.84")

    def test_validation_axis_is_the_unique_winner_reversal(self):
        r = audit()
        ranks = {k: v["analogue_rank"] for k, v in r["leave_one_criterion_out"].items()}
        self.assertEqual(ranks["validation"], 1)
        self.assertTrue(all(v > 1 for k, v in ranks.items() if k != "validation"))
        self.assertEqual(r["analogue_validation_score_for_tie_if_all_else_fixed"], "8.2")


if __name__ == "__main__":
    unittest.main()
