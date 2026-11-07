"""Deterministic controls for E520 frozen-forecast block exclusions."""
import csv
import unittest
from research.e520_gistemp_contiguous_block_influence import influence
from research.e519_gistemp_leave_one_year_out import DATA, COLUMNS, METHODS, errors


class E520Tests(unittest.TestCase):
    def test_constant_method_order_and_no_flip(self):
        series = {method: [float(i + j) for i in range(15)]
                  for j, method in enumerate(METHODS)}
        original, cases = influence(series, 2)
        self.assertEqual(original, METHODS[0])
        self.assertEqual(len(cases), 14)
        self.assertTrue(all(selected == original for _, _, selected in cases))

    def test_excluding_block_changes_only_scoring(self):
        series = {method: [10.0] * 15 for method in METHODS}
        series[METHODS[0]] = [0.0] * 13 + [100.0, 100.0]
        series[METHODS[1]] = [9.0] * 15
        baseline, cases = influence(series, 2)
        self.assertEqual(baseline, METHODS[1])
        self.assertEqual(cases[-1], (2024, 2025, METHODS[0]))
        self.assertEqual(len(series[METHODS[0]]), 15)

    def test_reject_invalid_blocks_and_lengths(self):
        series = {method: [0.0] * 15 for method in METHODS}
        for size in (0, 15, 16):
            with self.assertRaises(AssertionError):
                influence(series, size)
        series[METHODS[-1]].pop()
        with self.assertRaises(AssertionError):
            influence(series, 2)

    def test_pinned_source_reproduces_documented_flip_counts(self):
        with DATA.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        years = [int(row["year"]) for row in rows]
        self.assertEqual(years, list(range(2001, 2026)))
        expected = {"global": (4, 5), "tropics": (7, 4), "arctic": (4, 1)}
        for zone, column in COLUMNS:
            if zone.lower() not in expected:
                continue
            error_series = errors(years, [int(row[column]) / 100 for row in rows])
            for block_size, count in zip((2, 5), expected[zone.lower()]):
                original, cases = influence(error_series, block_size)
                self.assertEqual(len(cases), 16 - block_size)
                self.assertEqual(sum(selected != original for _, _, selected in cases), count)


if __name__ == "__main__":
    unittest.main()
