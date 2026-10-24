"""Deterministic E223 controls. No fabricated synthetic measurements are labelled real."""
import importlib.util
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "research/e223_independent_jitter_rank.py"
spec = importlib.util.spec_from_file_location("e223_independent_jitter_rank", MODULE)
e223 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e223)


def fixture():
    rows = []
    for window in (2.0, 4.0):
        for site, base in zip(e223.EXPECTED_SITES, (3.0, 2.0, 1.0)):
            for north in e223.OFFSETS:
                for east in e223.OFFSETS:
                    rows.append({
                        "site": site, "window_km": window,
                        "north_offset_km": north, "east_offset_km": east,
                        "features": {
                            "plane_detrended_relief_std_m": base,
                            "slope_p90_dimensionless": base / 10,
                        },
                    })
    return {
        "experiment": "synthetic unit-test fixture",
        "sources": {s: {} for s in e223.EXPECTED_SITES},
        "window_measurements": rows,
    }


class E223Tests(unittest.TestCase):
    def test_fixed_order_is_invariant_across_all_combinations(self):
        result = e223.evaluate(fixture())
        for case in result["comparisons"].values():
            self.assertEqual(case["independent_combinations"], 15625)
            self.assertEqual(case["independent_center_order_fraction"], 1)
            self.assertEqual(case["synchronized_center_order_fraction"], 1)
            self.assertEqual(sum(case["independent_order_counts"].values()), 15625)
            self.assertEqual(sum(case["synchronized_order_counts"].values()), 25)

    def test_independent_offsets_can_reverse_order_while_sync_does_not(self):
        source = fixture()
        # Identical shared offset response for two sites preserves synchronized
        # ordering, but independent offsets can reverse their ordering.
        for row in source["window_measurements"]:
            if row["site"] == "ladakh_lead":
                row["features"]["plane_detrended_relief_std_m"] += row["east_offset_km"]
            elif row["site"] == "lonar_lead":
                row["features"]["plane_detrended_relief_std_m"] += row["east_offset_km"]
        # Base gap 1 prevents reversal; deliberately narrow it to 0.2.
        for row in source["window_measurements"]:
            if row["site"] == "lonar_lead":
                row["features"]["plane_detrended_relief_std_m"] += 0.8
        case = e223.evaluate(source)["comparisons"]["2km/plane_detrended_relief_std_m"]
        self.assertEqual(case["synchronized_center_order_fraction"], 1)
        self.assertLess(case["independent_center_order_fraction"], 1)
        self.assertGreater(len(case["independent_order_counts"]), 1)

    def test_missing_offset_fails_closed(self):
        source = fixture()
        source["window_measurements"].pop()
        with self.assertRaises(ValueError):
            e223.evaluate(source)

    def test_duplicate_offset_fails_closed(self):
        source = fixture()
        source["window_measurements"].append(source["window_measurements"][0].copy())
        with self.assertRaises(ValueError):
            e223.evaluate(source)

    def test_tie_fails_closed(self):
        source = fixture()
        for row in source["window_measurements"]:
            if row["site"] == "lonar_lead":
                row["features"]["slope_p90_dimensionless"] = 0.3
        with self.assertRaises(ValueError):
            e223.evaluate(source)


if __name__ == "__main__":
    unittest.main()
