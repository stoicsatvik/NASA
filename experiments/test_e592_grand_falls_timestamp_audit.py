import json
import unittest

from experiments.e592_grand_falls_timestamp_audit import (
    EXPECTED_FILE_NAME,
    EXPECTED_FILE_SIZE,
    MAX_SAMPLE_BYTES,
    ProbeError,
    audit,
    summarize_timestamps,
    validate_sample_url,
)
from experiments.e590_grand_falls_2023_2024_probe import CATALOG_RECORD_ID

SAFE_URL = "https://www.sciencebase.gov/catalog/file/get/?f=fixture"


class E592TimestampTests(unittest.TestCase):
    def test_chronological_bounds_are_parsed_not_lexicographic(self):
        payload = (
            b"Date and Time,Record Number\n"
            b"7/9/2023 9:59,1\n"
            b"7/10/2023 0:00,2\n"
        )
        result = summarize_timestamps(payload)
        self.assertEqual(result["chronological_min_naive"], "2023-07-09T09:59:00")
        self.assertEqual(result["chronological_max_naive"], "2023-07-10T00:00:00")
        self.assertEqual(result["ordering"], "STRICTLY_INCREASING")
        self.assertEqual(result["adjacent_interval_count"], 1)
        self.assertEqual(result["positive_interval_min_seconds"], 50_460)

    def test_duplicate_and_out_of_order_rows_are_preserved(self):
        payload = (
            b"Date and Time,Record Number\n"
            b"7/9/2023 23:58,1\n"
            b"7/9/2023 23:59,2\n"
            b"7/10/2023 0:00,3\n"
            b"7/10/2023 0:00,4\n"
            b"7/9/2023 23:59,5\n"
            b"not-a-date,6\n"
        )
        result = summarize_timestamps(payload)
        self.assertEqual(result["row_count"], 6)
        self.assertEqual(result["valid_timestamp_count"], 5)
        self.assertEqual(result["invalid_timestamp_count"], 1)
        self.assertEqual(result["duplicate_timestamp_value_count"], 2)
        self.assertEqual(result["duplicate_timestamp_row_count"], 2)
        self.assertEqual(result["negative_interval_count"], 1)
        self.assertEqual(result["zero_interval_count"], 1)
        self.assertEqual(result["one_minute_interval_count"], 2)
        self.assertEqual(result["ordering"], "INCOMPLETE_TIMESTAMP_PARSE")

    def test_one_minute_sequence_is_reported_without_claiming_raw_hz(self):
        payload = (
            b"Date and Time,Record Number\n"
            b"7/9/2023 23:58,1\n"
            b"7/9/2023 23:59,2\n"
            b"7/10/2023 0:00,3\n"
        )
        result = summarize_timestamps(payload)
        self.assertEqual(result["cadence"], "ALL_ADJACENT_VALID_ROWS_60_SECONDS")
        self.assertEqual(result["one_minute_interval_fraction"], 1.0)
        self.assertEqual(result["timezone_status"].split(";")[0], "NOT_ENCODED_IN_COLUMN")

    def test_missing_or_duplicate_timestamp_header_fails_closed(self):
        with self.assertRaises(ValueError):
            summarize_timestamps(b"Timestamp,Record Number\n7/9/2023 9:59,1\n")
        with self.assertRaises(ValueError):
            summarize_timestamps(
                b"Date and Time,Date and Time,Record Number\n7/9/2023 9:59,7/9/2023 9:59,1\n"
            )

    def test_raw_timestamp_strings_are_not_retained(self):
        raw = "7/9/2023 23:58"
        result = summarize_timestamps(
            b"Date and Time,Record Number\n7/9/2023 23:58,1\n7/9/2023 23:59,2\n"
        )
        encoded = json.dumps(result)
        self.assertNotIn(raw, encoded)
        self.assertIn("2023-07-09T23:58:00", encoded)
        self.assertFalse(result["raw_timestamps_stored"])

    def test_url_boundary_rejects_nonstandard_ports_userinfo_and_fragments(self):
        for url in (
            "http://www.sciencebase.gov/catalog/file/get/?f=x",
            "https://example.com/file.csv",
            "https://www.sciencebase.gov:444/catalog/file/get/?f=x",
            "https://user@www.sciencebase.gov/catalog/file/get/?f=x",
            "https://www.sciencebase.gov/catalog/file/get/?f=x#fragment",
            "https://www.sciencebase.gov/a/../file.csv",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ProbeError):
                    validate_sample_url(url)

    def test_url_boundary_accepts_allowlisted_https_endpoint(self):
        validate_sample_url(SAFE_URL)
        validate_sample_url(
            "https://prod-is-usgs-sb-prod-content.s3.amazonaws.com/object.csv"
        )

    def test_audit_fetches_only_exact_catalogued_file_and_returns_aggregate_timestamps(self):
        csv_bytes = (
            b"Date and Time,Record Number\n"
            b"7/9/2023 23:58,1\n"
            b"7/9/2023 23:59,2\n"
        )
        payload = csv_bytes + b" " * (MAX_SAMPLE_BYTES - len(csv_bytes))
        document = {
            "id": CATALOG_RECORD_ID,
            "files": [{
                "name": EXPECTED_FILE_NAME,
                "size": EXPECTED_FILE_SIZE,
                "downloadUri": SAFE_URL,
            }],
        }
        calls = {"metadata": 0, "sample": 0}

        def metadata_fetcher(url, *, limit):
            calls["metadata"] += 1
            self.assertGreaterEqual(limit, 1)
            return {"status": 200, "payload": json.dumps(document).encode("utf-8")}

        def sample_fetcher(url, *, limit):
            calls["sample"] += 1
            self.assertEqual(url, SAFE_URL)
            self.assertEqual(limit, MAX_SAMPLE_BYTES)
            return {
                "status": 200,
                "headers": {
                    "Content-Type": "text/csv",
                    "Content-Length": str(EXPECTED_FILE_SIZE),
                },
                "payload": payload,
                "final_url": SAFE_URL,
            }

        result = audit(metadata_fetcher, sample_fetcher)
        self.assertEqual(result["decision"], "TIMESTAMP_AUDIT_COMPLETE")
        self.assertEqual(calls, {"metadata": 1, "sample": 1})
        self.assertEqual(result["timestamp_audit"]["row_count"], 2)
        self.assertEqual(result["timestamp_audit"]["one_minute_interval_count"], 1)
        self.assertFalse(result["raw_rows_stored"])
        self.assertFalse(result["raw_timestamps_stored"])
        self.assertFalse(result["full_file_downloaded"])
        encoded = json.dumps(result)
        self.assertNotIn("fixture", encoded)
        self.assertNotIn("7/9/2023 23:58", encoded)

    def test_catalog_item_identity_mismatch_prevents_sample_request(self):
        document = {"id": "wrong-item", "files": [{
            "name": EXPECTED_FILE_NAME,
            "size": EXPECTED_FILE_SIZE,
            "downloadUri": SAFE_URL,
        }]}
        sample_calls = []

        def metadata_fetcher(url, *, limit):
            return {"status": 200, "payload": json.dumps(document).encode("utf-8")}

        def sample_fetcher(url, *, limit):
            sample_calls.append(url)
            raise AssertionError("sample request must not run")

        result = audit(metadata_fetcher, sample_fetcher)
        self.assertEqual(result["decision"], "CATALOG_ITEM_ID_NOT_CONFIRMED")
        self.assertEqual(sample_calls, [])

    def test_catalogue_size_mismatch_prevents_sample_request(self):
        document = {"id": CATALOG_RECORD_ID, "files": [{
            "name": EXPECTED_FILE_NAME,
            "size": EXPECTED_FILE_SIZE - 1,
            "downloadUri": SAFE_URL,
        }]}
        sample_calls = []

        def metadata_fetcher(url, *, limit):
            return {"status": 200, "payload": json.dumps(document).encode("utf-8")}

        def sample_fetcher(url, *, limit):
            sample_calls.append(url)
            raise AssertionError("sample request must not run")

        result = audit(metadata_fetcher, sample_fetcher)
        self.assertEqual(result["decision"], "EXPECTED_FILE_RECORD_NOT_UNIQUE")
        self.assertEqual(sample_calls, [])

    def test_unconfirmed_content_range_is_not_parsed(self):
        csv_bytes = b"Date and Time,Record Number\n7/9/2023 23:58,1\n"
        payload = csv_bytes + b" " * (MAX_SAMPLE_BYTES - len(csv_bytes))
        document = {"id": CATALOG_RECORD_ID, "files": [{
            "name": EXPECTED_FILE_NAME,
            "size": EXPECTED_FILE_SIZE,
            "downloadUri": SAFE_URL,
        }]}

        def metadata_fetcher(url, *, limit):
            return {"status": 200, "payload": json.dumps(document).encode("utf-8")}

        def sample_fetcher(url, *, limit):
            return {
                "status": 206,
                "headers": {"Content-Type": "text/csv"},
                "payload": payload,
                "final_url": SAFE_URL,
            }

        result = audit(metadata_fetcher, sample_fetcher)
        self.assertEqual(result["decision"], "BOUNDED_PREFIX_NOT_CONFIRMED")
        self.assertNotIn("timestamp_audit", result)


if __name__ == "__main__":
    unittest.main()
