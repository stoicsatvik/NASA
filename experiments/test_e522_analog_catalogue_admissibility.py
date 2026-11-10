import unittest

from experiments.e522_analog_catalogue_admissibility import audit, load_catalogue


class E522AnalogCatalogueAdmissibilityTests(unittest.TestCase):
    def test_official_gallery_pair_inventory_and_provenance(self):
        rows = load_catalogue()
        self.assertEqual(len(rows), 11)
        self.assertTrue(all(row["source_url"].endswith("analog-explorer/") for row in rows))
        self.assertTrue(all(row["source_accessed_utc"] == "2026-11-10" for row in rows))
        report = audit(rows)
        self.assertEqual(report["moon_mars_pair_count"], 9)
        self.assertEqual(report["out_of_scope_pair_count"], 2)
        self.assertEqual(report["moon_mars_target_body_counts"], {"Mars": 6, "Moon": 3})

    def test_mechanism_families_are_singletons(self):
        report = audit()
        self.assertEqual(report["mechanism_family_count"], 9)
        self.assertTrue(all(n == 1 for n in report["mechanism_family_sizes"].values()))
        self.assertFalse(report["mechanism_grouping_has_reference_centroid"])

    def test_body_grouping_is_numerically_large_but_scientifically_heterogeneous(self):
        report = audit()
        self.assertTrue(report["body_grouping_has_minimum_positive_count"])
        self.assertEqual(report["moon_mars_target_body_counts"], {"Mars": 6, "Moon": 3})
        self.assertGreater(report["mechanism_family_count"], 1)

    def test_gallery_alone_fails_closed_for_e001(self):
        report = audit()
        self.assertFalse(report["numeric_features_present"])
        self.assertFalse(report["coordinates_and_footprints_present"])
        self.assertFalse(report["negative_controls_present"])
        self.assertFalse(report["e001_ready"])
        self.assertIn("NOT YET MEASURED", report["claim_state"])


if __name__ == "__main__":
    unittest.main()
