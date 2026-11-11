"""Bounded, provenance-pinned MOLA MEGDR sample around the Jezero CTX/HiRISE overlap.

Only five complete raster rows from each of two official PDS products are
requested. HTTP Range must be honored exactly; a server that ignores Range is
read for at most 33 bytes and rejected. Count=0 bins are excluded because the
MEGDR topography product supplies interpolated values for empty bins.

This is a MOLA-only sample/coverage audit, not cross-instrument registration,
analogue recovery, or route-safety evidence.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg128"
TOPO_URL = f"{BASE}/megt44n000hb.img"
COUNT_URL = f"{BASE}/megc44n000hb.img"
TOPO_LABEL_URL = f"{BASE}/megt44n000hb.lbl"
COUNT_LABEL_URL = f"{BASE}/megc44n000hb.lbl"

# Frozen from the official PDS3 labels linked above. The 2026 PDS4 bundle
# directory retains the same MEGDR product names and supplies PDS4 XML labels.
LINES = 5632
SAMPLES = 11520
PIXELS_PER_DEGREE = 128.0
CENTER_LATITUDE = 0.0
CENTER_LONGITUDE = 180.0
LINE_PROJECTION_OFFSET = 5632.5
SAMPLE_PROJECTION_OFFSET = 23040.5
NORTH = 44.0
SOUTH = 0.0
WEST = 0.0
EAST = 90.0
TOPO_ROW_BYTES = SAMPLES * 2
COUNT_ROW_BYTES = SAMPLES
TOPO_TOTAL_BYTES = LINES * TOPO_ROW_BYTES
COUNT_TOTAL_BYTES = LINES * COUNT_ROW_BYTES
DEFAULT_LAT = 18.3995
DEFAULT_LON = 77.42975
USER_AGENT = "UnifiedParallelFoundry-E544/1.0 (bounded scientific data request)"


def nearest_integer(value: float) -> int:
    """Round nonnegative pixel coordinates half-up, avoiding bankers' rounding."""
    if not math.isfinite(value) or value < 0:
        raise ValueError("pixel coordinate must be finite and nonnegative")
    return math.floor(value + 0.5)


def coordinate_to_pixel(latitude: float, longitude: float) -> tuple[int, int]:
    """Return zero-based (row, col) for PDS simple-cylindrical pixel centres."""
    if not (SOUTH <= latitude <= NORTH and WEST <= longitude <= EAST):
        raise ValueError("coordinate lies outside MEGT/MEGC44N000HB coverage")
    line = (CENTER_LATITUDE - latitude) * PIXELS_PER_DEGREE + LINE_PROJECTION_OFFSET
    sample = (longitude - CENTER_LONGITUDE) * PIXELS_PER_DEGREE + SAMPLE_PROJECTION_OFFSET
    row = nearest_integer(line) - 1
    col = nearest_integer(sample) - 1
    if not (0 <= row < LINES and 0 <= col < SAMPLES):
        raise ValueError("coordinate maps outside raster dimensions")
    return row, col


def pixel_center(row: int, col: int) -> tuple[float, float]:
    if not (0 <= row < LINES and 0 <= col < SAMPLES):
        raise ValueError("pixel index outside raster dimensions")
    line = row + 1
    sample = col + 1
    latitude = CENTER_LATITUDE + (LINE_PROJECTION_OFFSET - line) / PIXELS_PER_DEGREE
    longitude = CENTER_LONGITUDE + (sample - SAMPLE_PROJECTION_OFFSET) / PIXELS_PER_DEGREE
    return latitude, longitude


def parse_range_response(status: int, headers: dict, payload: bytes, start: int, end: int, total: int) -> bytes:
    expected_len = end - start + 1
    expected_range = f"bytes {start}-{end}/{total}"
    if status != 206:
        raise RuntimeError(f"RANGE_NOT_HONORED status={status}; expected 206")
    actual_range = next((value for key, value in headers.items() if key.lower() == "content-range"), None)
    if actual_range != expected_range:
        raise RuntimeError(f"CONTENT_RANGE_MISMATCH expected={expected_range!r} actual={actual_range!r}")
    if len(payload) != expected_len:
        raise RuntimeError(f"RANGE_LENGTH_MISMATCH expected={expected_len} actual={len(payload)}")
    return payload


