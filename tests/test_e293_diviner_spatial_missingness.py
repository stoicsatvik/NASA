"""Deterministic, source-independent E293 spatial-null controls."""
import unittest
from research.e293_diviner_spatial_missingness import (
    audit_mask, longest_circular_run, max_circular_window,
)


class SpatialMaskTests(unittest.TestCase):
    def test_empty_and_all_missing(self):
        self.assertEqual(longest_circular_run([]), 0)
        self.assertEqual(longest_circular_run([False] * 16), 0)
        self.assertEqual(longest_circular_run([True] * 16), 16)
        self.assertEqual(max_circular_window([True] * 16, 4), 4)

    def test_wraparound_cluster(self):
        mask = [True, True] + [False] * 8 + [True] * 3
        self.assertEqual(longest_circular_run(mask), 5)
        self.assertEqual(max_circular_window(mask, 5), 5)

    def test_fixed_count_null_and_determinism(self):
        mask = [False] * 128
        for index in range(20, 40):
            mask[index] = True
        first = audit_mask(mask, seed=293, permutations=39)
        self.assertEqual(first, audit_mask(mask, seed=293, permutations=39))
        self.assertEqual(first["missing"], 20)
        self.assertEqual(first["longest_circular_missing_run_pixels"], 20)
        self.assertLess(first["permutation_p_run"], 0.05)

    def test_null_controls(self):
        mask = [False] * 32
        result = audit_mask(mask, seed=2, permutations=19)
        self.assertEqual(result["permutation_p_run"], 1.0)
        self.assertEqual(result["permutation_p_window"], 1.0)
        self.assertRaises(ValueError, max_circular_window, mask, 0)
        self.assertRaises(ValueError, audit_mask, [], seed=1)


if __name__ == "__main__":
    unittest.main()
