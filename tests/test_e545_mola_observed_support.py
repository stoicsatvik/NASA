import unittest

import numpy as np

from experiments.e545_mola_observed_support import (
    AcquisitionError,
    COUNT_RECORD_BYTES,
    TOPO_RECORD_BYTES,
    byte_range,
    extract_window,
    fetch_exact_range,
    make_window,
    parse_pds_label,
    pixel_index,
    summarize_window,
    validate_label,
    validate_url,
)

TOPO_LABEL = """
PDS_VERSION_ID = PDS3
FILE_RECORDS = 5632
RECORD_BYTES = 23040
TARGET_NAME = MARS
INSTRUMENT_ID = MOLA
PRODUCT_VERSION_ID = "2.0"
OBJECT = IMAGE
LINES = 5632
LINE_SAMPLES = 11520
SAMPLE_TYPE = MSB_INTEGER
SAMPLE_BITS = 16
UNIT = METER
END_OBJECT = IMAGE
MAP_PROJECTION_TYPE = SIMPLE CYLINDRICAL
POSITIVE_LONGITUDE_DIRECTION = EAST
MAP_RESOLUTION = 128.0 <PIXEL/DEGREE>
MAXIMUM_LATITUDE = 44.0 <DEGREE>
MINIMUM_LATITUDE = 0.0 <DEGREE>
WESTERNMOST_LONGITUDE = 0.0 <DEGREE>
EASTERNMOST_LONGITUDE = 90.0 <DEGREE>
LINE_PROJECTION_OFFSET = 5632.5
SAMPLE_PROJECTION_OFFSET = 23040.5
COORDINATE_SYSTEM_NAME = PLANETOCENTRIC
"""


class FakeResponse:
    def __init__(self, status_code, content=b"", headers=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}
        self.closed = False

    def close(self):
        self.closed = True


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