def fetch_exact_range(url: str, start: int, end: int, total: int, retries: int = 3) -> bytes:
    expected_len = end - start + 1
    last_error = None
    for attempt in range(retries):
        request = urllib.request.Request(
            url,
            headers={"Range": f"bytes={start}-{end}", "User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                status = getattr(response, "status", response.getcode())
                headers = {key.lower(): value for key, value in response.headers.items()}
                # Bound reads if the server ignores Range; never pull a full tile by accident.
                if status != 206:
                    payload = response.read(33)
                else:
                    payload = response.read(expected_len + 1)
                return parse_range_response(status, headers, payload, start, end, total)
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP_{exc.code}"
            if exc.code not in (429, 500, 502, 503, 504) or attempt + 1 == retries:
                raise RuntimeError(last_error) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = type(exc).__name__
            if attempt + 1 == retries:
                raise RuntimeError(f"NETWORK_TRANSIENT_EXHAUSTED:{last_error}") from exc
        time.sleep(1 + attempt)
    raise RuntimeError(f"NETWORK_TRANSIENT_EXHAUSTED:{last_error}")


def extract_topography(row_bytes: bytes, col: int) -> int:
    if len(row_bytes) != TOPO_ROW_BYTES or not (0 <= col < SAMPLES):
        raise ValueError("invalid topography row or column")
    offset = col * 2
    return int.from_bytes(row_bytes[offset:offset + 2], byteorder="big", signed=True)


def extract_count(row_bytes: bytes, col: int) -> int:
    if len(row_bytes) != COUNT_ROW_BYTES or not (0 <= col < SAMPLES):
        raise ValueError("invalid count row or column")
    return row_bytes[col]


def acquire_patch(latitude: float = DEFAULT_LAT, longitude: float = DEFAULT_LON, radius: int = 2) -> dict:
    if not isinstance(radius, int) or isinstance(radius, bool) or not (0 <= radius <= 10):
        raise ValueError("radius must be an integer from 0 through 10")
    center_row, center_col = coordinate_to_pixel(latitude, longitude)
    row_min, row_max = center_row - radius, center_row + radius
    col_min, col_max = center_col - radius, center_col + radius
    if row_min < 0 or row_max >= LINES or col_min < 0 or col_max >= SAMPLES:
        raise ValueError("requested patch crosses raster boundary")

    topo_rows = {}
    count_rows = {}
    for row in range(row_min, row_max + 1):
        topo_start = row * TOPO_ROW_BYTES
        topo_rows[row] = fetch_exact_range(TOPO_URL, topo_start, topo_start + TOPO_ROW_BYTES - 1, TOPO_TOTAL_BYTES)
        count_start = row * COUNT_ROW_BYTES
        count_rows[row] = fetch_exact_range(COUNT_URL, count_start, count_start + COUNT_ROW_BYTES - 1, COUNT_TOTAL_BYTES)

    cells = []
    observed_topography = []
    counts = []
    for row in range(row_min, row_max + 1):
        for col in range(col_min, col_max + 1):
            count = extract_count(count_rows[row], col)
            topo = extract_topography(topo_rows[row], col)
            cell_lat, cell_lon = pixel_center(row, col)
            cells.append({
                "row": row,
                "col": col,
                "latitude_planetocentric_deg": round(cell_lat, 8),
                "longitude_east_deg": round(cell_lon, 8),
                "topography_m_above_gmm3_areoid": topo,
                "mola_observation_count": count,
                "observed_bin": count > 0,
            })
            counts.append(count)
            if count > 0:
                observed_topography.append(topo)

    return {
        "experiment": "E544_MOLA_BOUNDED_JEZERO_PATCH",
        "claim_boundary": "MOLA-only source acquisition and count-mask audit; not CTX/HiRISE co-registration, cross-body similarity, analogue recovery, or route safety",
        "target": {"name": "Jezero CTX/HiRISE metadata-envelope overlap centroid", "latitude_planetocentric_deg": latitude, "longitude_east_deg": longitude},
        "window": {"radius_pixels": radius, "rows_inclusive": [row_min, row_max], "cols_inclusive": [col_min, col_max], "cell_count": len(cells)},
        "source": {
            "archive": "NASA PDS Geosciences Node, MGS MOLA MEGDR PDS4 migrated bundle; PDS3 product labels",
            "dataset_id": "MGS-M-MOLA-5-MEGDR-L3-V1.0",
            "topography_product": "MEGT44N000HB.IMG",
            "count_product": "MEGC44N000HB.IMG",
            "topography_label_url": TOPO_LABEL_URL,
            "count_label_url": COUNT_LABEL_URL,
            "topography_data_url": TOPO_URL,
            "count_data_url": COUNT_URL,
            "coordinate_reference": "IAU2000, planetocentric, simple cylindrical, positive east",
            "topography_units": "metres above GMM3 areoid; signed 16-bit big-endian median topography",
            "count_units": "unsigned 8-bit number of observations per bin",
            "resolution": "128 pixels/degree; nominal MAP_SCALE 0.463 km/pixel at equator",
            "topography_file_bytes": TOPO_TOTAL_BYTES,
            "count_file_bytes": COUNT_TOTAL_BYTES,
            "topography_record_bytes": TOPO_ROW_BYTES,
            "count_record_bytes": COUNT_ROW_BYTES,
            "missingness": "topography supplies interpolated values in bins with no observations; exclude count=0 bins from observed-topography summaries",
        },
        "summary": {
            "cells": len(cells),
            "observed_bins": sum(1 for value in counts if value > 0),
            "zero_count_bins": sum(1 for value in counts if value == 0),
            "median_observation_count": statistics.median(counts),
            "observed_topography_min_m": min(observed_topography) if observed_topography else None,
            "observed_topography_median_m": statistics.median(observed_topography) if observed_topography else None,
            "observed_topography_max_m": max(observed_topography) if observed_topography else None,
        },
        "cells": cells,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--latitude", type=float, default=DEFAULT_LAT)
    parser.add_argument("--longitude", type=float, default=DEFAULT_LON)
    parser.add_argument("--radius", type=int, default=2)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = acquire_patch(args.latitude, args.longitude, args.radius)
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
