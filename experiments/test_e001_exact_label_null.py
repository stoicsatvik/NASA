"""Exact small-cohort null tests; synthetic only, no empirical analogue claim."""
import unittest
from experiments.e001_exact_label_null import exact_label_null


class ExactLabelNullTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"site_id": "a", "family": "mars", "is_analog": "1", "x": 0.0},
            {"site_id": "b", "family": "mars", "is_analog": "1", "x": 0.1},
            {"site_id": "c", "family": "mars", "is_analog": "0", "x": 1.0},
            {"site_id": "d", "family": "mars", "is_analog": "0", "x": 2.0},
        ]

    def test_exhaustive_null_and_tail(self):
        result = exact_label_null(self.rows, ["x"])
        self.assertEqual(result["exact_null_assignments"], 6)
        self.assertEqual(len(result["null_scores"]), 6)
        self.assertGreaterEqual(result["one_sided_p"], 1 / 6)
        self.assertLessEqual(result["one_sided_p"], 1)
        self.assertAlmostEqual(
            result["null_mean_top_1_rate"],
            sum(result["null_scores"]) / 6)

    def test_combinatorial_guard(self):
        with self.assertRaisesRegex(ValueError, "max_assignments"):
            exact_label_null(self.rows, ["x"], max_assignments=5)

    def test_family_with_one_positive_rejected(self):
        self.rows[1]["is_analog"] = "0"
        with self.assertRaisesRegex(ValueError, "two positive"):
            exact_label_null(self.rows, ["x"])


if __name__ == "__main__":
    unittest.main()
