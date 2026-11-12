"""E596 tests for coordinate-free, fail-closed catalogue provenance auditing."""
import json
import tempfile
import unittest
from pathlib import Path

from experiments.e596_analogue_catalogue_provenance_audit import audit


def feature(site_id, status="Draft", precision="Approximately 10 km", sensitive="No"):
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [12.0, 34.0]},
        "properties": {
            "id": site_id,
            "name": site_id,
            "country": "Example",
            "review_status": status,
            "coordinate_precision": precision,
            "analogue_for_primary": "Mars",
            "analogue_type_primary": "Volcanic",
            "sensitive_site": sensitive,
            "references": [{"citation": "primary source"}],
            "photos": [],
        },
    }


class E596CatalogueAuditTests(unittest.TestCase):
    def test_draft_sites_are_not_admitted_as_e001_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sites.geojson"
            path.write_text(json.dumps({
                "type": "FeatureCollection",
                "features": [
                    feature("draft-a"),
                    feature("draft-b", precision="Region only", sensitive="Yes"),
                ],
            }), encoding="utf-8")
            result = audit(path)
        self.assertEqual(result["feature_count"], 2)
        self.assertEqual(result["draft_count"], 2)
        self.assertEqual(result["verified_count"], 0)
        self.assertEqual(result["e001_label_admission"], "NONE; source review status is not an independently validated ground-truth label")
        self.assertEqual(result["coordinate_precision_counts"], {
            "Approximately 10 km": 1, "Region only": 1
        })
        self.assertEqual(result["sensitive_site_count"], 1)

    def test_verified_source_status_still_does_not_auto_promote_to_ground_truth(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sites.geojson"
            path.write_text(json.dumps({
                "type": "FeatureCollection",
                "features": [feature("reviewed", status="Verified")],
            }), encoding="utf-8")
            result = audit(path)
        self.assertEqual(result["verified_count"], 1)
        self.assertEqual(result["verified_source_candidate_ids"], ["reviewed"])
        self.assertEqual(result["e001_label_admission"], "NONE; source review status is not an independently validated ground-truth label")

    def test_coordinates_and_geometry_are_never_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sites.geojson"
            path.write_text(json.dumps({
                "type": "FeatureCollection",
                "features": [feature("sensitive", sensitive="Yes")],
            }), encoding="utf-8")
            result = audit(path)
        self.assertFalse(result["raw_coordinates_retained"])
        self.assertFalse(result["raw_geometry_retained"])
        self.assertNotIn("coordinates", result["sites"][0])
        self.assertNotIn("geometry", result["sites"][0])

    def test_missing_references_and_duplicate_ids_fail_closed(self):
        for features in (
            [feature("no-refs")],
            [feature("duplicate"), feature("duplicate")],
        ):
            if features[0]["properties"]["id"] == "no-refs":
                features[0]["properties"]["references"] = []
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "sites.geojson"
                path.write_text(json.dumps({
                    "type": "FeatureCollection", "features": features
                }), encoding="utf-8")
                with self.assertRaises(ValueError):
                    audit(path)


if __name__ == "__main__":
    unittest.main()
