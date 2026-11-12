import json
import unittest
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from experiments import e590_grand_falls_2023_2024_probe as e590


def response(status, payload=b"", headers=None, final_url=None):
    return {
        "status": status,
        "payload": payload,
        "headers": headers or {},
        "final_url": final_url or e590.PARENT_ITEM_URL,
    }


class E590Tests(unittest.TestCase):
    def test_parent_child_and_catalog_identifiers_are_pinned(self):
        self.assertEqual(e590.PARENT_ITEM_ID, "677ee6bed34e760b392c4aa3")
        self.assertEqual(e590.CATALOG_RECORD_ID, "67bf94acd34e8876fcbfc91b")
        self.assertEqual(e590.DOI, "10.5066/P13HPPYM")
        parent_query = parse_qs(urlsplit(e590.PARENT_ITEM_URL).query)
        self.assertEqual(parent_query["format"], ["json"])
        self.assertEqual(parent_query["fields"], [e590.ITEM_FIELDS])
        child_query = parse_qs(urlsplit(e590.CHILDREN_URL).query)
        self.assertEqual(child_query["filter"], [f"parentId={e590.PARENT_ITEM_ID}"])
        self.assertEqual(child_query["format"], ["json"])

    def test_file_summary_redacts_signed_query_values_and_accepts_explicit_file_url(self):
        record = {
            "name": "field-data.csv",
            "size": 123,
            "url": "https://www.sciencebase.gov/catalog/file/get/abc?sig=secret&expires=123",
        }
        summary = e590._safe_file_record(record)
        rendered = json.dumps(summary)
        self.assertEqual(summary["name"], "field-data.csv")
        self.assertEqual(summary["size_bytes"], 123)
        self.assertEqual(e590._download_uri(record), record["url"])
        self.assertNotIn("secret", rendered)
        self.assertNotIn('"123"', rendered)
        self.assertFalse(summary["download_uri"]["query_values_stored"])

    def test_extract_file_records_reads_top_level_and_facets(self):
        item = {
            "files": [{"name": "top.csv", "size": 10, "url": "https://www.sciencebase.gov/catalog/file/get/a"}],
            "facets": [
                {"name": "data", "files": [{"name": "facet.zip", "size": 20, "url": "https://www.sciencebase.gov/catalog/file/get/b"}]}
            ],
        }
        records = e590._extract_file_records(item, "item-1")
        self.assertEqual({r["name"] for r in records}, {"top.csv", "facet.zip"})
        self.assertTrue(all(r["_source_item_id"] == "item-1" for r in records))

    def test_metadata_failures_are_preserved_without_file_claim(self):
        with patch.object(e590, "fetch_bounded", side_effect=[
            response(503, b"unavailable"),
            response(503, b"unavailable"),
            response(503, b"unavailable"),
        ]):
            result = e590.audit()
        self.assertEqual(result["decision"], "METADATA_UNAVAILABLE")
        self.assertEqual(result["parent_metadata_http_status"], 503)
        self.assertEqual(result["catalog_record_metadata_http_status"], 503)
        self.assertIsNone(result["file_count"] if result["file_count"] is None else None)
        self.assertFalse(result["credentials_used"])

    def test_no_small_candidate_does_not_trigger_file_download(self):
        parent = json.dumps({"title": "Grand Falls", "files": []}).encode()
        children = json.dumps({"items": [{"id": e590.CATALOG_RECORD_ID, "title": "Sediment Transport Data"}]}).encode()
        catalog = json.dumps({
            "title": "Grand Falls",
            "facets": [{"files": [
                {"name": "large.zip", "size": 9_000_000, "url": "https://www.sciencebase.gov/catalog/file/get/large"},
                {"name": "preview.csv", "size": 100, "url": "https://www.sciencebase.gov/catalog/item/preview"},
            ]}],
        }).encode()
        with patch.object(e590, "fetch_bounded", side_effect=[
            response(200, parent),
            response(200, children),
            response(200, catalog),
        ]) as fetch:
            result = e590.audit()
        self.assertEqual(result["decision"], "NO_SMALL_METADATA_LINKED_DELIMITED_FILE")
        self.assertEqual(result["child_count"], 1)
        self.assertEqual(result["file_count"], 2)
        self.assertEqual(fetch.call_count, 3)

    def test_child_catalog_csv_is_range_checked_and_aggregated(self):
        payload = (
            b"timestamp,wind_speed_mph,sediment_flux_g_m2_s\n"
            b"2023-07-07T00:00:00Z,5,0.2\n"
            b"2023-07-07T00:00:10Z,7,0.4\n"
        )
        size = len(payload)
        parent = json.dumps({"title": "Grand Falls", "files": []}).encode()
        children = json.dumps({"items": [{"id": e590.CATALOG_RECORD_ID, "title": "Sediment Transport Data"}]}).encode()
        catalog = json.dumps({
            "title": "Sediment Transport Data",
            "facets": [{"files": [{
                "name": "field-data.csv",
                "size": size,
                "url": "https://www.sciencebase.gov/catalog/file/get/field-data.csv",
            }]}],
        }).encode()
        range_payload = payload[:min(e590.MAX_HEADER_BYTES, size)]
        side_effects = [
            response(200, parent),
            response(200, children),
            response(200, catalog),
            response(
                206,
                range_payload,
                {"Content-Range": f"bytes 0-{len(range_payload)-1}/{size}", "Content-Type": "text/csv"},
                "https://www.sciencebase.gov/catalog/file/get/field-data.csv",
            ),
            response(
                200,
                payload,
                {"Content-Type": "text/csv"},
                "https://www.sciencebase.gov/catalog/file/get/field-data.csv",
            ),
        ]
        with patch.object(e590, "fetch_bounded", side_effect=side_effects) as fetch:
            result = e590.audit()
        self.assertEqual(result["decision"], "SMALL_PUBLIC_FIELD_DATA_FILE_ACQUIRED_AND_PROFILED")
        self.assertTrue(result["catalog_record_id_in_parent_children"])
        self.assertEqual(result["data_sample"]["summary"]["data_summary"]["row_count"], 2)
        self.assertEqual(result["data_sample"]["summary"]["data_summary"]["numeric_summaries"]["wind_speed_mph"]["mean"], 6.0)
        self.assertEqual(fetch.call_count, 5)
        self.assertFalse(result["raw_values_stored"])
        self.assertNotIn("rows", result["data_sample"]["summary"]["data_summary"])

    def test_invalid_range_stops_before_full_download(self):
        parent = json.dumps({"title": "Grand Falls", "files": []}).encode()
        children = json.dumps({"items": []}).encode()
        catalog = json.dumps({
            "title": "Grand Falls",
            "files": [{
                "name": "field-data.csv",
                "size": 40,
                "url": "https://www.sciencebase.gov/catalog/file/get/field-data.csv",
            }],
        }).encode()
        side_effects = [
            response(200, parent),
            response(200, children),
            response(200, catalog),
            response(206, b"head", {"Content-Range": "bytes 1-4/40"}),
        ]
        with patch.object(e590, "fetch_bounded", side_effect=side_effects) as fetch:
            result = e590.audit()
        self.assertEqual(result["decision"], "BOUNDED_RANGE_NOT_CONFIRMED")
        self.assertEqual(fetch.call_count, 4)
        self.assertIsNone(result["data_sample"])

    def test_transport_errors_are_fail_closed(self):
        with patch.object(e590, "fetch_bounded", side_effect=TimeoutError("timed out")):
            result = e590.audit()
        self.assertEqual(result["decision"], "ACQUISITION_ERROR")
        self.assertEqual(result["error_type"], "TimeoutError")
        self.assertFalse(result["credentials_used"])
        self.assertFalse(result["raw_values_stored"])


if __name__ == "__main__":
    unittest.main()
