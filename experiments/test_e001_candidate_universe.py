"""E001 candidate-universe counterexample, synthetic fixture only.

Run: python -m unittest experiments.test_e001_candidate_universe -v
This tests evaluation validity, NOT planetary analogue recovery.
"""
import unittest
from experiments.e001_baseline import rank_fold


class CandidateUniverseAudit(unittest.TestCase):
    def test_other_family_positive_is_silently_excluded(self):
        rows = [
            {"site_id": "mars_ref", "family": "mars", "is_analog": "1", "x": 0.1},
            {"site_id": "mars_holdout", "family": "mars", "is_analog": "1", "x": 0.0},
            {"site_id": "moon_positive", "family": "moon", "is_analog": "1", "x": 0.01},
            {"site_id": "hard_negative", "family": "mars", "is_analog": "0", "x": 10.0},
        ]
        result = rank_fold(rows, ["x"], rows[1], candidate_policy="legacy_negatives_only")
        # Existing evaluator admits only is_analog=0 controls, so it excludes
        # moon_positive, despite that candidate being closer to the reference.
        self.assertEqual(result["rank"], 1)
        self.assertEqual(result["candidates"], 2)
        full = rank_fold(rows, ["x"], rows[1])
        self.assertEqual((full["rank"], full["candidates"]), (2, 3))
        # A fully specified non-reference candidate universe reverses the rank:
        # moon_positive distance .09 < mars_holdout distance .10.
        reference = rows[0]["x"]
        candidate_universe = [rows[1], rows[2], rows[3]]
        ranked = sorted(candidate_universe,
                        key=lambda r: (abs(r["x"] - reference), r["site_id"]))
        self.assertEqual([r["site_id"] for r in ranked],
                         ["moon_positive", "mars_holdout", "hard_negative"])
        self.assertEqual(next(i + 1 for i, r in enumerate(ranked)
                              if r["site_id"] == "mars_holdout"), 2)


if __name__ == "__main__":
    unittest.main()
