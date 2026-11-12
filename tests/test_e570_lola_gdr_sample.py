from __future__ import annotations

import math
import struct

import pytest

from experiments.e570_lola_gdr_sample import (
    describe_window,
    extract_window_rows,
    parse_label,
    pixel_index,
    read_bounded_range_response,
    validate_content_range,
    validate_label,
    window_range,
)

LABEL = """PDS_VERSION_ID = "PDS3"
DATA_SET_ID = "LRO-L-LOLA-4-GDR-V1.0"
PRODUCT_ID = "LDEM_16_FLOAT"
TARGET_NAME = MOON
INSTRUMENT_ID = LOLA
RECORD_TYPE = FIXED_LENGTH
SAMPLE_TYPE = PC_REAL
SAMPLE_BITS = 32
UNIT = KILOMETER
LINES = 2880
LINE_SAMPLES = 5760
RECORD_BYTES = 23040
FILE_RECORDS = 2880
SCALING_FACTOR = 1
OFFSET = 1737.4
MAP_PROJECTION_TYPE = "SIMPLE CYLINDRICAL"
MAP_RESOLUTION = 16 <pix/deg>
MAP_SCALE = 1.89521 <km/pix>
LINE_PROJECTION_OFFSET = 1439.5 <pix>
SAMPLE_PROJECTION_OFFSET = 2879.5 <pix>
CENTER_LATITUDE = 0 <deg>
CENTER_LONGITUDE = 180 <deg>
MAP_PROJECTION_ROTATION = 0.0
LINE_FIRST_PIXEL = 1
LINE_LAST_PIXEL = 2880
SAMPLE_FIRST_PIXEL = 1
SAMPLE_LAST_PIXEL = 5760
MAXIMUM_LATITUDE = 90 <deg>
MINIMUM_LATITUDE = -90 <deg>
WESTERNMOST_LONGITUDE = 0 <deg>
EASTERNMOST_LONGITUDE = 360 <deg>
POSITIVE_LONGITUDE_DIRECTION = "EAST"
COORDINATE_SYSTEM_NAME = "MEAN EARTH/POLAR AXIS OF DE421"
MINIMUM = -9.075
MAXIMUM = 10.790
"""


def test_pds_label_parses_and_validates_exact_product_contract():
    fields = parse_label(LABEL)
    validate_label(fields)
    assert fields["product_id"] == "LDEM_16_FLOAT"
    assert fields["dataset_id"] == "LRO-L-LOLA-4-GDR-V1.0"
    assert fields["unit"] == "KILOMETER"
    assert fields["reference_radius_offset_km"] == 1737.4
    assert fields["map_resolution_pix_per_degree"] == 16
    assert fields["declared_missing_constant"] is False


def test_label_validation_fails_closed_on_wrong_sample_type():
    fields = parse_label(LABEL.replace("PC_REAL", "IEEE_REAL"))
    with pytest.raises(ValueError, match="sample_type"):
        validate_label(fields)


def test_pixel_index_uses_pixel_registered_simple_cylindrical_grid():
    assert pixel_index(32.8, 344.4) == (915, 5510)
    assert pixel_index(0.0, 0.0) == (1440, 0)
    assert pixel_index(0.0, 360.0) == (1440, 0)
    assert pixel_index(-45.0, 90.0) == (2160, 1440)


def test_pixel_index_rejects_invalid_latitude():
    with pytest.raises(ValueError, match="latitude"):
        pixel_index(90.1, 0.0)


def test_window_range_counts_intervening_fixed_record_bytes():
    start, end = window_range(10, 20, 100, 110, 23040)
    assert start == 10 * 23040 + 100 * 4
    assert end == 20 * 23040 + 110 * 4 + 3
    assert end - start + 1 == 10 * 23040 + 11 * 4


def test_range_validation_rejects_server_that_ignores_range():
    with pytest.raises(RuntimeError, match="did not honor"):
        validate_content_range(200, None, 16, 0, 15, 100)


def test_range_validation_checks_exact_content_range_and_length():
    validate_content_range(206, "bytes 100-115/1000", 16, 100, 115, 1000)
    with pytest.raises(RuntimeError, match="Content-Range"):
        validate_content_range(206, "bytes 99-115/1000", 17, 100, 115, 1000)


