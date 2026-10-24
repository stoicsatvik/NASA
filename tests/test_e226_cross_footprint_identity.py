"""Deterministic synthetic controls for E226; not empirical terrain evidence."""
import importlib.util
import math
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "research/e226_cross_footprint_identity.py"
spec = importlib.util.spec_from_file_location("e226_cross_footprint_identity", MODULE)
e226 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e226)


def fixture():
    rows = []
    for window in e226.WINDOWS:
        for site, base in zip(e226.SITES, (1.0, 3.0, 7.0)):
            for north in e226.OFFSETS:
                for east in e226.OFFSETS:
                    rows.append({
                        "site": site, "window_km": window,
                        "north_offset_km": north, "east_offset_km": east,
                        "features": {
                            "plane_detrended_relief_std_m": base,
                            "slope_p90_dimensionless": base / 10,
                        },
                    })
    return {
        "experiment": "synthetic unit fixture",
        "sources": {s: {} for s in e226.SITES},
        "window_measurements": rows,
    }


class E226Tests(unittest.TestCase):
    def test_perfect_stable_fixture_and_permutation_invariant(self):
        r = e226.evaluate(fixture())
        self.assertEqual(len(r["comparisons"]), 12)
        for row in r["comparisons"].values():
            self.assertEqual(row["correct"], 72)
            self.assertEqual(row["total"], 72)
            self.assertEqual(row["exact_reference_label_permutation_correct"], [72, 24, 24, 0, 0, 24])
            self.assertEqual(sum(row["confusion"].values()), 72)

    def test_footprint_shift_breaks_cross_scale_not_same_scale(self):
        source = fixture()
        for row in source["window_measurements"]:
            if row["window_km"] == 4.0:
                base = {"ladakh_lead": 7.0, "lonar_lead": 3.0,
                        "western_ghats_lead": 1.0}[row["site"]]
                row["features"] = {
                    "plane_detrended_relief_std_m": base,
                    "slope_p90_dimensionless": base / 10,
                }
        r = e226.evaluate(source)["comparisons"]
        self.assertEqual(r["query_4km__reference_4km__both"]["correct"], 72)
        self.assertEqual(r["query_2km__reference_4km__both"]["correct"], 24)

    def test_center_excluded(self):
        self.assertEqual(e226.evaluate(fixture())["queries_per_case"], 72)

    def test_missing_row_rejected(self):
        s = fixture()
        s["window_measurements"].pop()
        with self.assertRaises(ValueError):
            e226.evaluate(s)

    def test_duplicate_rejected(self):
        s = fixture()
        s["window_measurements"].append(s["window_measurements"][0].copy())
        with self.assertRaises(ValueError):
            e226.evaluate(s)

    def test_nan_rejected(self):
        s = fixture()
        s["window_measurements"][0]["features"]["slope_p90_dimensionless"] = math.nan
        with self.assertRaises(ValueError):
            e226.evaluate(s)


if __name__ == "__main__":
    unittest.main()
