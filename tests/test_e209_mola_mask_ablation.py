"""E209 synthetic controls, not Mars observations."""
import unittest
from research.e209_mola_mask_ablation import rank_sensitivity


class RankSensitivityTests(unittest.TestCase):
    def test_complete_coverage_preserves_ranking(self):
        heights = [0, 1, 2, 3, 10, 11, 12, 13, 0, 1, 2, 3, 10, 11, 12, 13]
        result = rank_sensitivity(heights, [1] * 16, 4, 4, tile_size=2)
        self.assertEqual(result["top_decile_overlap_fraction"], 1)
        self.assertEqual(result["ordinal_rank_correlation"], 1)

    def test_sparse_tiles_excluded_not_zero_filled(self):
        counts = [0] * 16
        counts[0] = counts[1] = 1
        result = rank_sensitivity(list(range(16)), counts, 4, 4, tile_size=2)
        self.assertEqual(result["eligible_tiles"], 1)
        self.assertEqual(result["excluded_tiles"], 3)
        self.assertIsNone(result["ordinal_rank_correlation"])

    def test_missing_count_not_treated_as_measurement(self):
        heights = [0, 0, 0, 100, 0, 0, 0, 0, 10, 11, 12, 13, 10, 11, 12, 13]
        counts = [1, 1, 1, 0] + [1] * 12
        result = rank_sensitivity(heights, counts, 4, 4, tile_size=2)
        self.assertLess(result["top_decile_overlap_fraction"], 1)

    def test_invalid_inputs(self):
        with self.assertRaisesRegex(ValueError, "grid shape"):
            rank_sensitivity([1], [1], 2, 2, tile_size=2)
        with self.assertRaisesRegex(ValueError, "tile_size"):
            rank_sensitivity([1] * 16, [1] * 16, 4, 4, tile_size=3)


if __name__ == "__main__":
    unittest.main()
