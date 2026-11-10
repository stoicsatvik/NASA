import unittest

from experiments.e532_public_catalogue_audit import (
    SOURCE_COMMIT,
    SOURCE_URL,
    audit,
    safe_source_url,
)


def feature(site_id, target, status="Draft", refs=None, photos=None, sensitive="No"):
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [10.0, 20.0]},
        "properties": {
            "id": site_id,
            "name": site_id,
            "analogue_for_primary": target,
            "review_status": status,
            "coordinate_precision": "Approximately 10 km",
            "sensitive_site": sensitive,
            "references": refs or [],
            "photos": photos or [],
            "target_feature": "fixture",
        },
    }


class E532PublicCatalogueAuditTests(unittest.TestCase):
    def test_source_is_pinned_to_one_immutable_file(self):
        self.assertTrue(safe_source_url(SOURCE_URL))
        self.assertEqual(len(SOURCE_COMMIT), 40)
        self.assertFalse(safe_source_url(SOURCE_URL.replace(SOURCE_COMMIT, "main")))
        self.assertFalse(safe_source_url(SOURCE_URL.replace("raw.githubusercontent.com", "example.com")))
        self.assertFalse(safe_source_url(SOURCE_URL + "?download=1"))

    def test_audit_counts_candidate_labels_and_review_state(self):
        document = {
            "type": "FeatureCollection",
            "generated": "2026-10-12",
            "features": [
                feature("a", "Mars", refs=[
                    {"doi": "10.1000/a", "url": "https://doi.org/10.1000/a",
                     "peer_reviewed": True, "unverified": False}
                ], photos=[{"file": "a.jpg"}], sensitive="Yes"),
                feature("b", "Moon", status="Verified", refs=[
                    {"doi": None, "url": "https://example.org/b",
                     "peer_reviewed": False, "unverified": True}
                ]),
            ],
        }
        result = audit(document, "abc", 123)
        self.assertEqual(result["feature_count"], 2)
        self.assertEqual(result["primary_target_counts"], {"Mars": 1, "Moon": 1})
        self.assertEqual(result["mars_or_moon_primary_candidate_count"], 2)
        self.assertEqual(result["peer_reviewed_reference_count"], 1)
        self.assertEqual(result["non_peer_reviewed_reference_count"], 1)
        self.assertEqual(result["unverified_reference_count"], 1)
        self.assertEqual(result["photo_count"], 1)
        self.assertEqual(result["source"]["sha256"], "abc")
        self.assertFalse(result["all_records_draft"])

    def test_candidate_only_catalogue_never_becomes_e001_ground_truth_without_controls(self):
        document = {
            "type": "FeatureCollection",
            "features": [feature("a", "Mars"), feature("b", "Moon")],
        }
        result = audit(document)
        self.assertEqual(result["explicit_non_analogue_control_count"], 0)
        self.assertFalse(result["e001_supervised_recovery_ready"])

    def test_duplicate_ids_and_missing_geometry_are_visible(self):
        first = feature("same", "Mars")
        second = feature("same", "Moon")
        second["geometry"] = {"type": "Polygon", "coordinates": []}
        result = audit({"type": "FeatureCollection", "features": [first, second]})
        self.assertEqual(result["duplicate_site_id_count"], 1)
        self.assertEqual(result["valid_point_geometry_count"], 1)


if __name__ == "__main__":
    unittest.main()
