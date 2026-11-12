import json
import unittest

from experiments.e583_ctx_qa_cohort_screen import (
    COLLECTION,
    JEZERO_BBOX,
    SEARCH_LIMIT,
    build_search_payload,
    select_items,
    summarize_metrics,
    summarize_receipt,
)


class E583Tests(unittest.TestCase):
    def test_search_payload_pins_collection_bbox_and_small_limit(self):
        self.assertEqual(
            build_search_payload(),
            {"collections": [COLLECTION], "bbox": JEZERO_BBOX, "limit": SEARCH_LIMIT},
        )
        self.assertLessEqual(SEARCH_LIMIT, 9)

    def test_selection_filters_collection_deduplicates_sorts_and_caps(self):
        features = []
        for item_id in ["Z-item", "A-item", "M-item", "B-item"]:
            features.append({
                "type": "Feature",
                "id": item_id,
                "collection": COLLECTION,
                "properties": {"datetime": "2023-04-18T12:00:00Z"},
                "bbox": [77.0, 18.0, 77.5, 18.5],
                "assets": {"qa_metrics": {"href": "https://astrogeo-ard.s3-us-west-2.amazonaws.com/qa.txt"}},
            })
        features.append({
            "type": "Feature",
            "id": "wrong-collection",
            "collection": "other",
            "assets": {"qa_metrics": {"href": "https://astrogeo-ard.s3-us-west-2.amazonaws.com/qa.txt"}},
        })
        features.append(features[0])
        selected = select_items({"type": "FeatureCollection", "features": features}, max_items=3)
        self.assertEqual([item["id"] for item in selected], ["A-item", "B-item", "M-item"])
        self.assertEqual(len(selected), 3)

    def test_missing_qa_asset_is_preserved_as_a_candidate_result(self):
        selected = select_items({
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "id": "item-without-qa",
                "collection": COLLECTION,
                "properties": {},
                "assets": {"dtm": {"href": "https://astrogeo-ard.s3-us-west-2.amazonaws.com/dtm.tif"}},
            }],
        })
        self.assertEqual(len(selected), 1)
        self.assertIsNone(selected[0]["qa_asset"])

    def test_metric_summary_extracts_only_named_qa_statistics(self):
        parsed = {
            "decision": "QA_KEY_VALUE_SUMMARY",
            "metric_count": 3,
            "metrics": [
                {"key": "Mean difference", "value": 2.5, "unit": "meters"},
                {"key": "Median difference", "value": 2.0, "unit": "meters"},
                {"key": "StdDev of difference", "value": 0.5, "unit": "meters"},
            ],
        }
        summary = summarize_metrics(parsed)
        self.assertEqual(summary["mean_difference_m"], 2.5)
        self.assertEqual(summary["median_difference_m"], 2.0)
        self.assertEqual(summary["stddev_difference_m"], 0.5)
        self.assertEqual(summary["metric_count"], 3)

    def test_receipt_summary_contains_no_raw_item_or_qa_data(self):
        summary = summarize_receipt({
            "experiment": "E583",
            "decision": "PARTIAL_OR_INCOMPLETE_QA_COHORT",
            "items": [{
                "id": "item-1",
                "decision": "QA_KEY_VALUE_SUMMARY",
                "metrics": {"mean_difference_m": 2.5},
                "sha256": "abc",
                "raw_qa_text_stored": False,
            }],
        })
        encoded = json.dumps(summary)
        self.assertIn("item-1", encoded)
        self.assertNotIn("raw_text", encoded)
        self.assertNotIn("coordinates", encoded)
        self.assertFalse(summary["raw_item_json_stored"])
        self.assertFalse(summary["raw_qa_text_stored"])


if __name__ == "__main__":
    unittest.main()
