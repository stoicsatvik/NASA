"""Offline controls for E418; no network or planetary similarity claim."""
import copy
import math
import unittest

from research.e418_geographic_negative_deletion import audit, pairwise_auc


class E418Tests(unittest.TestCase):
    def setUp(self):
        self.toy = {
            "sites": [
                {"name": "p1", "lat": 10.0, "lon": -10.0},
                {"name": "p2", "lat": 20.0, "lon": -20.0},
                {"name": "p3", "lat": 30.0, "lon": -30.0},
            ],
            "negatives": [
                {"name": "n1", "lat": 0.0, "lon": 0.0},
                {"name": "n2", "lat": 5.0, "lon": 5.0},
                {"name": "n3", "lat": 15.0, "lon": 15.0},
            ],
        }

    def test_all_negative_deletions_and_replay(self):
        original = copy.deepcopy(self.toy)
        a = audit(self.toy, allow_toy=True)
        self.assertEqual(a, audit(self.toy, allow_toy=True))
        self.assertEqual(self.toy, original)
        self.assertEqual(len(a["rows"]), 3)
        self.assertEqual({r["omitted_negative"] for r in a["rows"]}, {"n1", "n2", "n3"})
        for row in a["rows"]:
            self.assertEqual(row["permutations"], math.comb(5, 3))
            self.assertTrue(0 < row["familywise_conditional_p"] <= 1)
            self.assertEqual(len(row["feature_auc"]), 5)

    def test_pairwise_ties(self):
        self.assertEqual(pairwise_auc([{"x": 1}], [{"x": 1}], lambda s: s["x"]), 0.5)
        self.assertEqual(pairwise_auc([{"x": 2}], [{"x": 1}], lambda s: s["x"]), 1.0)

    def test_fail_closed_population(self):
        with self.assertRaises(ValueError):
            audit(self.toy)
        bad = copy.deepcopy(self.toy)
        bad["negatives"][0]["name"] = "p1"
        with self.assertRaises(ValueError):
            audit(bad, allow_toy=True)
        bad = copy.deepcopy(self.toy)
        bad["sites"][0]["lat"] = float("nan")
        with self.assertRaises(ValueError):
            audit(bad, allow_toy=True)


if __name__ == "__main__":
    unittest.main()
