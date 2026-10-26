"""Deterministic controls for the exploratory E305 published-THEMIS audit."""
import csv
import tempfile
import unittest
from pathlib import Path

from research.e305_published_themis_time_audit import DATA, load, longitude_distance, matched, run


class PublishedThemisAudit(unittest.TestCase):
    def test_source_shape_and_units(self):
        rows = load()
        self.assertEqual(len(rows), 24)
        self.assertEqual(sum(r["local_time_h"] < 12 for r in rows), 13)
        self.assertEqual(sum(r["local_time_h"] >= 12 for r in rows), 11)
        self.assertEqual(longitude_distance(359, 1), 2)

    def test_season_matched_disjoint_pairs(self):
        rows = load()
        pairs = matched(rows, 10)
        self.assertEqual(len(pairs), 7)
        self.assertEqual(len({p["morning_id"] for p in pairs}), 7)
        self.assertEqual(len({p["evening_id"] for p in pairs}), 7)
        self.assertTrue(all(p["solar_longitude_separation_deg"] <= 10 for p in pairs))
        self.assertTrue(all(p["evening_minus_morning_k"] > 0 for p in pairs))

    def test_sensitivity_and_claim_boundary(self):
        result = run()
        self.assertEqual(result["measurement_status"], "SECONDARY_PUBLISHED_REAL_OBSERVATIONS")
        self.assertEqual(result["e001_known_analogue_recovery"], "NOT YET MEASURED")
        self.assertEqual(result["new_raw_pds_measurements"], 0)
        self.assertEqual([result["sensitivity"][str(t)]["n_disjoint_pairs"] for t in (5,10,15,20)], [5,7,8,9])
        self.assertEqual(result["ten_degree_positive_signs"], 7)
        self.assertAlmostEqual(result["unmatched_evening_minus_morning_mean_k"], 19.385958, places=5)

    def test_tampered_source_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "tampered.csv"
            path.write_text(DATA.read_text().replace("I34883005", "I35195003", 1))
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                load(path)
            path.write_text(DATA.read_text().replace("198.303", "nan", 1))
            with self.assertRaisesRegex(ValueError, "Nonfinite"):
                load(path)


if __name__ == "__main__":
    unittest.main()
