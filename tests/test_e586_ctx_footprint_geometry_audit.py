import copy
import unittest

from shapely.geometry import Polygon, MultiPolygon

from experiments.e586_ctx_footprint_geometry_audit import (
    analyze_features,
    geometry_sha256,
    pairwise_footprint_overlap,
    project_geometry,
    safe_asset_summary,
)

COLLECTION = "mro_ctx_controlled_usgs_dtms"


def rectangle(west, south, east, north):
    return {
        "type": "Polygon",
        "coordinates": [[
            [west, south], [east, south], [east, north],
            [west, north], [west, south],
        ]],
    }


def receipt(ids):
    return {
        "experiment": "E583",
        "credentials_used": False,
        "items": [
            {
                "id": item_id,
                "metrics": {
                    "mean_difference_m": 25.0,
                    "median_difference_m": 24.0,
                    "stddev_difference_m": 12.0,
                },
            }
            for item_id in ids
        ],
    }


def features(ids):
    result = []
    for index, item_id in enumerate(ids):
        west = 76.75 + index * 0.01
        geometry = rectangle(west, 17.75, west + 0.25, 18.25)
        result.append({
            "type": "Feature",
            "id": item_id,
            "collection": COLLECTION,
            "bbox": [west, 17.75, west + 0.25, 18.25],
            "geometry": geometry,
            "assets": {
                "qa_metrics": {
                    "href": "https://astrogeo-ard.s3.amazonaws.com/qa.txt?X-Amz-Signature=SECRET",
                    "title": "QA metrics",
                    "type": "text/plain",
                    "roles": ["metadata"],
                }
            },
        })
    return result


class E586Tests(unittest.TestCase):
    def test_nine_pinned_items_produce_geometry_metrics_only(self):
        ids = [f"item-{index}" for index in range(9)]
        result = analyze_features(features(ids), receipt(ids))
        self.assertEqual(result["decision"], "GEOMETRY_AUDIT_COMPLETE")
        self.assertEqual(result["selected_item_count"], 9)
        self.assertEqual(result["strict_geometry_contained_count"], 9)
        self.assertEqual(result["partial_geometry_count"], 0)
        self.assertEqual(result["invalid_item_count"], 0)
        self.assertEqual(result["pairwise_footprint_overlap"]["total_pairs"], 36)
        self.assertNotIn("coordinates", str(result))
        self.assertNotIn("SECRET", str(result))
        self.assertFalse(result["raw_geometry_stored"])

    def test_actual_footprint_overlap_can_reject_bbox_overlap_as_proxy(self):
        left = Polygon([
            (76.8, 17.8), (77.2, 17.8), (76.8, 18.2), (76.8, 17.8)
        ])
        right = Polygon([
            (77.2, 18.2), (77.2, 17.8), (76.8, 18.2), (77.2, 18.2)
        ])
        self.assertEqual(left.bounds, right.bounds)
        projected_left = project_geometry(left.__geo_interface__)[1]
        projected_right = project_geometry(right.__geo_interface__)[1]
        rows = [
            {"id": "left", "_geometry": projected_left},
            {"id": "right", "_geometry": projected_right},
        ]
        result = pairwise_footprint_overlap(rows)
        self.assertEqual(result["total_pairs"], 1)
        self.assertEqual(result["footprint_intersecting_pairs"], 0)

    def test_partial_actual_geometry_is_measured_not_inferred_from_bbox(self):
        ids = [f"item-{index}" for index in range(9)]
        data = features(ids)
        data[0]["geometry"] = rectangle(76.0, 17.75, 77.0, 18.25)
        data[0]["bbox"] = [76.0, 17.75, 77.0, 18.25]
        result = analyze_features(data, receipt(ids))
        self.assertEqual(result["decision"], "GEOMETRY_AUDIT_COMPLETE")
        self.assertEqual(result["strict_geometry_contained_count"], 8)
        self.assertEqual(result["partial_geometry_count"], 1)
        self.assertLess(
            result["items"][0]["fraction_of_footprint_inside_aoi"], 0.99
        )

    def test_polygon_holes_reduce_true_footprint_area(self):
        outer = Polygon(
            [(76.8, 17.8), (77.2, 17.8), (77.2, 18.2), (76.8, 18.2)],
            holes=[[(76.9, 17.9), (77.1, 17.9), (77.1, 18.1), (76.9, 18.1)]],
        )
        plain = Polygon([(76.8, 17.8), (77.2, 17.8), (77.2, 18.2), (76.8, 18.2)])
        projected_hole = project_geometry(outer.__geo_interface__)[1]
        projected_plain = project_geometry(plain.__geo_interface__)[1]
        self.assertLess(projected_hole.area, projected_plain.area)

    def test_multipolygon_is_supported(self):
        geometry = MultiPolygon([
            Polygon([(76.8, 17.8), (76.9, 17.8), (76.9, 17.9), (76.8, 17.9)]),
            Polygon([(77.0, 18.0), (77.1, 18.0), (77.1, 18.1), (77.0, 18.1)]),
        ])
        parsed, projected = project_geometry(geometry.__geo_interface__)
        self.assertEqual(parsed.geom_type, "MultiPolygon")
        self.assertGreater(projected.area, 0)

    def test_item_set_mismatch_fails_closed(self):
        ids = [f"item-{index}" for index in range(9)]
        data = features(ids)
        data.pop()
        result = analyze_features(data, receipt(ids))
        self.assertEqual(result["decision"], "ITEM_SET_MISMATCH")
        self.assertEqual(result["missing_item_ids"], [ids[-1]])

    def test_invalid_geometry_is_preserved_as_partial_not_repaired(self):
        ids = [f"item-{index}" for index in range(9)]
        data = features(ids)
        data[0]["geometry"] = {
            "type": "Polygon",
            "coordinates": [[[76.8, 17.8], [77.2, 18.2], [76.8, 18.2], [77.2, 17.8], [76.8, 17.8]]],
        }
        result = analyze_features(data, receipt(ids))
        self.assertEqual(result["decision"], "PARTIAL_GEOMETRY_AUDIT")
        self.assertEqual(result["invalid_item_count"], 1)
        self.assertEqual(result["invalid_items"][0]["id"], ids[0])

    def test_geometry_hash_is_deterministic(self):
        geometry = rectangle(76.8, 17.8, 77.2, 18.2)
        self.assertEqual(geometry_sha256(geometry), geometry_sha256(copy.deepcopy(geometry)))

    def test_signed_query_values_are_not_retained(self):
        summary = safe_asset_summary({
            "href": "https://astrogeo-ard.s3.amazonaws.com/qa.txt?X-Amz-Signature=SECRET",
            "title": "QA metrics",
            "type": "text/plain",
            "roles": ["metadata"],
        })
        self.assertEqual(summary["url"]["host"], "astrogeo-ard.s3.amazonaws.com")
        self.assertEqual(summary["url"]["query_key_names"], ["x-amz-signature"])
        self.assertNotIn("SECRET", str(summary))


if __name__ == "__main__":
    unittest.main()
