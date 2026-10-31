"""Synthetic controls for E446 support gate, not planetary validation."""
import copy
import unittest

from research.e446_cross_body_support_gate import evaluate


def fixture():
    planetary = {"grid_shape": [720, 1440],
                 "equatorial_pixel_north_south_km": {
                     "moon": 7.58083760603737, "mars": 14.78948374908695}}
    sites = []
    for name in ("lonar_lead", "western_ghats_lead", "ladakh_lead"):
        for km in (2, 4):
            sites.append({"site": name, "physical_window_km": km,
                          "metrics": {"pixel_m": {"north_south": 30.887522287092473},
                                      "shape": [65 if km == 2 else 130, 69]}})
    return planetary, {"sites": sites}


class SupportGateTests(unittest.TestCase):
    def test_all_six_fail(self):
        p, e = fixture()
        result = evaluate(p, e)
        self.assertTrue(result["all_six_earth_windows_fail_both_planetary_support_gates"])
        self.assertTrue(result["all_six_earth_windows_fail_even_one_pixel_per_body"])
        self.assertEqual(len(result["records"]), 6)

    def test_resolution_threshold(self):
        p, e = fixture()
        result = evaluate(p, e)
        self.assertAlmostEqual(result["minimum_4pixel_support_km"]["moon"], 30.32335042414948)
        self.assertAlmostEqual(result["minimum_4pixel_support_km"]["mars"], 59.1579349963478)

    def test_no_false_positive_from_large_earth_pixel_count(self):
        p, e = fixture()
        e["sites"][0]["metrics"]["shape"][0] = 1000000
        self.assertFalse(evaluate(p, e)["records"][0]["moon_meets_four_sample_gate"])

    def test_fail_closed_bad_planetary_resolution(self):
        p, e = fixture()
        p["equatorial_pixel_north_south_km"]["mars"] = 0
        with self.assertRaises(ValueError):
            evaluate(p, e)

    def test_fail_closed_wrong_grid(self):
        p, e = fixture()
        p["grid_shape"] = [100, 100]
        with self.assertRaises(ValueError):
            evaluate(p, e)

    def test_eligible_large_window_control(self):
        p, e = fixture()
        for row in e["sites"]:
            row["physical_window_km"] = 64
        result = evaluate(p, e)
        self.assertFalse(result["all_six_earth_windows_fail_both_planetary_support_gates"])
        self.assertTrue(all(r["moon_meets_four_sample_gate"] and r["mars_meets_four_sample_gate"]
                            for r in result["records"]))


if __name__ == "__main__":
    unittest.main()
