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

    def test_file_summary_redacts_signed_query_values(self):
        record = {
            "name": "field-data.csv",
            "size": 123,
            "url": "https://www.sciencebase.gov/catalog/file/get/abc?sig=secret&expires=123",
        }
        summary = e590._safe_file_record(record)
        rendered = json.dumps(summary)
        self.assertEqual(e590._download_uri(record), record["url"])
        self.assertNotIn("secret", rendered)
        self.assertNotIn('"123"', rendered)
        self.assertFalse(summary["download_uri"]["query_values_stored"])

    def test_candidate_prefers_explicit_file_endpoint_over_page_url(self):
        records = [
            {"name": "small-page.csv", "size": 1_091_813, "url": "https://sciencebase.usgs.gov/catalog/file/get/a"},
            {"name": "large-direct.csv", "size": 67_050_032, "url": "https://www.sciencebase.gov/catalog/file/get/b?f=large-direct.csv"},
        ]
        self.assertEqual(e590._choose_candidate(records)["name"], "large-direct.csv")

    def test_extract_file_records_reads_top_level_and_facets(self):
        item = {
            "files": [{"name": "top.csv", "size": 10, "url": "https://www.sciencebase.gov/catalog/file/get/a"}],
            "facets": [{"name": "data", "files": [{"name": "facet.zip", "size": 20, "url": "https://www.sciencebase.gov/catalog/file/get/b"}]}],
        }
        records = e590._extract_file_records(item, "item-1")
        self.assertEqual({r["name"] for r in records}, {"top.csv", "facet.zip"})
        self.assertTrue(all(r["_source_item_id"] == "item-1" for r in records))

    def test_metadata_failures_are_preserved(self):
        with patch.object(e590, "fetch_bounded", side_effect=[
            response(503), response(503), response(503)
        ]):
            result = e590.audit()
        self.assertEqual(result["decision"], "METADATA_UNAVAILABLE")
        self.assertEqual(result["parent_metadata_http_status"], 503)
        self.assertEqual(result["catalog_record_metadata_http_status"], 503)
        self.assertFalse(result["credentials_used"])

    def test_no_supported_file_does_not_trigger_range_request(self):
        parent = json.dumps({"title": "Grand Falls", "files": []}).encode()
        children = json.dumps({"items": [{"id": e590.CATALOG_RECORD_ID, "title": "Sediment Transport Data"}]}).encode()
        catalog = json.dumps({
            "title": "Grand Falls",
            "files": [
                {"name": "large.csv", "size": 200_000_000, "url": "https://www.sciencebase.gov/catalog/file/get/large?f=large.csv"},
                {"name": "metadata.xml", "size": 1000, "url": "https://www.sciencebase.gov/catalog/file/get/meta?f=meta.xml"},
            ],
        }).encode()
        with patch.object(e590, "fetch_bounded", side_effect=[
            response(200, parent), response(200, children), response(200, catalog)
        ]) as fetch:
            result = e590.audit()
        self.assertEqual(result["decision"], "NO_SUPPORTED_METADATA_LINKED_CSV")
        self.assertEqual(fetch.call_count, 3)

    def test_csv_range_sample_is_profiled_without_raw_rows(self):
        payload = b"timestamp,wind_speed_mph,sediment_flux_g_m2_s\n2023-07-07T00:00:00Z,5,0.2\n2023-07-07T00:00:10Z,7,0.4\n"
        size = len(payload)
        parent = json.dumps({"title": "Grand Falls", "files": []}).encode()
        children = json.dumps({"items": [{"id": e590.CATALOG_RECORD_ID, "title": "Sediment Transport Data"}]}).encode()
        catalog = json.dumps({
            "title": "Sediment Transport Data",
            "facets": [{"files": [{
                "name": "field-data.csv", "size": size,
                "url": "https://www.sciencebase.gov/catalog/file/get/field-data.csv?f=field-data.csv",
            }]}],
        }).encode()
        side_effects = [
            response(200, parent),
            response(200, children),
            response(200, catalog),
            response(206, payload, {
                "Content-Range": f"bytes 0-{size-1}/{size}",
                "Content-Type": "text/csv",
            }, "https://www.sciencebase.gov/catalog/file/get/field-data.csv?f=field-data.csv"),
        ]
        with patch.object(e590, "fetch_bounded", side_effect=side_effects) as fetch:
            result = e590.audit()
        self.assertEqual(result["decision"], "PUBLIC_CSV_PREFIX_SAMPLE_ACQUIRED_AND_PROFILED")
        self.assertEqual(result["data_sample"]["summary"]["data_summary"]["row_count"], 2)
        self.assertEqual(result["data_sample"]["summary"]["data_summary"]["numeric_summaries"]["wind_speed_mph"]["mean"], 6.0)
        self.assertEqual(fetch.call_count, 4)
        self.assertFalse(result["raw_values_stored"])
        self.assertNotIn("rows", result["data_sample"]["summary"]["data_summary"])

    def test_large_csv_prefix_is_bounded_and_marked_partial(self):
        payload = b"timestamp,wind_speed_mph\n2023-07-07,5\n2023-07-08,7\n2023-07-09,8\n"
        with patch.object(e590, "MAX_SAMPLE_BYTES", 48):
            prefix = payload[:48]
            self.assertTrue(e590._complete_csv_prefix(prefix).endswith(b"\n"))
            self.assertLessEqual(len(prefix), 48)

    def test_html_or_mismatched_range_is_rejected(self):
        payload = b"<html>access denied</html>"
        size = 100
        parent = json.dumps({"title": "Grand Falls", "files": []}).encode()
        children = json.dumps({"items": []}).encode()
        catalog = json.dumps({"title": "Grand Falls", "files": [{
            "name": "field.csv", "size": size,
            "url": "https://www.sciencebase.gov/catalog/file/get/field.csv?f=field.csv",
        }]}).encode()
        side_effects = [
            response(200, parent), response(200, children), response(200, catalog),
            response(206, payload, {"Content-Range": f"bytes 0-{len(payload)-1}/4255", "Content-Type": "text/html"}),
        ]
        with patch.object(e590, "fetch_bounded", side_effect=side_effects) as fetch:
            result = e590.audit()
        self.assertEqual(result["decision"], "BOUNDED_RANGE_NOT_CONFIRMED")
        self.assertTrue(result["range_probe"]["html_response"])
        self.assertEqual(fetch.call_count, 4)

    def test_transport_errors_are_fail_closed(self):
        with patch.object(e590, "fetch_bounded", side_effect=TimeoutError("timed out")):
            result = e590.audit()
        self.assertEqual(result["decision"], "ACQUISITION_ERROR")
        self.assertEqual(result["error_type"], "TimeoutError")
        self.assertFalse(result["credentials_used"])
        self.assertFalse(result["raw_values_stored"])


if __name__ == "__main__":
    unittest.main()
