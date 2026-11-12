import json
import unittest

from experiments.e572_analogue_catalogue_admissibility import audit_document


def feature(site_id, body, family, review, coordinates, extra=None, compare=None):
    properties = {
        "id": site_id,
        "analogue_for_primary": body,
        "analogue_type_primary": family,
        "review_status": review,
        "coordinate_precision": "Approximately 1 km",
        "references": [
            {
                "peer_reviewed": True,
                "unverified": False,
                "supports": ["analogue_for_primary", "target_feature"],
            }
        ],
        "access_level": 2,
        "hazard_rating": 2,
    }
    properties.update(extra or {})
    if compare is not None:
        properties["compare"] = compare
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": coordinates},
        "properties": properties,
    }


class E572CatalogueAuditTests(unittest.TestCase):
    def test_filters_to_mars_and_moon_and_rejects_catalogue_only_labels(self):
        document = {
            "type": "FeatureCollection",
            "generated": "2026-10-12",
            "features": [
                feature("mars-a", "Mars", "Volcanic", "Draft", [1, 2], {"temp_min_c": -20}),
                feature("mars-b", "Mars", "Volcanic", "Draft", [2, 3]),
                feature("moon-a", "Moon", "Geological", "Draft", [3, 4]),
                feature("europa-a", "Europa", "Ice", "Verified", [4, 5]),
            ],
        }
        result = audit_document(document)
        self.assertEqual(result["in_scope_features"], 3)
        self.assertEqual(result["in_scope_by_body"], {"Mars": 2, "Moon": 1})
        self.assertEqual(result["review_status_counts"], {"Draft": 3})
        self.assertEqual(result["common_numeric_fields"], ["access_level", "hazard_rating"])
        self.assertEqual(result["common_physical_numeric_fields"], [])
        self.assertEqual(result["explicit_non_analogue_controls"], 0)
        self.assertFalse(result["minimum_e001_input_gate_passed"])

    def test_minimum_gate_can_pass_only_with_verified_family_controls_and_physical_fields(self):
        document = {
            "type": "FeatureCollection",
            "features": [
                feature(
                    "positive-a", "Mars", "Volcanic", "Verified", [1, 2],
                    {"slope_mean_deg": 3.0},
                    {"elevation_m": 100.0},
                ),
                feature(
                    "positive-b", "Mars", "Volcanic", "Verified", [2, 3],
                    {"slope_mean_deg": 4.0},
                    {"elevation_m": 120.0},
                ),
                feature(
                    "control-a", "Mars", None, "Verified", [3, 4],
                    {"is_analog": False, "control_role": "negative", "slope_mean_deg": 2.0},
                    {"elevation_m": 90.0},
                ),
            ],
        }
        result = audit_document(document)
        self.assertEqual(result["verified_families_with_two_or_more"], [{"family": "Volcanic", "count": 2}])
        self.assertEqual(result["explicit_non_analogue_controls"], 1)
        self.assertEqual(result["common_physical_numeric_fields"], ["slope_mean_deg"])
        self.assertEqual(result["target_measurement_fields"], ["elevation_m"])
        self.assertEqual(result["common_target_measurement_fields"], ["elevation_m"])
        self.assertTrue(result["minimum_e001_input_gate_passed"])

    def test_sparse_target_measurement_field_does_not_satisfy_minimum_gate(self):
        document = {
            "type": "FeatureCollection",
            "features": [
                feature(
                    "positive-a", "Mars", "Volcanic", "Verified", [1, 2],
                    {"slope_mean_deg": 3.0}, {"elevation_m": 100.0},
                ),
                feature(
                    "positive-b", "Mars", "Volcanic", "Verified", [2, 3],
                    {"slope_mean_deg": 4.0},
                ),
                feature(
                    "control-a", "Mars", None, "Verified", [3, 4],
                    {"is_analog": False, "control_role": "negative", "slope_mean_deg": 2.0},
                ),
            ],
        }
        result = audit_document(document)
        self.assertEqual(
            result["target_measurement_field_coverage"],
            [{"field": "elevation_m", "count": 1}],
        )
        self.assertEqual(result["target_measurement_fields"], ["elevation_m"])
        self.assertEqual(result["common_target_measurement_fields"], [])
        self.assertFalse(result["minimum_e001_input_gate_passed"])
        self.assertTrue(any(
            "not populated across every in-scope positive/control record" in reason
            for reason in result["e001_reasons"]
        ))

    def test_duplicate_site_ids_are_rejected(self):
        first = feature("same", "Mars", "Volcanic", "Draft", [1, 2])
        second = feature("same", "Moon", "Volcanic", "Draft", [2, 3])
        with self.assertRaisesRegex(ValueError, "Duplicate site id"):
            audit_document({"type": "FeatureCollection", "features": [first, second]})

    def test_invalid_point_coordinates_are_rejected(self):
        bad = feature("bad", "Mars", "Volcanic", "Draft", [181, 2])
        with self.assertRaisesRegex(ValueError, "Out-of-range coordinates"):
            audit_document({"type": "FeatureCollection", "features": [bad]})


if __name__ == "__main__":
    unittest.main()
