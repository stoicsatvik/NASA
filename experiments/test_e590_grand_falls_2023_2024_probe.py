import json
import unittest
from unittest.mock import patch

from experiments import e590_grand_falls_2023_2024_probe as e590


def response(status, payload=b"", headers=None, final_url=None):
    return {
        "status": status,
        "payload": payload,
        "headers": headers or {},
        "final_url": final_url or e590.ITEM_URL,
    }


class E590Tests(unittest.TestCase):
    def test_item_and_projection_are_pinned(self):
        from urllib.parse import parse_qs, urlsplit
        query = parse_qs(urlsplit(e590.ITEM_URL).query)
        self.assertIn(e590.ITEM_ID, e590.ITEM_URL)
        self.assertEqual(query["format"], ["json"])
        self.assertEqual(query["fields"], [e590.ITEM_FIELDS])
        self.assertEqual(e590.DOI, "10.5066/P13HPPYM")

    def test_file_summary_redacts_signed_query_values(self):
        record = {
            "name": "field-data.csv",
            "size": 123,
            "downloadUri": "https://prod-is-usgs-sb-prod-content.s3.amazonaws.com/x.csv?X-Amz-Signature=secret&Expires=123",
        }
        summary = e590._safe_file_record(record)
        rendered = json.dumps(summary)
        self.assertEqual(summary["name"], "field-data.csv")
        self.assertEqual(summary["size_bytes"], 123)
        self.assertNotIn("secret", rendered)
        self.assertNotIn('"123"', rendered)
        self.assertFalse(summary["download_uri"]["query_values_stored"])

    def test_metadata_http_failure_is_preserved_without_file_claim(self):
        with patch.object(e590, "fetch_bounded", return_value=response(503, b"unavailable")):
            result = e590.audit()
        self.assertEqual(result["decision"], "METADATA_HTTP_ERROR")
        self.assertEqual(result["metadata_http_status"], 503)
        self.assertIsNone(result["file_count"])
        self.assertIsNone(result["data_sample"])
        self.assertFalse(result["credentials_used"])

    def test_missing_or_oversized_files_do_not_trigger_download(self):
        metadata = json.dumps({
            "title": "Grand Falls",
            "files": [
                {"name": "large.zip", "size": 9_000_000, "downloadUri": "https://sciencebase.gov/file"},
                {"name": "preview.csv", "size": 100, "url": "https://sciencebase.gov/preview"},
            ],
        }).encode()
        with patch.object(e590, "fetch_bounded", return_value=response(200, metadata)) as fetch:
            result = e590.audit()
        self.assertEqual(result["decision"], "NO_SMALL_METADATA_LINKED_DELIMITED_FILE")
        self.assertEqual(result["file_count"], 2)
        self.assertEqual(fetch.call_count, 1)

    def test_one_small_csv_is_range_checked_and_aggregated(self):
        payload = (
            b"timestamp,wind_speed_mph,sediment_flux_g_m2_s\n"
            b"2023-07-07T00:00:00Z,5,0.2\n"
            b"2023-07-07T00:00:10Z,7,0.4\n"
        )
        size = len(payload)
        metadata = json.dumps({
            "title": "Grand Falls",
            "files": [{
                "name": "field-data.csv",
                "size": size,
                "downloadUri": "https://prod-is-usgs-sb-prod-content.s3.amazonaws.com/field-data.csv",
            }],
        }).encode()
        range_payload = payload[:min(e590.MAX_HEADER_BYTES, size)]
        side_effects = [
            response(200, metadata, final_url=e590.ITEM_URL),
            response(
                206,
                range_payload,
                {"Content-Range": f"bytes 0-{len(range_payload)-1}/{size}", "Content-Type": "text/csv"},
                "https://prod-is-usgs-sb-prod-content.s3.amazonaws.com/field-data.csv",
            ),
            response(
                200,
                payload,
                {"Content-Type": "text/csv"},
                "https://prod-is-usgs-sb-prod-content.s3.amazonaws.com/field-data.csv",
            ),
        ]
        with patch.object(e590, "fetch_bounded", side_effect=side_effects) as fetch:
            result = e590.audit()
        self.assertEqual(result["decision"], "SMALL_PUBLIC_FIELD_DATA_FILE_ACQUIRED_AND_PROFILED")
        self.assertEqual(result["data_sample"]["summary"]["data_summary"]["row_count"], 2)
        self.assertEqual(result["data_sample"]["summary"]["data_summary"]["numeric_summaries"]["wind_speed_mph"]["mean"], 6.0)
        self.assertEqual(fetch.call_count, 3)
        self.assertFalse(result["raw_values_stored"])
        self.assertNotIn("rows", result["data_sample"]["summary"]["data_summary"])

    def test_invalid_range_stops_before_full_download(self):
        payload = b"timestamp,wind_speed\n2023-07-07,5\n"
        metadata = json.dumps({
            "title": "Grand Falls",
            "files": [{
                "name": "field-data.csv",
                "size": len(payload),
                "downloadUri": "https://prod-is-usgs-sb-prod-content.s3.amazonaws.com/field-data.csv",
            }],
        }).encode()
        side_effects = [
            response(200, metadata),
            response(206, payload[:4], {"Content-Range": f"bytes 1-4/{len(payload)}"}),
        ]
        with patch.object(e590, "fetch_bounded", side_effect=side_effects) as fetch:
            result = e590.audit()
        self.assertEqual(result["decision"], "BOUNDED_RANGE_NOT_CONFIRMED")
        self.assertEqual(fetch.call_count, 2)
        self.assertIsNone(result["data_sample"])

    def test_null_and_transport_errors_are_fail_closed(self):
        with patch.object(e590, "fetch_bounded", side_effect=TimeoutError("timed out")):
            result = e590.audit()
        self.assertEqual(result["decision"], "ACQUISITION_ERROR")
        self.assertEqual(result["error_type"], "TimeoutError")
        self.assertFalse(result["credentials_used"])
        self.assertFalse(result["raw_values_stored"])
        self.assertNotIn("url", result)


if __name__ == "__main__":
    unittest.main()
