from __future__ import annotations

import unittest
from unittest.mock import patch

from experiments.e562_firms_source_access import (
    EXPECTED_FIELDS,
    FetchResult,
    classify_protected_probe,
    parse_sample_summary,
    run_audit,
    validate_url,
)


class E562FirmsSourceAccessTests(unittest.TestCase):
    def test_url_allowlist_rejects_credentials_and_unknown_hosts(self):
        validate_url("https://firms.modaps.eosdis.nasa.gov/content/active_fire/")
        with self.assertRaises(ValueError):
            validate_url("https://user:pass@firms.modaps.eosdis.nasa.gov/x")
        with self.assertRaises(ValueError):
            validate_url("https://example.com/data.csv")
        with self.assertRaises(ValueError):
            validate_url("https://firms.modaps.eosdis.nasa.gov/x?token=secret")

    def test_sample_parser_counts_rows_and_preserves_sensor_fields(self):
        fields = sorted(EXPECTED_FIELDS)
        header = ",".join(fields)
        row1 = ",".join(
            "2023-07-12" if field == "acq_date"
            else "VIIRS" if field == "instrument"
            else "N" if field == "satellite"
            else "2.0NRT" if field == "version"
            else "1" for field in fields
        )
        row2 = row1.replace("2023-07-12", "2023-07-12")
        payload = (header + "\n" + row1 + "\n" + row2 + "\n").encode()
        result = FetchResult(200, "text/csv", payload, len(payload), False, False)
        summary = parse_sample_summary(result)
        self.assertEqual(summary["outcome"], "SAMPLE_PARSED")
        self.assertEqual(summary["row_count"], 2)
        self.assertEqual(summary["field_count"], 14)
        self.assertTrue(summary["required_fields_present"])
        self.assertEqual(summary["instruments"], ["VIIRS"])

    def test_truncated_sample_is_not_misreported_as_a_complete_dataset(self):
        result = FetchResult(200, "text/csv", b"latitude,longitude\n1,2", 22, True, False)
        self.assertEqual(parse_sample_summary(result)["outcome"], "SAMPLE_NOT_FULLY_RETRIEVED")

    def test_login_redirect_and_auth_status_are_not_followed(self):
        for status, redirect in ((302, True), (401, False), (403, False)):
            result = FetchResult(status, "text/html", b"login", 5, False, redirect)
            self.assertEqual(
                classify_protected_probe(result, api=False),
                "AUTHENTICATION_REQUIRED",
            )

    def test_api_key_error_is_distinguished_from_a_generic_http_error(self):
        result = FetchResult(400, "text/plain", b"Invalid MAP_KEY.", 16, False, False)
        self.assertEqual(
            classify_protected_probe(result, api=True),
            "MAP_KEY_REQUIRED",
        )

    def test_audit_receipt_never_retains_raw_rows_or_credentials(self):
        sample = FetchResult(200, "text/csv", b"latitude,longitude\n1,2\n", 22, False, False)
        daily = FetchResult(401, "text/html", b"login", 5, False, False)
        api = FetchResult(400, "text/plain", b"Invalid MAP_KEY", 15, False, False)
        with patch("experiments.e562_firms_source_access.fetch_url", side_effect=[sample, daily, api]):
            receipt = run_audit()
        self.assertFalse(receipt["protocol"]["credentials_used"])
        self.assertFalse(receipt["protocol"]["credentials_created"])
        self.assertFalse(receipt["protocol"]["raw_rows_retained"])
        self.assertNotIn("authorization", str(receipt).lower())
        self.assertEqual(receipt["daily_file_probe"]["outcome"], "AUTHENTICATION_REQUIRED")
        self.assertEqual(receipt["no_key_api_probe"]["outcome"], "MAP_KEY_REQUIRED")


if __name__ == "__main__":
    unittest.main()