def test_window_extraction_reads_only_requested_columns_from_each_row():
    record_bytes = 32
    rows = []
    for row in range(3):
        record = [float(row * 10 + col) for col in range(8)]
        rows.append(struct.pack("<8f", *record))
    # Range begins at column 2 of row 0 and ends at column 4 of row 2.
    payload = rows[0][2 * 4:] + rows[1] + rows[2][:5 * 4]
    extracted = extract_window_rows(payload, 0, 2, 2, 4, record_bytes)
    assert extracted == [[2.0, 3.0, 4.0], [12.0, 13.0, 14.0], [22.0, 23.0, 24.0]]


def test_flat_window_has_zero_relief_and_zero_slope():
    result = describe_window([[1.25] * 5 for _ in range(5)], 30.0, 1.89521)
    assert result["radial_height_relief_p95_p05_m"] == pytest.approx(0.0)
    assert result["radial_height_mad_m"] == pytest.approx(0.0)
    assert result["median_local_slope_deg"] == pytest.approx(0.0)
    assert result["p90_local_slope_deg"] == pytest.approx(0.0)


def test_planar_window_reports_slope_with_latitude_adjusted_spacing():
    rows = [[1.0 + 0.001 * c for c in range(5)] for _ in range(5)]
    equator = describe_window(rows, 0.0, 1.0)
    midlat = describe_window(rows, 60.0, 1.0)
    assert midlat["median_local_slope_deg"] > equator["median_local_slope_deg"]


def test_nonfinite_samples_are_counted_as_missing_not_imputed():
    rows = [[1.0] * 5 for _ in range(5)]
    rows[0][0] = float("nan")
    result = describe_window(rows, 0.0, 1.89521)
    assert result["valid_pixel_count"] == 24
    assert result["missing_or_nonfinite_pixel_count"] == 1


def test_label_validation_fails_closed_when_missing_constant_is_declared():
    label = LABEL.replace(
        "MINIMUM = -9.075",
        "MISSING_CONSTANT = -3.4028235e38\nMINIMUM = -9.075",
    )
    fields = parse_label(label)
    assert fields["declared_missing_constant"] is True
    with pytest.raises(ValueError, match="missing constant"):
        validate_label(fields)


def test_projection_offset_changes_are_rejected_before_pixel_indexing():
    label = LABEL.replace(
        "SAMPLE_PROJECTION_OFFSET = 2879.5",
        "SAMPLE_PROJECTION_OFFSET = 2878.5",
    )
    fields = parse_label(label)
    with pytest.raises(ValueError, match="sample_projection_offset"):
        validate_label(fields)


class _FakeStreamResponse:
    def __init__(self, status_code, headers, chunks):
        self.status_code = status_code
        self.headers = headers
        self.chunks = chunks
        self.iterated = False

    def iter_content(self, chunk_size):
        self.iterated = True
        yield from self.chunks


def test_range_reader_rejects_ignored_range_before_reading_body():
    response = _FakeStreamResponse(200, {}, [b"x" * 100])
    with pytest.raises(RuntimeError, match="did not honor bounded HTTP Range"):
        read_bounded_range_response(response, 100, 115, 1000)
    assert response.iterated is False


def test_range_reader_caps_body_even_when_content_range_header_is_correct():
    response = _FakeStreamResponse(
        206,
        {"Content-Range": "bytes 100-115/1000"},
        [b"x" * 17],
    )
    with pytest.raises(RuntimeError, match="exceeded its byte cap"):
        read_bounded_range_response(response, 100, 115, 1000)


def test_range_reader_accepts_exact_streamed_payload():
    response = _FakeStreamResponse(
        206,
        {"Content-Range": "bytes 100-115/1000"},
        [b"01234567", b"89abcdef"],
    )
    assert read_bounded_range_response(response, 100, 115, 1000) == b"0123456789abcdef"
    assert response.iterated is True


def test_projection_rotation_and_extent_are_pinned():
    label = LABEL.replace(
        "MAP_PROJECTION_ROTATION = 0.0",
        "MAP_PROJECTION_ROTATION = 1.0",
    )
    fields = parse_label(label)
    with pytest.raises(ValueError, match="map_projection_rotation_deg"):
        validate_label(fields)
