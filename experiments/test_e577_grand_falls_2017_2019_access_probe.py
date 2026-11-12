import io
import unittest
import zipfile

from experiments.e577_grand_falls_2017_2019_access_probe import (
    choose_candidate,
    inspect_payload,
    parse_content_range,
    safe_url_summary,
    summarize_text,
    summarize_zip,
)


class E577Tests(unittest.TestCase):
    def test_url_summary_redacts_query_values(self):
        value = safe_url_summary("https://sciencebase.usgs.gov/manager/download/x?sig=secret&expires=123")
        self.assertEqual(value["host"], "sciencebase.usgs.gov")
        self.assertEqual(value["query_key_names"], ["expires", "sig"])
        self.assertNotIn("secret", str(value))
        self.assertNotIn("123", str(value))

    def test_candidate_requires_explicit_download_uri_and_supported_type(self):
        files = [
            {"name": "preview.csv", "size": 100, "url": "https://sciencebase.usgs.gov/manager/item/x"},
            {"name": "large.csv", "size": 9_000_000, "downloadUri": "https://sciencebase.usgs.gov/manager/download/y"},
            {"name": "small.csv", "size": 500, "downloadUri": "https://sciencebase.usgs.gov/manager/download/z"},
        ]
        self.assertEqual(choose_candidate(files)["name"], "small.csv")

    def test_content_range_validation(self):
        self.assertEqual(parse_content_range("bytes 0-31/100"), (0, 31, 100))
        self.assertEqual(parse_content_range("bytes 1-31/100"), (1, 31, 100))
        self.assertIsNone(parse_content_range("bytes 0-100/100"))
        self.assertIsNone(parse_content_range("items 0-31/100"))

    def test_csv_summary_uses_real_rows_without_retaining_row_objects(self):
        payload = (
            "timestamp,wind_speed_mph,sediment_flux_g_m2_s\n"
            "2017-02-07T00:00:00Z,5,0.2\n"
            "2017-02-07T00:00:10Z,7,0.4\n"
        ).encode()
        summary = summarize_text(payload)
        self.assertEqual(summary["row_count"], 2)
        self.assertEqual(summary["time_bounds"]["timestamp"]["min"], "2017-02-07T00:00:00Z")
        self.assertEqual(summary["numeric_summaries"]["wind_speed_mph"]["mean"], 6.0)
        self.assertNotIn("rows", summary)

    def test_zip_selects_smallest_delimited_member(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("large.csv", "a,b\n1,2\n" * 10)
            archive.writestr("small.csv", "timestamp,wind_speed\n2020-01-01,3\n")
        summary = summarize_zip(buffer.getvalue())
        self.assertEqual(summary["format"], "zip_with_delimited_member")
        self.assertEqual(summary["member_name"], "small.csv")
        self.assertEqual(summary["member_summary"]["row_count"], 1)

    def test_inspect_payload_returns_aggregates_not_raw_rows(self):
        payload = b"timestamp,wind_speed\n2020-01-01,3\n"
        result = inspect_payload("sample.csv", payload)
        self.assertEqual(result["data_summary"]["row_count"], 1)
        self.assertNotIn("raw_rows", result["data_summary"])


if __name__ == "__main__":
    unittest.main()
