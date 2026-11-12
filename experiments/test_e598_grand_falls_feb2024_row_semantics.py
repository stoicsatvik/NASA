"""Deterministic E598 tests for exact-file selection and cross-release row semantics."""
import unittest

from experiments.e598_grand_falls_feb2024_row_semantics import (
    EXPECTED_FILE_NAME,
    EXPECTED_FILE_SIZE,
    classify_csv_response,
    select_exact_file,
    summarize_payload,
)
from experiments.e597_grand_falls_row_group_semantics import CHANNELS, summarize_rows


class E598FileSelectionTests(unittest.TestCase):
    def test_selects_only_exact_name_and_size(self):
        records = [
            {"name": EXPECTED_FILE_NAME, "size": EXPECTED_FILE_SIZE},
            {"name": EXPECTED_FILE_NAME, "size": EXPECTED_FILE_SIZE + 1},
            {"name": "other.csv", "size": EXPECTED_FILE_SIZE},
        ]
        self.assertEqual(select_exact_file(records), records[0])

    def test_rejects_missing_or_size_mismatched_file(self):
        with self.assertRaises(ValueError):
            select_exact_file([{"name": EXPECTED_FILE_NAME, "size": EXPECTED_FILE_SIZE + 1}])

    def test_rejects_ambiguous_exact_file_records(self):
        record = {"name": EXPECTED_FILE_NAME, "size": EXPECTED_FILE_SIZE}
        with self.assertRaises(ValueError):
            select_exact_file([record, dict(record)])


class E598RowSemanticsTests(unittest.TestCase):
    def make_fixture(self):
        headers = ["Date and Time", "Record Number"] + [
            column for family in CHANNELS.values() for column in family
        ]
        rows = []
        for timestamp, start, base in [
            ("02/14/2024 09:25", 1, 10),
            ("02/14/2024 09:26", 4, 20),
        ]:
            signature = [
                str(base + family_index + channel_index)
                for family_index, family in enumerate(CHANNELS.values())
                for channel_index, _ in enumerate(family)
            ]
            for offset in range(3):
                rows.append([timestamp, str(start + offset)] + signature)
        return headers, rows

    def test_repeated_vectors_do_not_collapse_sequential_row_ids(self):
        headers, rows = self.make_fixture()
        summary = summarize_rows(headers, rows)
        self.assertEqual(summary["row_count"], 6)
        self.assertEqual(summary["record_number"]["unique_record_ids"], 6)
        self.assertEqual(summary["record_number"]["unit_step_count"], 5)
        self.assertEqual(summary["timestamps"]["group_size_distribution"], {"3": 2})
        self.assertEqual(
            summary["within_timestamp_group"]["unique_channel_vector_count_distribution"],
            {"1": 2},
        )

    def test_incomplete_channel_values_remain_missing(self):
        headers, rows = self.make_fixture()
        rows[0][2] = ""
        summary = summarize_rows(headers, rows)
        self.assertEqual(
            summary["within_timestamp_group"]["row_nonnull_channel_count_distribution"]["11"],
            1,
        )

    def test_exact_file_size_gate_precedes_parsing(self):
        with self.assertRaises(ValueError):
            summarize_payload(b"too short")


    def test_nonstandard_content_type_requires_exact_csv_header(self):
        header = ["Date and Time", "Record Number"] + [
            column for family in CHANNELS.values() for column in family
        ]
        payload = (",".join(header) + "\n").encode()
        self.assertEqual(
            classify_csv_response("application/octet-stream", payload),
            "NONSTANDARD_CONTENT_TYPE_BUT_EXACT_CSV_SCHEMA_VALID",
        )

    def test_html_payload_is_not_admitted_as_csv(self):
        self.assertIsNone(classify_csv_response("text/html", b"<html><body>not csv</body></html>"))


if __name__ == "__main__":
    unittest.main()
