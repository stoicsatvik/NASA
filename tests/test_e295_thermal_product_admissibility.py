"""E295 deterministic mathematical falsification and provenance fail-closed tests."""
import unittest

from research.e295_thermal_product_admissibility import (
    REQUIRED_OBSERVATION_FIELDS, counterexample, cross_product_gate,
    piecewise_linear, product_gate, run,
)


class E295Tests(unittest.TestCase):
    def test_strict_monotone_rank_reversal(self):
        result = counterexample()
        self.assertEqual(result["raw_distances_k"], {"A": 5., "B": 15.})
        self.assertEqual(result["display_distances_arbitrary_units"], {"A": 90., "B": 10.})
        self.assertEqual((result["raw_nearest"], result["display_nearest"]), ("A", "B"))

    def test_invalid_stretch_rejected(self):
        with self.assertRaises(ValueError):
            piecewise_linear(1., ((0., 0.), (1., 1.), (2., 0.)))
        with self.assertRaises(ValueError):
            piecewise_linear(4., ((0., 0.), (1., 1.)))

    def test_visual_mosaic_is_not_kelvin_even_if_metadata_is_supplied(self):
        meta = {k: True for k in REQUIRED_OBSERVATION_FIELDS}
        self.assertEqual(product_gate("themis_night_global_mosaic", meta)["status"],
                         "REJECT_VISUAL_MOSAIC")
        self.assertFalse(product_gate("themis_night_global_mosaic", meta)["quantitative"])

    def test_projected_brightness_temperature_requires_scene_metadata(self):
        self.assertEqual(product_gate("themis_ir_pbt")["status"], "NEEDS_PRODUCT_METADATA")
        meta = {k: True for k in REQUIRED_OBSERVATION_FIELDS}
        self.assertEqual(product_gate("themis_ir_pbt", meta)["status"],
                         "WITHIN_PRODUCT_QUANTITATIVE_CANDIDATE")
        self.assertFalse(product_gate("themis_ir_pbt", meta)["cross_body_comparable"])

    def test_kelvin_quantity_mismatch_fails_closed(self):
        meta = {k: True for k in REQUIRED_OBSERVATION_FIELDS}
        result = cross_product_gate("themis_ir_pbt", "diviner_stn", (meta, meta))
        self.assertEqual(result, {"status": "REJECT_QUANTITY_MISMATCH", "units_match": True})

    def test_unknown_product_and_claims(self):
        self.assertEqual(product_gate("unknown")["status"], "UNKNOWN_PRODUCT")
        self.assertEqual(run()["e001_known_analogue_recovery"], "NOT YET MEASURED")
        self.assertEqual(run()["new_real_measurements"], 0)


if __name__ == "__main__":
    unittest.main()
