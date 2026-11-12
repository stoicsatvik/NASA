import json
import unittest
from unittest.mock import patch

from experiments import e590_grand_falls_2023_2024_probe as e590


def response(status, payload=b"", headers=None, final_url=None):
    return {
        "status": status,
        "payload": payload,
        "headers": headers or {},
        "final_url": final_url or e590.PARENT_ITEM_URL,
    }


class FakeResponse:
    def __init__(self, payload, headers, url):
        self.payload = payload
        self.headers = headers
        self.url = url
        self.status = 200
        self.read_limit = None

    def read(self, limit):
        self.read_limit = limit
        return self.payload[:limit]

    def geturl(self):
        return self.url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeOpener:
    def __init__(self, response):
        self.response = response

    def open(self, request, timeout):
        return self.response


class E590Tests(unittest.TestCase):
    def test_parent_child_and_catalog_identifiers_are_pinned(self):
        self.assertEqual(e590.PARENT_ITEM_ID, "677ee6bed34e760b392c4aa3")
        self.assertEqual(e590.CATALOG_RECORD_ID, "67bf94acd34e8876fcbfc91b")
        self.assertEqual(e590.DOI, "10.5066/P13HPPYM")

    def test_file_summary_redacts_signed_query_values(self):
        record = {
            "name": "field-data.csv", "size": 123,
            "url": "https://www.sciencebase.gov/catalog/file/get/abc?sig=secret&expires=123",
        }
        summary = e590._safe_file_record(record)
        rendered = json.dumps(summary)
        self.assertEqual(e590._download_uri(record), record["url"])
        self.assertNotIn("secret", rendered)
        self.assertNotIn('"123"', rendered)
        self.assertFalse(summary["download_uri"]["query_values_stored"])

    def test_candidate_prefers_explicit_file_endpoint(self):
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

    def test_sample_classifier_accepts_range_or_bounded_stream_prefix(self):
        payload = b"x" * 50
        self.assertEqual(e590.classify_sample_response(206, {
            "Content-Type": "text/csv", "Content-Range": "bytes 0-49/100"
        }, payload, 100, 50), "http_range")
        self.assertEqual(e590.classify_sample_response(200, {
            "Content-Type": "text/csv", "Content-Length": "100"
        }, payload, 100, 50), "bounded_stream_prefix")
        self.assertIsNone(e590.classify_sample_response(200, {
            "Content-Type": "text/html", "Content-Length": "100"
        }, payload, 100, 50))

    def test_prefix_reader_never_reads_more_than_limit(self):
        fake = FakeResponse(b"x" * 1000, {"Content-Type": "text/csv", "Content-Length": "1000"},
                             "https://www.sciencebase.gov/catalog/file/get/a?f=a")
        with patch.object(e590.urllib.request, "build_opener", return_value=FakeOpener(fake)):
            result = e590.fetch_prefix_bounded(fake.url, limit=50)
        self.assertEqual(len(result["payload"]), 50)
        self.assertEqual(fake.read_limit, 50)

    def test_metadata_failures_are_preserved(self):
        with patch.object(e590, "fetch_bounded", side_effect=[response(503), response(503), response(503)]):
            result = e590.audit()
        self.assertEqual(result["decision"], "METADATA_UNAVAILABLE")
        self.assertEqual(result["parent_metadata_http_status"], 503)
        self.assertEqual(result["catalog_record_metadata_http_status"], 503)
        self.assertFalse(result["credentials_used"])

    def test_no_supported_file_does_not_trigger_sample_request(self):
        parent = json.dumps({"title": "Grand Falls", "files": []}).encode()
        children = json.dumps({"items": [{"id": e590.CATALOG_RECORD_ID, "title": "Sediment Transport Data"}]}).encode()
        catalog = json.dumps({"title": "Grand Falls", "files": [
            {"name": "large.csv", "size": 200_000_000, "url": "https://www.sciencebase.gov/catalog/file/get/large?f=large.csv"},
            {"name": "metadata.xml", "size": 1000, "url": "https://www.sciencebase.gov/catalog/file/get/meta?f=meta.xml"},
        ]}).encode()
        with patch.object(e590, "fetch_bounded", side_effect=[
            response(200, parent), response(200, children), response(200, catalog)
        ]) as fetch:
            result = e590.audit()
        self.assertEqual(result["decision"], "NO_SUPPORTED_METADATA_LINKED_CSV")
        self.assertEqual(fetch.call_count, 3)

    def test_csv_prefix_sample_is_profiled_without_raw_rows(self):
        payload = b"timestamp,wind_speed_mph,sediment_flux_g_m2_s\n2023-07-07T00:00:00Z,5,0.2\n2023-07-07T00:00:10Z,7,0.4\n"
        size = len(payload)
        parent = json.dumps({"title": "Grand Falls", "files": []}).encode()
        children = json.dumps({"items": [{"id": e590.CATALOG_RECORD_ID, "title": "Sediment Transport Data"}]}).encode()
        catalog = json.dumps({"title": "Sediment Transport Data", "facets": [{"files": [{
            "name": "field-data.csv", "size": size,
            "url": "https://www.sciencebase.gov/catalog/file/get/field-data.csv?f=field-data.csv",
        }]}]}).encode()
        with patch.object(e590, "fetch_bounded", side_effect=[
            response(200, parent), response(200, children), response(200, catalog)
        ]), patch.object(e590, "fetch_prefix_bounded", return_value=response(
            200, payload, {"Content-Type": "text/csv", "Content-Length": str(size)},
            "https://www.sciencebase.gov/catalog/file/get/field-data.csv?f=field-data.csv"
        )):
            result = e590.audit()
        self.assertEqual(result["decision"], "PUBLIC_CSV_PREFIX_SAMPLE_ACQUIRED_AND_PROFILED")
        self.assertEqual(result["data_sample"]["summary"]["data_summary"]["row_count"], 2)
        self.assertEqual(result["data_sample"]["summary"]["data_summary"]["numeric_summaries"]["wind_speed_mph"]["mean"], 6.0)
        self.assertFalse(result["raw_values_stored"])
        self.assertNotIn("rows", result["data_sample"]["summary"]["data_summary"])

    def test_html_or_mismatched_range_is_rejected(self):
        payload = b"<html>access denied</html>"
        parent = json.dumps({"title": "Grand Falls", "files": []}).encode()
        children = json.dumps({"items": []}).encode()
        catalog = json.dumps({"title": "Grand Falls", "files": [{
            "name": "field.csv", "size": 100,
            "url": "https://www.sciencebase.gov/catalog/file/get/field.csv?f=field.csv",
        }]}).encode()
        with patch.object(e590, "fetch_bounded", side_effect=[
            response(200, parent), response(200, children), response(200, catalog)
        ]), patch.object(e590, "fetch_prefix_bounded", return_value=response(
            206, payload, {"Content-Range": "bytes 0-25/4255", "Content-Type": "text/html"}
        )):
            result = e590.audit()
        self.assertEqual(result["decision"], "BOUNDED_SAMPLE_NOT_CONFIRMED")
        self.assertTrue(result["sample_response"]["html_response"])

    def test_transport_errors_are_fail_closed(self):
        with patch.object(e590, "fetch_bounded", side_effect=TimeoutError("timed out")):
            result = e590.audit()
        self.assertEqual(result["decision"], "ACQUISITION_ERROR")
        self.assertEqual(result["error_type"], "TimeoutError")
        self.assertFalse(result["credentials_used"])
        self.assertFalse(result["raw_values_stored"])


if __name__ == "__main__":
    unittest.main()
