"""Offline E430 contract tests; no NASA dataset downloads or hidden labels."""
import json
import tempfile
import unittest
from pathlib import Path

from research.e430_earth_support_self_retrieval import FEATURES, SITES, load_pairs, retrieval


class SupportRetrievalTests(unittest.TestCase):
    def setUp(self):
        self.rows = {
            (site, km): tuple(float((i + 1) * (k + 2)) for k in range(4))
            for i, site in enumerate(SITES)
            for km in (2, 4)
        }

    def test_identical_supports_recover_all_sites(self):
        for mode in ("pooled_z", "log_ratio"):
            self.assertEqual(retrieval(self.rows, mode)["top1"], 3)

    def test_invalid_distance_or_ablation_fails(self):
        with self.assertRaises(ValueError):
            retrieval(self.rows, "cosine")
        with self.assertRaises(ValueError):
            retrieval(self.rows, "pooled_z", "site_name")

    def test_frozen_real_source_counts(self):
        rows = load_pairs()
        self.assertEqual(retrieval(rows, "pooled_z")["top1"], 2)
        self.assertEqual(retrieval(rows, "log_ratio")["top1"], 2)
        self.assertEqual(retrieval(rows, "log_ratio", FEATURES[3])["top1"], 0)
        for mode in ("pooled_z", "log_ratio"):
            self.assertTrue(all(retrieval(rows, mode, feature)["n"] == 3 for feature in FEATURES))

    def test_source_provenance_and_missingness_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            rows = [
                {"site": site, "physical_window_km": km,
                 "metrics": dict(zip(FEATURES, values))}
                for (site, km), values in self.rows.items()
            ]
            path.write_text(json.dumps({"experiment": "wrong", "sites": rows}))
            with self.assertRaises(ValueError):
                load_pairs(path)
            path.write_text(json.dumps({"experiment": "E214 real Earth fixture", "sites": rows[:-1]}))
            with self.assertRaises(ValueError):
                load_pairs(path)
            rows[0]["metrics"][FEATURES[0]] = 0
            path.write_text(json.dumps({"experiment": "E214 real Earth fixture", "sites": rows}))
            with self.assertRaises(ValueError):
                load_pairs(path)


if __name__ == "__main__":
    unittest.main()
