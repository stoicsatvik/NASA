import json
import unittest
from unittest.mock import patch

from experiments.e580_stac_search_probe import (
    BBOX,
    COLLECTION,
    MAX_RANGE_BYTES,
    ProbeError,
    build_search_payload,
    parse_feature_collection,
    range_probe,
    safe_url_summary,
    summarize_receipt,
    validate_public_url,
)


class E580Tests(unittest.TestCase):
    def test_search_payload_uses_pinned_collection_and_jezero_bbox(self):
        self.assertEqual(
            build_search_payload(),
            {
                "collections": [COLLECTION],
                "bbox": BBOX,
                "limit": 1,
            },
        )

    def test_safe_url_summary_redacts_query_values(self):
        summary = safe_url_summary(
            "https://astrogeo-ard.s3.amazonaws.com/a.tif?X-Amz-Signature=secret"
        )
        self.assertEqual(summary["host"], "astrogeo-ard.s3.amazonaws.com")
        self.assertEqual(summary["query_key_names"], ["x-amz-signature"])
        self.assertNotIn("secret", str(summary))

    def test_public_host_allowlist_accepts_official_stac_and_asset_hosts(self):
        validate_public_url("https://stac.astrogeology.usgs.gov/api/search")
        validate_public_url("https://astrogeo-ard.s3-us-west-2.amazonaws.com/a.tif")

    def test_public_host_allowlist_rejects_unknown_host(self):
        with self.assertRaises(ProbeError):
            validate_public_url("https://evil.example/a.tif")

    def test_parse_item_metadata_and_dtm_asset(self):
        fixture = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "id": "CTX_TEST_001",
                "collection": COLLECTION,
                "bbox": [77.0, 18.0, 78.0, 19.0],
                "geometry": {"type": "Polygon", "coordinates": []},
                "properties": {
                    "datetime": "2024-01-01T00:00:00Z",
                    "proj:epsg": 49900,
                    "proj:shape": [100, 100],
                    "proj:transform": [1, 0, 0, 0, -1, 0],
                    "proj:wkt2": "fixture",
                },
                "assets": {
                    "dtm": {
                        "href": "https://astrogeo-ard.s3-us-west-2.amazonaws.com/a.tif",
                        "type": "image/tiff; application=geotiff",
                    },
                    "qa_metrics": {"href": "https://astrogeo-ard.s3-us-west-2.amazonaws.com/qa.json"},
                },
            }],
        }
        result = parse_feature_collection(json.dumps(fixture).encode("utf-8"))
        self.assertEqual(result["decision"], "ITEM_METADATA_ACQUIRED")
        item = result["items"][0]
        self.assertEqual(item["id"], "CTX_TEST_001")
        self.assertEqual(item["geometry_type"], "Polygon")
        self.assertEqual(item["proj_epsg"], 49900)
        self.assertEqual(item["asset_keys"], ["dtm", "qa_metrics"])
        self.assertTrue(item["dtm_href_usable"])
        self.assertTrue(item["proj_wkt2_present"])

    def test_empty_search_is_not_a_scientific_null(self):
        result = parse_feature_collection(
            b'{"type":"FeatureCollection","features":[]}'
        )
        self.assertEqual(result["decision"], "NO_ITEMS_MATCHED")
        self.assertEqual(result["matched"], 0)

    def test_parser_rejects_non_feature_collection(self):
        with self.assertRaises(ProbeError):
            parse_feature_collection(b'{"type":"Feature","features":[]}')

    def test_range_probe_requires_http_206_and_zero_based_content_range(self):
        response = {
            "status": 206,
            "headers": {
                "Content-Range": f"bytes 0-{MAX_RANGE_BYTES - 1}/100000",
                "Content-Type": "image/tiff",
            },
            "bytes_read": MAX_RANGE_BYTES,
            "payload": b"x" * MAX_RANGE_BYTES,
            "final_url": "https://astrogeo-ard.s3-us-west-2.amazonaws.com/a.tif",
            "too_large": False,
        }
        with patch("experiments.e580_stac_search_probe.fetch_bounded", return_value=response):
            result = range_probe("https://astrogeo-ard.s3-us-west-2.amazonaws.com/a.tif")
        self.assertTrue(result["range_verified"])
        self.assertEqual(result["status"], 206)
        self.assertEqual(result["bytes_read"], MAX_RANGE_BYTES)
        self.assertNotIn("query_values_stored", result["url"])

    def test_receipt_summary_is_null_safe_and_never_claims_pixels(self):
        summary = summarize_receipt({"experiment": "E580", "decision": "ACQUISITION_ERROR"})
        self.assertFalse(summary["credentials_used"])
        self.assertFalse(summary["sample_pixels_acquired"])
        self.assertFalse(summary["raw_item_json_stored"])
        self.assertIsNone(summary["item_id"])


if __name__ == "__main__":
    unittest.main()