class E545MolaObservedSupportTests(unittest.TestCase):
    def test_exact_pds_object_allowlist(self):
        validate_url(
            "https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg128/megt44n000hb.img",
            "megt44n000hb",
            "img",
        )
        for url in (
            "http://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg128/megt44n000hb.img",
            "https://evil.example/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg128/megt44n000hb.img",
            "https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg128/megt44n090hb.img",
            "https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg128/megt44n000hb.img?download=1",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    validate_url(url, "megt44n000hb", "img")

    def test_label_parser_and_topography_contract(self):
        fields = parse_pds_label(TOPO_LABEL)
        self.assertEqual(fields["PRODUCT_VERSION_ID"], "2.0")
        self.assertEqual(fields["UNIT"], "METER")
        self.assertEqual(fields["SAMPLE_TYPE"], "MSB_INTEGER")
        self.assertEqual(fields["RECORD_BYTES"], "23040")
        validated = validate_label(TOPO_LABEL, "topography")
        self.assertEqual(validated["TARGET_NAME"], "MARS")

    def test_rejects_wrong_counts_record_width(self):
        broken = TOPO_LABEL.replace("RECORD_BYTES = 23040", "RECORD_BYTES = 11520")
        with self.assertRaisesRegex(ValueError, "RECORD_BYTES"):
            validate_label(broken, "topography")

    def test_jezero_overlap_centroid_maps_to_expected_one_based_pixel(self):
        row, col = pixel_index(18.3995, 77.27025)
        self.assertEqual((row, col), (3277, 9891))

    def test_rejects_coordinates_outside_the_pinned_tile(self):
        for lat, lon in ((44.0, 77.0), (18.0, 90.0), (-1.0, 77.0), (18.0, -0.1)):
            with self.subTest(lat=lat, lon=lon):
                with self.assertRaises(ValueError):
                    pixel_index(lat, lon)

    def test_window_is_odd_symmetric_and_inside_tile(self):
        window = make_window(3277, 9891, 33)
        self.assertEqual(
            (window["row_start"], window["row_end"], window["col_start"], window["col_end"]),
            (3261, 3293, 9875, 9907),
        )
        self.assertEqual(window["height"] * window["width"], 1089)
        with self.assertRaisesRegex(ValueError, "odd"):
            make_window(20, 20, 32)

    def test_byte_ranges_are_inclusive_fixed_record_offsets(self):
        self.assertEqual(byte_range(1, 1, TOPO_RECORD_BYTES), (0, 23039))
        self.assertEqual(byte_range(3261, 3293, TOPO_RECORD_BYTES), ((3261 - 1) * 23040, 3293 * 23040 - 1))
        self.assertEqual(byte_range(3261, 3293, COUNT_RECORD_BYTES), ((3261 - 1) * 11520, 3293 * 11520 - 1))

    def test_extracts_big_endian_topography_and_unsigned_counts_windows(self):
        topo_rows = np.array([[1, 2, 3, 4], [5, 6, 7, 8]], dtype=">i2").tobytes()
        count_rows = bytes([10, 20, 30, 40, 50, 60, 70, 80])
        window = {"height": 2, "col_start": 2, "col_end": 3}
        topo = extract_window(topo_rows, record_bytes=8, line_samples=4, window=window, kind="topography")
        counts = extract_window(count_rows, record_bytes=4, line_samples=4, window=window, kind="counts")
        np.testing.assert_array_equal(topo, np.array([[2, 3], [6, 7]], dtype=np.int16))
        np.testing.assert_array_equal(counts, np.array([[20, 30], [60, 70]], dtype=np.uint8))

    def test_summary_masks_interpolated_bins_using_the_count_tile(self):
        topo = np.array([[10, 20], [30, 40]], dtype=np.int16)
        counts = np.array([[1, 0], [2, 0]], dtype=np.uint8)
        result = summarize_window(topo, counts)
        self.assertEqual(result["window_bins"], 4)
        self.assertEqual(result["observed_bins_count_gt_zero"], 2)
        self.assertEqual(result["zero_count_bins"], 2)
        self.assertEqual(result["observed_bin_fraction"], 0.5)
        self.assertEqual(result["count_sum_across_bins"], 3)
        self.assertEqual(result["topography_observed_bins_median_m"], 20.0)
        self.assertEqual(result["topography_all_bins_median_m"], 25.0)
        self.assertTrue(result["interpolated_topography_excluded_from_observed_statistics"])

    def test_zero_observation_window_is_a_measured_negative_not_a_crash(self):
        result = summarize_window(
            np.array([[1, 2], [3, 4]], dtype=np.int16),
            np.zeros((2, 2), dtype=np.uint8),
        )
        self.assertEqual(result["observed_bins_count_gt_zero"], 0)
        self.assertIsNone(result["topography_observed_bins_median_m"])

    def test_exact_range_response_requires_206_and_matching_content_range(self):
        start, end, total = 100, 107, 1000
        response = FakeResponse(
            206,
            b"12345678",
            {"Content-Range": "bytes 100-107/1000", "Content-Length": "8"},
        )
        session = FakeSession(response)
        data, receipt = fetch_exact_range(
            session,
            "https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg128/megt44n000hb.img",
            "megt44n000hb",
            start,
            end,
            total,
        )
        self.assertEqual(data, b"12345678")
        self.assertEqual(receipt["bytes"], 8)
        self.assertEqual(session.calls[0][1]["headers"]["Range"], "bytes=100-107")
        self.assertTrue(response.closed)

    def test_ignored_range_is_preserved_and_full_download_is_refused(self):
        response = FakeResponse(200, b"")
        session = FakeSession(response)
        with self.assertRaises(AcquisitionError) as caught:
            fetch_exact_range(
                session,
                "https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg128/megt44n000hb.img",
                "megt44n000hb",
                0,
                7,
                1000,
            )
        self.assertEqual(caught.exception.outcome, "NEGATIVE_RESULT_RANGE_IGNORED")
        self.assertTrue(caught.exception.details["full_download_refused"])
        self.assertTrue(response.closed)

    def test_content_range_mismatch_fails_closed(self):
        response = FakeResponse(206, b"12345678", {"Content-Range": "bytes 101-108/1000"})
        with self.assertRaisesRegex(AcquisitionError, "Content-Range"):
            fetch_exact_range(
                FakeSession(response),
                "https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg128/megt44n000hb.img",
                "megt44n000hb",
                100,
                107,
                1000,
            )


if __name__ == "__main__":
    unittest.main()
