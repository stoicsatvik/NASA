"""E598 tests for duplicate-aware correlation and circular-shift nulls."""
import unittest
import numpy as np

from experiments.e598_grand_falls_wind_particle_association import (
    correlation_matrix,
    circular_shift_max_null,
    rankdata_average,
)


class E598AssociationTests(unittest.TestCase):
    def test_average_ranks_handle_ties(self):
        self.assertTrue(np.allclose(rankdata_average(np.array([1, 1, 2, 3])), [1.5, 1.5, 3, 4]))

    def test_spearman_perfect_positive_and_negative(self):
        x = np.array([[1, 2, 3, 4]], dtype=float)
        positive = correlation_matrix(x, x, "spearman")
        negative = correlation_matrix(x, x[:, ::-1], "spearman")
        self.assertAlmostEqual(float(positive[0, 0]), 1.0)
        self.assertAlmostEqual(float(negative[0, 0]), -1.0)

    def test_circular_shift_null_is_deterministic_and_familywise(self):
        n = 256
        base = np.sin(np.arange(n) / 9.0)
        wind = np.vstack([base, np.roll(base, 3), np.roll(base, 7)])
        particle = np.vstack([base, np.roll(base, 5), np.roll(base, 11)])
        ranks_w = np.vstack([rankdata_average(row) for row in wind])
        ranks_p = np.vstack([rankdata_average(row) for row in particle])
        a = circular_shift_max_null(ranks_w, ranks_p, permutations=99, min_shift=10, seed=7)
        b = circular_shift_max_null(ranks_w, ranks_p, permutations=99, min_shift=10, seed=7)
        self.assertEqual(a, b)
        self.assertGreaterEqual(a["familywise_p_value"], 0.0)
        self.assertLessEqual(a["familywise_p_value"], 1.0)
        self.assertTrue(a["shift_draws_unique"])

    def test_constant_series_is_rejected(self):
        with self.assertRaises(ValueError):
            correlation_matrix(np.ones((1, 8)), np.arange(8, dtype=float).reshape(1, 8), "spearman")


if __name__ == "__main__":
    unittest.main()
