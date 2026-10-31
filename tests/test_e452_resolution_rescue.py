import unittest
from research.e452_resolution_rescue import evaluate

MOLA = {"pixels_per_degree": 16, "shape": [2880, 5760], "observed_fraction": 0.9455320457175926}
COARSE = {"grid_shape": [720, 1440], "equatorial_pixel_north_south_km":
          {"moon": 7.58083760603737, "mars": 14.78948374908695}}
EARTH = {"sites": [{"site": site, "physical_window_km": width}
                   for site in ("lonar_lead", "western_ghats_lead", "ladakh_lead")
                   for width in (2, 4)]}


class E452Tests(unittest.TestCase):
    def test_finer_mola_changes_one_pixel_gate_only(self):
        out = evaluate(MOLA, COARSE, EARTH)
        self.assertEqual(out["mars16_one_pixel_windows"], 3)
        self.assertEqual(out["mars16_four_pixel_windows"], 0)
        self.assertEqual(out["moon4_four_pixel_windows"], 0)

    def test_exact_spans(self):
        out = evaluate(MOLA, COARSE, EARTH)
        self.assertAlmostEqual(out["records"][0]["pixel_spans"]["mars_16ppd"], 0.5409248987811283)
        self.assertAlmostEqual(out["records"][1]["pixel_spans"]["mars_16ppd"], 1.0818497975622565)
        self.assertAlmostEqual(out["four_pixel_minimum_km"]["moon_4ppd"], 30.32335042414948)

    def test_no_fake_site_coverage(self):
        self.assertIsNone(evaluate(MOLA, COARSE, EARTH)["mola16_site_specific_measured_fraction"])

    def test_wrong_mola_product_rejected(self):
        with self.assertRaises(ValueError):
            evaluate({**MOLA, "pixels_per_degree": 4}, COARSE, EARTH)

    def test_invalid_pixel_rejected(self):
        with self.assertRaises(ValueError):
            evaluate(MOLA, {**COARSE, "equatorial_pixel_north_south_km": {"moon": float("nan"), "mars": 14}}, EARTH)

    def test_invalid_window_rejected(self):
        with self.assertRaises(ValueError):
            evaluate(MOLA, COARSE, {"sites": [{"site": "x", "physical_window_km": -1}] * 6})

    def test_missing_coverage_rejected(self):
        with self.assertRaises(ValueError):
            evaluate({**MOLA, "observed_fraction": 0}, COARSE, EARTH)


if __name__ == "__main__":
    unittest.main()
