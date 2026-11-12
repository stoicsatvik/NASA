"""E570: bounded real LOLA GDR sample and metadata validation.

Only three 11x11 windows are acquired by HTTP byte ranges. The receipt keeps
source hashes and aggregate descriptors, never raw raster values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
from pathlib import Path
from typing import Any

import requests

LABEL_URL = (
    "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/"
    "lrolol_1xxx/data/lola_gdr/cylindrical/float_img/ldem_16_float.lbl"
)
IMAGE_URL = (
    "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/"
    "lrolol_1xxx/data/lola_gdr/cylindrical/float_img/ldem_16_float.img"
)
PRODUCT_PAGE = "https://pds-geosciences.wustl.edu/missions/lro/lola.htm"
DATASET_DOI = "10.17189/1520642"
BUNDLE_DOI = "10.17189/tnyt-7007"
EXPECTED_FILE_BYTES = 66_355_200
WINDOW_SIZE = 11
MAX_TOTAL_RANGE_BYTES = 1_000_000
USER_AGENT = "Unified-Parallel-Foundry-E570/1.0"

# Analyst-selected sample centers only. They are not ground-truth analogue labels.
SAMPLE_CENTERS = (
    {"id": "window_a", "latitude_deg": 32.8, "longitude_deg_east": 344.4},
    {"id": "window_b", "latitude_deg": 8.5, "longitude_deg_east": 31.4},
    {"id": "window_c", "latitude_deg": -45.0, "longitude_deg_east": 90.0},
)


def label_value(label: str, key: str) -> str:
    match = re.search(
        rf"^\s*{re.escape(key)}\s*=\s*(.*?)\s*$",
        label,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if not match:
        raise ValueError(f"required PDS label field missing: {key}")
    value = match.group(1).strip()
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    return value


def numeric_prefix(value: str) -> float:
    match = re.match(r"\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?)", value)
    if not match:
        raise ValueError(f"not a numeric PDS value: {value!r}")
    return float(match.group(1))


def parse_label(label: str) -> dict[str, Any]:
    fields = {
        "pds_version_id": label_value(label, "PDS_VERSION_ID"),
        "dataset_id": label_value(label, "DATA_SET_ID"),
        "product_id": label_value(label, "PRODUCT_ID"),
        "target_name": label_value(label, "TARGET_NAME"),
        "instrument_id": label_value(label, "INSTRUMENT_ID"),
        "record_type": label_value(label, "RECORD_TYPE"),
        "sample_type": label_value(label, "SAMPLE_TYPE"),
        "unit": label_value(label, "UNIT"),
        "sample_bits": int(numeric_prefix(label_value(label, "SAMPLE_BITS"))),
        "lines": int(numeric_prefix(label_value(label, "LINES"))),
        "line_samples": int(numeric_prefix(label_value(label, "LINE_SAMPLES"))),
        "record_bytes": int(numeric_prefix(label_value(label, "RECORD_BYTES"))),
        "file_records": int(numeric_prefix(label_value(label, "FILE_RECORDS"))),
        "scaling_factor": numeric_prefix(label_value(label, "SCALING_FACTOR")),
        "reference_radius_offset_km": numeric_prefix(label_value(label, "OFFSET")),
        "map_projection_type": label_value(label, "MAP_PROJECTION_TYPE"),
        "map_resolution_pix_per_degree": numeric_prefix(label_value(label, "MAP_RESOLUTION")),
        "map_scale_km_per_pixel_at_equator": numeric_prefix(label_value(label, "MAP_SCALE")),
        "line_projection_offset": numeric_prefix(label_value(label, "LINE_PROJECTION_OFFSET")),
        "sample_projection_offset": numeric_prefix(label_value(label, "SAMPLE_PROJECTION_OFFSET")),
        "center_latitude_deg": numeric_prefix(label_value(label, "CENTER_LATITUDE")),
        "center_longitude_deg": numeric_prefix(label_value(label, "CENTER_LONGITUDE")),
        "longitude_direction": label_value(label, "POSITIVE_LONGITUDE_DIRECTION"),
        "coordinate_system_name": label_value(label, "COORDINATE_SYSTEM_NAME"),
        "minimum_km": numeric_prefix(label_value(label, "MINIMUM")),
        "maximum_km": numeric_prefix(label_value(label, "MAXIMUM")),
    }
    fields["declared_missing_constant"] = bool(
        re.search(r"^\s*(?:MISSING_CONSTANT|MISSING_VALUE)\s*=", label, re.I | re.M)
    )
    return fields


def validate_label(fields: dict[str, Any]) -> None:
    expected = {
        "pds_version_id": "PDS3",
        "dataset_id": "LRO-L-LOLA-4-GDR-V1.0",
        "product_id": "LDEM_16_FLOAT",
        "target_name": "MOON",
        "instrument_id": "LOLA",
        "record_type": "FIXED_LENGTH",
        "sample_type": "PC_REAL",
        "unit": "KILOMETER",
        "sample_bits": 32,
        "lines": 2880,
        "line_samples": 5760,
        "record_bytes": 23040,
        "file_records": 2880,
        "map_projection_type": "SIMPLE CYLINDRICAL",
        "longitude_direction": "EAST",
    }
    for key, value in expected.items():
        if fields.get(key) != value:
            raise ValueError(f"PDS metadata mismatch for {key}: {fields.get(key)!r} != {value!r}")
    if fields["file_records"] * fields["record_bytes"] != EXPECTED_FILE_BYTES:
        raise ValueError("PDS fixed-record dimensions do not match the pinned IMG byte size")
    if fields["line_samples"] * 4 != fields["record_bytes"]:
        raise ValueError("float32 row size does not match RECORD_BYTES")
    if fields["map_resolution_pix_per_degree"] != 16:
        raise ValueError("unexpected LOLA map resolution")
    if fields["reference_radius_offset_km"] != 1737.4:
        raise ValueError("unexpected LOLA reference-sphere radius")
    if fields["scaling_factor"] != 1:
        raise ValueError("unexpected LOLA scaling factor")


def pixel_index(latitude_deg: float, longitude_deg_east: float, resolution: float = 16) -> tuple[int, int]:
    if not math.isfinite(latitude_deg) or not -90 <= latitude_deg <= 90:
        raise ValueError("latitude must be finite and within [-90, 90]")
    if not math.isfinite(longitude_deg_east):
        raise ValueError("longitude must be finite")
    # The label describes a pixel-registered, 16-pixel/degree simple cylindrical grid.
    row = min(2879, max(0, math.floor((90.0 - latitude_deg) * resolution)))
    col = math.floor((longitude_deg_east % 360.0) * resolution)
    return row, min(5759, max(0, col))


def window_range(
    row_start: int,
    row_end: int,
    col_start: int,
    col_end: int,
    record_bytes: int = 23040,
) -> tuple[int, int]:
    if row_start < 0 or row_end < row_start or col_start < 0 or col_end < col_start:
        raise ValueError("invalid window bounds")
    start = row_start * record_bytes + col_start * 4
    end = row_end * record_bytes + col_end * 4 + 3
    return start, end


def validate_content_range(
    status_code: int,
    content_range: str | None,
    payload_length: int,
    start: int,
    end: int,
    total_bytes: int,
) -> None:
    expected = f"bytes {start}-{end}/{total_bytes}"
    if status_code != 206:
        raise RuntimeError(f"server did not honor bounded HTTP Range (status {status_code})")
    if content_range != expected:
        raise RuntimeError(f"Content-Range mismatch: {content_range!r} != {expected!r}")
    if payload_length != end - start + 1:
        raise RuntimeError("HTTP Range payload length mismatch")


def extract_window_rows(
    payload: bytes,
    row_start: int,
    row_end: int,
    col_start: int,
    col_end: int,
    record_bytes: int = 23040,
) -> list[list[float]]:
    width = col_end - col_start + 1
    if width <= 0 or row_end < row_start:
        raise ValueError("invalid window dimensions")
    expected_start, expected_end = window_range(
        row_start, row_end, col_start, col_end, record_bytes
    )
    if len(payload) != expected_end - expected_start + 1:
        raise ValueError("range payload length does not match the requested window")
    rows: list[list[float]] = []
    for row_index in range(row_end - row_start + 1):
        offset = row_index * record_bytes
        row_bytes = payload[offset : offset + width * 4]
        if len(row_bytes) != width * 4:
            raise ValueError("truncated row slice")
        rows.append(list(struct.unpack("<" + "f" * width, row_bytes)))
    return rows


def quantile(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("quantile requires at least one value")
    if not 0 <= probability <= 1:
        raise ValueError("quantile probability must be in [0, 1]")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def describe_window(
    rows: list[list[float]],
    latitude_deg: float,
    pixel_scale_km: float,
) -> dict[str, Any]:
    width = len(rows[0]) if rows else 0
    if not rows or width < 3 or any(len(row) != width for row in rows):
        raise ValueError("window must be a rectangular grid at least 3x3")
    finite = [value for row in rows for value in row if math.isfinite(value)]
    missing = len(rows) * width - len(finite)
    if len(finite) < 9:
        raise ValueError("too few finite LOLA samples for a local descriptor")
    p05 = quantile(finite, 0.05)
    p50 = quantile(finite, 0.50)
    p95 = quantile(finite, 0.95)
    mad = quantile([abs(value - p50) for value in finite], 0.50)

    dx_m = pixel_scale_km * 1000.0 * max(abs(math.cos(math.radians(latitude_deg))), 1e-6)
    dy_m = pixel_scale_km * 1000.0
    slopes: list[float] = []
    for r in range(1, len(rows) - 1):
        for c in range(1, width - 1):
            neighbors = (rows[r][c], rows[r][c - 1], rows[r][c + 1], rows[r - 1][c], rows[r + 1][c])
            if not all(math.isfinite(value) for value in neighbors):
                continue
            dz_dx = (rows[r][c + 1] - rows[r][c - 1]) * 1000.0 / (2 * dx_m)
            dz_dy = (rows[r + 1][c] - rows[r - 1][c]) * 1000.0 / (2 * dy_m)
            slopes.append(math.degrees(math.atan(math.hypot(dz_dx, dz_dy))))

    return {
        "window_width_pixels": width,
        "window_height_pixels": len(rows),
        "valid_pixel_count": len(finite),
        "missing_or_nonfinite_pixel_count": missing,
        "radial_height_p05_km": p05,
        "radial_height_median_km": p50,
        "radial_height_p95_km": p95,
        "radial_height_relief_p95_p05_m": (p95 - p05) * 1000.0,
        "radial_height_mad_m": mad * 1000.0,
        "median_local_slope_deg": quantile(slopes, 0.50) if slopes else None,
        "p90_local_slope_deg": quantile(slopes, 0.90) if slopes else None,
        "slope_sample_count": len(slopes),
        "longitude_pixel_spacing_m_at_center": dx_m,
        "latitude_pixel_spacing_m": dy_m,
    }


def fetch_label(session: requests.Session) -> tuple[str, dict[str, Any]]:
    response = session.get(
        LABEL_URL,
        headers={"Accept-Encoding": "identity", "User-Agent": USER_AGENT},
        timeout=(10, 30),
    )
    if response.status_code != 200:
        raise RuntimeError(f"LOLA label HTTP status {response.status_code}")
    label = response.text
    fields = parse_label(label)
    validate_label(fields)
    receipt = {
        "url": LABEL_URL,
        "http_status": response.status_code,
        "content_bytes": len(response.content),
        "sha256": hashlib.sha256(response.content).hexdigest(),
        "pds_fields": fields,
    }
    return label, receipt


def fetch_window(
    session: requests.Session,
    fields: dict[str, Any],
    center: dict[str, Any],
) -> tuple[dict[str, Any], int, str]:
    row, col = pixel_index(
        float(center["latitude_deg"]),
        float(center["longitude_deg_east"]),
        float(fields["map_resolution_pix_per_degree"]),
    )
    half = WINDOW_SIZE // 2
    row_start, row_end = row - half, row + half
    col_start, col_end = col - half, col + half
    if row_start < 0 or row_end >= fields["lines"] or col_start < 0 or col_end >= fields["line_samples"]:
        raise ValueError(f"sample window {center['id']} touches a raster edge")
    start, end = window_range(
        row_start, row_end, col_start, col_end, fields["record_bytes"]
    )
    response = session.get(
        IMAGE_URL,
        headers={
            "Range": f"bytes={start}-{end}",
            "Accept-Encoding": "identity",
            "User-Agent": USER_AGENT,
        },
        timeout=(10, 60),
    )
    validate_content_range(
        response.status_code,
        response.headers.get("Content-Range"),
        len(response.content),
        start,
        end,
        fields["file_records"] * fields["record_bytes"],
    )
    rows = extract_window_rows(
        response.content,
        row_start,
        row_end,
        col_start,
        col_end,
        fields["record_bytes"],
    )
    descriptor = describe_window(
        rows,
        float(center["latitude_deg"]),
        float(fields["map_scale_km_per_pixel_at_equator"]),
    )
    receipt = {
        **center,
        "center_row_zero_based": row,
        "center_column_zero_based": col,
        "window_rows_zero_based": [row_start, row_end],
        "window_columns_zero_based": [col_start, col_end],
        "requested_byte_range": [start, end],
        "range_bytes_transferred": len(response.content),
        "range_sha256": hashlib.sha256(response.content).hexdigest(),
        "content_range": response.headers.get("Content-Range"),
        "raw_pixel_values_retained": False,
        "descriptor": descriptor,
    }
    return receipt, len(response.content), hashlib.sha256(response.content).hexdigest()


def run() -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "experiment": "E570_LOLA_GDR_BOUNDED_REAL_SAMPLE",
        "date": "2026-11-12",
        "outcome": "NOT_RUN",
        "source": {
            "product_page": PRODUCT_PAGE,
            "dataset_doi": DATASET_DOI,
            "bundle_doi": BUNDLE_DOI,
            "label_url": LABEL_URL,
            "image_url": IMAGE_URL,
        },
        "claim_state": {
            "LOLA_GDR_metadata": "NOT YET VERIFIED",
            "LOLA_real_sample_ingestion": "NOT YET MEASURED",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
        },
        "limitations": [
            "Sample centers are analyst-selected acquisition windows, not analogue labels or geological ground truth.",
            "The PDS label reports radial height relative to a 1737.4 km reference sphere; this receipt does not apply a lunar geoid correction.",
            "The 16 pixels/degree grid has approximately 1.89521 km equatorial postings; longitude spacing contracts with cosine(latitude).",
            "Only three 11x11 windows are sampled; no global coverage or spatial representativeness is claimed.",
            "No Diviner thermal, MOLA, THEMIS or Earth descriptor is joined in this experiment.",
            "No raw raster pixels or full IMG file are retained.",
        ],
    }
    session = requests.Session()
    try:
        _, label_receipt = fetch_label(session)
        fields = label_receipt["pds_fields"]
        receipt["label"] = label_receipt
        total_bytes = 0
        windows = []
        hashes = []
        for center in SAMPLE_CENTERS:
            window_receipt, transferred, digest = fetch_window(session, fields, center)
            total_bytes += transferred
            windows.append(window_receipt)
            hashes.append(digest)
            if total_bytes > MAX_TOTAL_RANGE_BYTES:
                raise RuntimeError("bounded LOLA sample exceeded the 1 MB transfer cap")
        receipt["windows"] = windows
        receipt["transport"] = {
            "range_requests": len(windows),
            "range_bytes_transferred": total_bytes,
            "range_transfer_cap_bytes": MAX_TOTAL_RANGE_BYTES,
            "full_img_downloaded": False,
            "raw_pixel_values_retained": False,
            "sample_range_hashes": hashes,
        }
        receipt["claim_state"] = {
            "LOLA_GDR_metadata": "SUPPORTED FOR PINNED PDS3 PRODUCT LABEL",
            "LOLA_real_sample_ingestion": "MEASURED FOR THREE BOUNDED 11x11 WINDOWS",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
        }
        receipt["outcome"] = "LOLA_METADATA_AND_THREE_REAL_WINDOWS_ACQUIRED"
    except Exception as exc:
        receipt["outcome"] = "ERROR"
        receipt["error"] = {"kind": type(exc).__name__, "message": str(exc)[:700]}
    finally:
        session.close()
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "experiment": result["experiment"],
        "outcome": result["outcome"],
        "windows": len(result.get("windows", [])),
        "range_bytes": result.get("transport", {}).get("range_bytes_transferred"),
        "cross_body_similarity": result["claim_state"]["cross_body_similarity"],
    }, sort_keys=True))
    return 0 if result["outcome"].startswith("LOLA_METADATA_AND_THREE_REAL_WINDOWS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
