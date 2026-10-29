"""Offline deterministic checks; not independent scientific measurements."""
import math
import unittest
from research.e397_geographic_control_null import audit, midranks


class GeographicNullTests(unittest.TestCase):
    def test_midrank_ties(self):
        self.assertEqual(midranks([4, 2, 2, 8]), [3, 1.5, 1.5, 4])

    def test_reject_nonfinite(self):
        with self.assertRaises(ValueError):
            midranks([1, math.nan])

    def test_exact_enumeration(self):
        catalog = {"sites": [{"name": "A", "lat": 80, "lon": -100},
                             {"name": "B", "lat": 70, "lon": -90}],
                   "negatives": [{"name": "C", "lat": 0, "lon": 40},
                                 {"name": "D", "lat": 10, "lon": 50}]}
        out = audit(catalog, allow_toy=True)
        self.assertEqual(out["permutations"], 6)
        self.assertEqual(out["features"]["abs_lat"]["auc"], 1)
        self.assertEqual(out["features"]["abs_lat"]["exact_one_sided_p"], 1/6)
        self.assertEqual(out["five_feature_familywise_p"], 2/6)

    def test_invalid_coordinates_and_duplicate_identity(self):
        base = {"sites": [{"name": "A", "lat": 90.01, "lon": 0}],
                "negatives": [{"name": "B", "lat": 0, "lon": 0}]}
        with self.assertRaises(ValueError):
            audit(base, allow_toy=True)
        base["sites"][0]["lat"] = 90
        base["negatives"][0]["name"] = "A"
        with self.assertRaises(ValueError):
            audit(base, allow_toy=True)


if __name__ == "__main__":
    unittest.main()
