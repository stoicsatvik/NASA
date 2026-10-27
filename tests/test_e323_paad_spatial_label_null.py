"""E323 deterministic controls: lexical labels, spatial groups and permutation nulls."""
import csv
import io
import unittest

from research.e323_paad_spatial_label_null import (
    audit, jaccard, nearest_indices, read_labeled_sites,
)


def rows(*items):
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["Field_Site", "Dune_Type", "Center_Latitude", "Center_Longitude"])
    writer.writerows(items)
    return stream.getvalue().encode()


def fixture():
    return read_labeled_sites(rows(
        ("A", "D", 0, 0), ("B", "D", 0, 0.01),
        ("C", "B", 0, 3), ("D", "B", 0, 3.01),
        ("E", "U", 40, 20),
    ))


class TestE323(unittest.TestCase):
    def test_raw_tokens_not_semantic_labels(self):
        sites = read_labeled_sites(rows(
            ("A", "D / Bd", 0, 0), ("B", "D", 0, 1), ("C", "Bd", 0, 2)))
        self.assertEqual(sites[0]["tokens"], frozenset({"D", "Bd"}))
        self.assertEqual(jaccard(sites[0]["tokens"], sites[1]["tokens"]), 0.5)

    def test_nearby_raw_label_dependency_measured(self):
        result = audit(fixture(), permutations=99)
        self.assertEqual(result["sites"], 5)
        self.assertGreater(result["name_only_nearest_jaccard"], 0.5)
        self.assertGreater(result["spatial_block_km"]["25"]["unblocked_minus_blocked_jaccard"], 0)
        self.assertEqual(result["e001_known_site_recovery"], "NOT YET MEASURED")

    def test_component_excludes_transitive_neighbors(self):
        sites = read_labeled_sites(rows(
            ("A", "D", 0, 0), ("B", "D", 0, 0.1),
            ("C", "D", 0, 0.2), ("D", "B", 0, 3)))
        indices = nearest_indices(sites, 15)
        self.assertEqual(indices[:3], [3, 3, 3])

    def test_antimeridian_spatial_group(self):
        sites = read_labeled_sites(rows(
            ("A", "D", 0, 179.999), ("B", "D", 0, -179.999),
            ("C", "B", 0, 0)))
        self.assertEqual(nearest_indices(sites, 25)[:2], [2, 2])

    def test_permutation_and_row_order_invariance(self):
        s = fixture()
        a = audit(s, permutations=99, seed=323)
        b = audit(list(reversed(s)), permutations=99, seed=323)
        self.assertEqual(a, b)
        self.assertEqual(a, audit(s, permutations=99, seed=323))

    def test_all_blocked_reports_absence_not_zero_score(self):
        s = read_labeled_sites(rows(
            ("A", "D", 0, 0), ("B", "B", 0, 0.001),
            ("C", "U", 0, 0.002)))
        result = audit(s, permutations=19)
        self.assertEqual(result["spatial_block_km"]["25"]["eligible_holdouts"], 0)
        self.assertIsNone(result["spatial_block_km"]["25"]["nearest_outside_component_jaccard"])
        self.assertNotIn("one_sided_upper_tail_p", result["spatial_block_km"]["25"])

    def test_invalid_source_and_permutation_bounds(self):
        for bad in (
            rows(("A", "D", 0, 0), ("A", "D", 0, 1), ("C", "B", 0, 2)),
            rows(("A", "", 0, 0), ("B", "D", 0, 1), ("C", "B", 0, 2)),
            rows(("A", "D", "nan", 0), ("B", "D", 0, 1), ("C", "B", 0, 2)),
        ):
            with self.assertRaises(ValueError):
                read_labeled_sites(bad)
        with self.assertRaises(ValueError):
            audit(fixture(), permutations=0)


if __name__ == "__main__":
    unittest.main()
