"""Frozen metadata-only tests; do not confuse pixel spacing with measured support."""
import math
import unittest

from e458_high_resolution_catalog_gate import evaluate, pixel_spacing_km


class E458CatalogGate(unittest.TestCase):
    def test_official_mars_128_equatorial_pixel_spacing(self):
        self.assertAlmostEqual(pixel_spacing_km("mars", 128) * 1000, 463.0835744, places=5)

    def test_moon_64_pixel_spacing(self):
        self.assertAlmostEqual(pixel_spacing_km("moon", 64), 0.47380235037733565, places=12)

    def test_four_pixel_gate_changes_from_e452(self):
        result = evaluate()
        self.assertEqual(result["paired_same_ppd_pass"], {"2": [128], "4": [64, 128]})
        self.assertEqual(len(result["rows"]), 16)

    def test_stricter_eight_pixel_gate(self):
        self.assertEqual(evaluate(8)["paired_same_ppd_pass"], {"2": [], "4": [128]})

    def test_missing_empirical_evidence_stays_missing(self):
        for row in evaluate()["rows"]:
            self.assertIsNone(row["measured_site_coverage"])
            self.assertIsNone(row["effective_spatial_resolution_km"])

    def test_invalid_inputs_rejected(self):
        for body, ppd in (("earth", 64), ("moon", 32), ("mars", True)):
            with self.assertRaises(ValueError):
                pixel_spacing_km(body, ppd)
        for threshold in (0, -1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                evaluate(threshold)

    def test_no_physical_claim_from_catalog(self):
        r = evaluate()
        self.assertEqual(r["known_analogue_recovery"], "NOT YET MEASURED")
        self.assertEqual(r["cross_body_similarity"], "NOT YET PROVEN")


if __name__ == "__main__":
    unittest.main()
