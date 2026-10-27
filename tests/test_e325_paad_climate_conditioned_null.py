"""E325 deterministic climate-stratified permutation controls."""
import csv
import io
import random
import unittest

from research.e325_paad_climate_conditioned_null import (
    audit, climate_family, groups_for, read_climate_sites,
    shuffle_within_groups,
)

CLIMATE = "Köppen_Geiger_Climate_Classification"


def fixture(*rows):
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["Field_Site", "Dune_Type", "Center_Latitude",
                     "Center_Longitude", CLIMATE])
    writer.writerows(rows)
    return read_climate_sites(stream.getvalue().encode("utf-8"))


def sites():
    return fixture(
        ("A", "B", 0, 0, "BWh"),
        ("B", "B", 0, 0.01, "BWh"),
        ("C", "D", 0, 3, "Cfa"),
        ("D", "D", 0, 3.01, "Cfa"),
        ("E", "U", 40, 20, "Dfc"),
    )


class TestE325(unittest.TestCase):
    def test_source_labels_are_not_guessed(self):
        self.assertEqual(climate_family("BWh"), "B")
        self.assertEqual(climate_family("Cfa"), "C")
        self.assertEqual(climate_family("BWh/BWk"), "UNCLASSIFIED")
        self.assertEqual(climate_family("desert"), "UNCLASSIFIED")

    def test_shuffling_preserves_full_strata(self):
        s = sites()
        tokens = [x["tokens"] for x in s]
        groups = groups_for(s, "climate_full")
        for seed in range(15):
            shuffled = shuffle_within_groups(tokens, groups, random.Random(seed))
            for group in groups:
                self.assertCountEqual([tokens[i] for i in group],
                                      [shuffled[i] for i in group])

    def test_climate_conditioned_null_and_claim_boundaries(self):
        result = audit(sites(), permutations=99)
        self.assertEqual(result["sites"], 5)
        self.assertEqual(result["e001_known_site_recovery"], "NOT YET MEASURED")
        self.assertEqual(result["cross_body_similarity"], "NOT YET PROVEN")
        self.assertEqual(result["conditional_permutations"]["climate_full"]
                         ["permutable_sites"], 4)
        self.assertGreater(result["observed"]["name_only_jaccard"], 0.5)
        for name in ("global", "climate_full", "climate_family"):
            self.assertTrue(0 < result["conditional_permutations"][name]
                            ["metrics"]["name_only_jaccard"]["upper_tail_p"] <= 1)

    def test_row_order_and_seed_reproducible(self):
        s = sites()
        self.assertEqual(audit(s, 39, 12), audit(list(reversed(s)), 39, 12))

    def test_singleton_strata_have_degenerate_null(self):
        s = sites()
        for i, row in enumerate(s):
            row["climate_full"] = f"unique_{i}"
        result = audit(s, 19)
        full = result["conditional_permutations"]["climate_full"]
        self.assertEqual(full["permutable_sites"], 0)
        self.assertTrue(full["metrics"]["name_only_jaccard"]["null"]["degenerate"])
        self.assertEqual(full["metrics"]["name_only_jaccard"]["upper_tail_p"], 1)

    def test_missing_climate_rejected(self):
        with self.assertRaises(ValueError):
            fixture(("A", "B", 0, 0, ""), ("B", "B", 0, 1, "BWh"),
                    ("C", "D", 0, 2, "Cfa"))

    def test_invalid_permutation_count_rejected(self):
        with self.assertRaises(ValueError):
            audit(sites(), permutations=0)


if __name__ == "__main__":
    unittest.main()
