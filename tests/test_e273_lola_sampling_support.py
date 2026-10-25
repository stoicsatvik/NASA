"""Deterministic E273 sampling-support controls, independent of network data."""
import unittest
import numpy as np

from research.e273_lola_sampling_support import (
    lunar_windows, martian_windows, top_decile_retention, summarize,
)


class E273Controls(unittest.TestCase):
    def test_block_means_reduce_checkerboard_roughness(self):
        z = np.indices((8, 8)).sum(axis=0).astype(float) % 2
        raw, coarsened = lunar_windows(z)
        self.assertEqual(raw.size, 4)
        np.testing.assert_allclose(raw, 0.5)
        np.testing.assert_allclose(coarsened, 0.0)

    def test_plane_is_not_equivalent_to_checkerboard(self):
        z = np.tile(np.arange(8, dtype=float), (8, 1))
        raw, coarsened = lunar_windows(z)
        self.assertTrue(np.all(raw > coarsened))
        self.assertTrue(np.all(coarsened > 0))

    def test_missing_mars_counts_gate(self):
        z = np.arange(16, dtype=float).reshape(4, 4)
        counts = np.ones_like(z, dtype=bool)
        counts[:2, :2] = False
        counts[2, 2] = False
        vals, excluded = martian_windows(z, counts)
        self.assertEqual(excluded, 1)
        self.assertEqual(vals.size, 3)
        self.assertTrue(np.isfinite(vals).all())

    def test_bad_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            lunar_windows(np.zeros((6, 8)))
        with self.assertRaises(ValueError):
            lunar_windows(np.full((8, 8), np.nan))
        with self.assertRaises(ValueError):
            martian_windows(np.zeros((4, 4)), np.ones((4, 2), bool))
        with self.assertRaises(ValueError):
            summarize(np.array([np.nan]))

    def test_rank_retention_and_ties_are_deterministic(self):
        a = np.arange(100, dtype=float)
        b = a.copy()
        r = top_decile_retention(a, b)
        self.assertEqual(r["intersection"], 10)
        self.assertEqual(r["retention_fraction"], 1.0)
        reverse = top_decile_retention(a, -a)
        self.assertEqual(reverse["intersection"], 0)
        with self.assertRaises(ValueError):
            top_decile_retention(a, a[:-1])


if __name__ == "__main__":
    unittest.main()
