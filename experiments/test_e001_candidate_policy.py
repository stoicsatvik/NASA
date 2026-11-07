"""Synthetic candidate-universe policy regression tests; no empirical analogue claim."""
import unittest
from experiments.e001_baseline import evaluate, rank_fold


class CandidatePolicyTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"site_id": "mars_ref", "family": "mars", "is_analog": "1", "x": 0.1},
            {"site_id": "mars_holdout", "family": "mars", "is_analog": "1", "x": 0.0},
            {"site_id": "moon_positive", "family": "moon", "is_analog": "1", "x": 0.01},
            {"site_id": "hard_negative", "family": "mars", "is_analog": "0", "x": 10.0},
        ]

    def test_full_universe_reverses_legacy_rank(self):
        holdout = self.rows[1]
        full = rank_fold(self.rows, ["x"], holdout)
        legacy = rank_fold(self.rows, ["x"], holdout, "legacy_negatives_only")
        self.assertEqual((full["rank"], full["candidates"]), (2, 3))
        self.assertEqual((legacy["rank"], legacy["candidates"]), (1, 2))
        self.assertEqual(full["candidate_policy"], "all_nonreference")

    def test_reject_undefined_universe(self):
        with self.assertRaisesRegex(ValueError, "Unknown candidate_policy"):
            rank_fold(self.rows, ["x"], self.rows[1], "positive_only")

    def test_evaluate_policy_is_propagated(self):
        mars_only = [r for r in self.rows if r["family"] == "mars"]
        full = evaluate(mars_only, ["x"])
        legacy = evaluate(mars_only, ["x"], "legacy_negatives_only")
        self.assertEqual(full["candidate_policy"], "all_nonreference")
        self.assertTrue(all(f["candidate_policy"] == "legacy_negatives_only" for f in legacy["folds"]))
        self.assertGreater(full["random_expected_top_1"], 0)


if __name__ == "__main__":
    unittest.main()
