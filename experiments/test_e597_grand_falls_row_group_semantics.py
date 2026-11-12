"""E597 deterministic tests for row identity and repeated timestamp groups."""
import unittest

from experiments.e597_grand_falls_row_group_semantics import CHANNELS, summarize_prefix


def make_fixture():
    headers = ["Date and Time", "Record Number"] + [
        column for family in CHANNELS.values() for column in family
    ]
    rows = []
    for timestamp, start in [("07/07/2023 09:25", 1), ("07/07/2023 09:26", 4)]:
        for offset in range(3):
            values = []
            for family_index, family in enumerate(CHANNELS.values()):
                for channel_index, _ in enumerate(family):
                    values.append(str((start + offset) * (family_index + channel_index + 1)))
            rows.append([timestamp, str(start + offset)] + values)
    return headers, rows


def serialize_fixture(headers, rows):
    import csv
    import io
    stream = io.StringIO()
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(headers)
    writer.writerows(rows)
    return stream.getvalue().encode()


class E597RowGroupTests(unittest.TestCase):
    def test_source_prefix_hashes_are_required(self):
        with self.assertRaises(ValueError):
            summarize_prefix(b"not the pinned sample")

    def test_channel_fixture_grouping_and_sequential_ids(self):
        headers, rows = make_fixture()
        # The production parser requires the pinned prefix hashes; this fixture tests
        # the row/group calculation through the extracted pure helper below.
        from experiments.e597_grand_falls_row_group_semantics import summarize_rows
        result = summarize_rows(headers, rows)
        self.assertEqual(result["row_count"], 6)
        self.assertEqual(result["timestamps"]["distinct_timestamp_groups"], 2)
        self.assertEqual(result["timestamps"]["group_size_distribution"], {"3": 2})
        self.assertEqual(result["record_number"]["timestamp_groups_with_distinct_record_ids"], 2)
        self.assertEqual(result["record_number"]["timestamp_groups_with_sequential_record_ids"], 2)
        self.assertEqual(result["within_timestamp_group"]["groups_with_all_rows_channel_vectors_distinct"], 2)

    def test_missing_channel_values_are_counted_not_imputed(self):
        headers, rows = make_fixture()
        rows[0][2] = ""
        from experiments.e597_grand_falls_row_group_semantics import summarize_rows
        result = summarize_rows(headers, rows)
        self.assertEqual(result["within_timestamp_group"]["family_rows_with_all_three_channels_present"]["wind_speed_mph"], 5)
        self.assertEqual(result["within_timestamp_group"]["row_nonnull_channel_count_distribution"]["11"], 1)
        self.assertEqual(result["row_nonnull_channel_count_distribution"]["12"], 5)

    def test_duplicate_record_numbers_are_measured_not_rewritten(self):
        headers, rows = make_fixture()
        rows[1][1] = rows[0][1]
        from experiments.e597_grand_falls_row_group_semantics import summarize_rows
        result = summarize_rows(headers, rows)
        self.assertEqual(result["record_number"]["unique_record_ids"], 5)
        self.assertEqual(result["record_number"]["reset_or_duplicate_count"], 1)


if __name__ == "__main__":
    unittest.main()
