"""Deterministic tests for E001 evaluation mechanics; synthetic data only."""
import unittest
from experiments.e001_baseline import evaluate, rank_fold


class E001BaselineTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"site_id": "a", "family": "mars", "is_analog": "1", "x": 0.0, "y": 0.0},
            {"site_id": "b", "family": "mars", "is_analog": "1", "x": 0.1, "y": 0.0},
            {"site_id": "c", "family": "mars", "is_analog": "0", "x": 9.0, "y": 9.0},
            {"site_id": "d", "family": "mars", "is_analog": "0", "x": 8.0, "y": 8.0},
        ]

    def test_nearby_analog_recovered(self):
        result = evaluate(self.rows, ["x", "y"])
        self.assertEqual(result["top_1_rate"], 1.0)
        self.assertEqual(len(result["folds"]), 2)

    def test_held_out_features_do_not_affect_training_stats(self):
        fold = rank_fold(self.rows, ["x"], self.rows[0])
        self.assertEqual(fold["rank"], 1)

    def test_missing_reference_rejected(self):
        with self.assertRaisesRegex(ValueError, "another same-family"):
            rank_fold(self.rows, ["x"], self.rows[0] | {"family": "moon"})

    def test_ablation_is_reported(self):
        self.assertEqual(set(evaluate(self.rows, ["x", "y"])["features"]), {"x", "y"})


if __name__ == "__main__":
    unittest.main()
