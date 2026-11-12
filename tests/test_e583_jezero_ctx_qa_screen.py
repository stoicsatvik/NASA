import unittest
from unittest.mock import patch

from experiments.e583_jezero_ctx_qa_screen import (
    COLLECTION,
    ITEM_ID,
    JEZERO_BBOX,
    ProbeError,
    audit_item,
    build_bbox_payload,
    build_pinned_payload,
    merge_features,
    parse_features,
    summarize_receipt,
)


class E583Tests(unittest.TestCase):
    def _feature(self, item_id=ITEM_ID, qa_href="https://astrogeo-ard.s3-us-west-2.amazonaws.com/qa.txt"):
        return {
            "type": "Feature",
            "id": item_id,
            "collection": COLLECTION,
            "properties": {"datetime": "2023-04-18T12:00:00Z"},
            "assets": {"qa_metrics": {"href": qa_href}, "dtm": {"href": "https://astrogeo-ard.s3-us-west-2.amazonaws.com/dtm.tif"}},
        }

    def test_bbox_and_pinned_queries_are_frozen(self):
        self.assertEqual(build_bbox_payload(), {"collections": [COLLECTION], "bbox": JEZERO_BBOX, "limit": 10})
        self.assertEqual(build_pinned_payload(), {"collections": [COLLECTION], "ids": [ITEM_ID], "limit": 1})

    def test_parse_features_requires_collection_and_stable_ids(self):
        parsed = parse_features({"type": "FeatureCollection", "features": [self._feature()]}, max_items=10)
        self.assertEqual(parsed[0]["id"], ITEM_ID)
        self.assertEqual(parsed[0]["datetime"], "2023-04-18T12:00:00Z")
        self.assertIn("qa_metrics", parsed[0]["assets"])
        with self.assertRaises(ProbeError):
            parse_features({"type": "FeatureCollection", "features": [self._feature(item_id="")]}, max_items=10)
        wrong = self._feature()
        wrong["collection"] = "other"
        with self.assertRaises(ProbeError):
            parse_features({"type": "FeatureCollection", "features": [wrong]}, max_items=10)

    def test_parse_features_rejects_duplicate_and_over_cap_items(self):
        feature = self._feature()
        with self.assertRaises(ProbeError):
            parse_features({"type": "FeatureCollection", "features": [feature, feature]}, max_items=10)
        with self.assertRaises(ProbeError):
            parse_features({"type": "FeatureCollection", "features": [feature, self._feature("OTHER") ]}, max_items=1)

    def test_merge_deduplicates_and_caps(self):
        a = {"id": "A"}
        b = {"id": "B"}
        self.assertEqual(merge_features([a], [a, b]), [a, b])
        self.assertEqual(merge_features([a, b], cap=1), [a])

    def test_audit_item_parses_metrics_without_retaining_text(self):
        item = {"id": ITEM_ID, "datetime": "2023-04-18T12:00:00Z", "assets": {"qa_metrics": {"href": "https://astrogeo-ard.s3-us-west-2.amazonaws.com/qa.txt"}}}
        response = {"status": 200, "bytes_read": 22, "declared_bytes": 22, "too_large": False, "final_url": item["assets"]["qa_metrics"]["href"], "payload": b"Mean difference: 2.5 m\n"}
        with patch("experiments.e583_jezero_ctx_qa_screen.fetch_bounded", return_value=response):
            result = audit_item(item)
        self.assertEqual(result["decision"], "QA_KEY_VALUE_SUMMARY")
        self.assertEqual(result["metrics"]["mean difference"], {"value": 2.5, "unit": "m"})
        self.assertFalse(result["raw_qa_text_stored"])
        self.assertNotIn("payload", result)

    def test_audit_item_fails_closed_for_missing_or_untrusted_asset(self):
        self.assertEqual(audit_item({"id": "A", "assets": {}})["decision"], "QA_ASSET_MISSING")
        item = {"id": "A", "assets": {"qa_metrics": {"href": "https://evil.example/qa.txt"}}}
        self.assertEqual(audit_item(item)["decision"], "QA_ASSET_URL_NOT_ALLOWLISTED")

    def test_receipt_summary_is_null_safe_and_redacted(self):
        result = summarize_receipt({"decision": "PARTIAL_OR_INCOMPLETE_QA_SCREEN"})
        self.assertEqual(result["item_count"], 0)
        self.assertEqual(result["items"], [])
        self.assertFalse(result["raw_coordinates_stored"])
        self.assertFalse(result["raw_mola_rows_stored"])


if __name__ == "__main__":
    unittest.main()
