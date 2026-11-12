import json
import unittest

from experiments.e582_ctx_qa_mola_audit import (
    COLLECTION,
    ITEM_ID,
    ProbeError,
    build_search_payload,
    parse_item,
    parse_mola_csv,
    parse_qa_metrics,
    safe_url_summary,
    summarize_receipt,
    validate_public_url,
)


class E582Tests(unittest.TestCase):
    def test_search_payload_pins_exact_collection_and_item(self):
        self.assertEqual(
            build_search_payload(),
            {"collections": [COLLECTION], "ids": [ITEM_ID], "limit": 1},
        )

    def test_public_url_allowlist_and_signed_query_redaction(self):
        validate_public_url("https://stac.astrogeology.usgs.gov/api/search")
        validate_public_url("https://astrogeo-ard.s3-us-west-2.amazonaws.com/qa.txt")
        with self.assertRaises(ProbeError):
            validate_public_url("https://evil.example/qa.txt")
        with self.assertRaises(ProbeError):
            validate_public_url("https://astrogeo-ard.s3-us-west-2.amazonaws.com:8443/qa.txt")
        summary = safe_url_summary(
            "https://astrogeo-ard.s3.amazonaws.com/qa.txt?X-Amz-Signature=secret"
        )
        self.assertEqual(summary["query_key_names"], ["x-amz-signature"])
        self.assertNotIn("secret", json.dumps(summary))
        self.assertFalse(summary["query_values_stored"])

    def test_item_parser_requires_the_pinned_feature_and_returns_only_asset_map(self):
        document = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "id": ITEM_ID,
                "collection": COLLECTION,
                "properties": {"datetime": "2023-04-18T12:00:00Z"},
                "assets": {
                    "qa_metrics": {"href": "https://astrogeo-ard.s3-us-west-2.amazonaws.com/qa.txt"},
                    "mola_csv": {"href": "https://astrogeo-ard.s3-us-west-2.amazonaws.com/control.csv"},
                },
            }],
        }
        summary, assets = parse_item(document)
        self.assertEqual(summary["id"], ITEM_ID)
        self.assertEqual(summary["asset_keys"], ["mola_csv", "qa_metrics"])
        self.assertIn("qa_metrics", assets)
        self.assertIn("mola_csv", assets)
        with self.assertRaises(ProbeError):
            parse_item({
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "id": "OTHER",
                    "collection": COLLECTION,
                    "assets": {},
                }],
            })

    def test_qa_parser_keeps_only_bounded_numeric_key_value_metrics(self):
        payload = (
            "Mean difference: -2.5 m\n"
            "Median difference = 1.25 meters\n"
            "Comment: values are descriptive only\n"
            "non-metric free text\n"
        ).encode()
        result = parse_qa_metrics(payload)
        self.assertEqual(result["decision"], "QA_KEY_VALUE_SUMMARY")
        self.assertEqual(result["metric_count"], 2)
        self.assertEqual(result["unparsed_nonempty_lines"], 2)
        self.assertEqual(result["metrics"][0], {"key": "Mean difference", "value": -2.5, "unit": "m"})
        self.assertFalse(result["raw_text_stored"])
        self.assertNotIn("payload", result)

    def test_qa_parser_fails_closed_on_non_utf8(self):
        result = parse_qa_metrics(b"\xff\xfe\xfa")
        self.assertEqual(result["decision"], "QA_NOT_UTF8_TEXT")
        self.assertFalse(result["raw_text_stored"])

    def test_mola_csv_parser_reports_schema_and_aggregates_without_rows(self):
        payload = (
            "point_id,latitude,longitude,elevation_m\n"
            "A,17.1,77.2,-2.0\n"
            "B,17.3,77.4,-4.0\n"
            "C,17.5,77.6,-6.0\n"
        ).encode()
        result = parse_mola_csv(payload)
        self.assertEqual(result["decision"], "MOLA_CSV_SCHEMA_AND_AGGREGATES")
        self.assertEqual(result["row_count"], 3)
        self.assertEqual(result["columns"], ["point_id", "latitude", "longitude", "elevation_m"])
        self.assertEqual(result["numeric_summaries"]["latitude"]["min"], 17.1)
        self.assertEqual(result["numeric_summaries"]["longitude"]["max"], 77.6)
        self.assertEqual(result["numeric_summaries"]["elevation_m"]["mean"], -4.0)
        self.assertFalse(result["raw_rows_stored"])
        self.assertNotIn("rows", result)

    def test_mola_csv_row_cap_is_explicit(self):
        payload = b"id,z\n1,2\n2,4\n3,6\n"
        result = parse_mola_csv(payload, max_rows=2)
        self.assertEqual(result["row_count"], 2)
        self.assertTrue(result["truncated_at_row_cap"])
        self.assertFalse(result["raw_rows_stored"])

    def test_empty_and_headerless_csv_fail_closed(self):
        self.assertEqual(parse_mola_csv(b"")["decision"], "MOLA_CSV_EMPTY")
        self.assertEqual(parse_mola_csv(b"\n \n")["decision"], "MOLA_CSV_EMPTY")

    def test_receipt_summary_never_claims_raw_data_retention(self):
        summary = summarize_receipt({
            "experiment": "E582",
            "decision": "ACQUISITION_OR_PARSING_ERROR",
        })
        self.assertFalse(summary["raw_item_json_stored"])
        self.assertFalse(summary["raw_qa_text_stored"])
        self.assertFalse(summary["raw_mola_csv_stored"])
        self.assertFalse(summary["raw_coordinates_stored"])
        self.assertIsNone(summary["item_id"])


if __name__ == "__main__":
    unittest.main()
