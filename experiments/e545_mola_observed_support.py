"""E545: bounded PDS MOLA topography/count sampling at the Jezero CTX/HiRISE overlap centroid."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
from pathlib import Path
from urllib.parse import urlsplit

import numpy as np
import requests

BASE = "https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg128"
HOST = "pds-geosciences.wustl.edu"
TOPO_NAME = "megt44n000hb"
COUNT_NAME = "megc44n000hb"
TOPO_IMG = f"{BASE}/{TOPO_NAME}.img"
TOPO_LABEL = f"{BASE}/{TOPO_NAME}.lbl"
COUNT_IMG = f"{BASE}/{COUNT_NAME}.img"
COUNT_LABEL = f"{BASE}/{COUNT_NAME}.lbl"

# Center of the published CTX/2025-HiRISE metadata-envelope intersection.
CENTER_LAT = 18.3995
CENTER_LON = 77.27025
WINDOW_SIZE = 33
PIXELS_PER_DEGREE = 128
FILE_RECORDS = 5632
LINE_SAMPLES = 11520
TOPO_RECORD_BYTES = 23040
COUNT_RECORD_BYTES = 11520
MAX_LABEL_BYTES = 64_000
MAX_RANGE_BYTES = 800_000
MAX_TOTAL_RANGE_BYTES = 1_200_000
USER_AGENT = "Unified-Parallel-Foundry-E545/1.0"


class AcquisitionError(RuntimeError):
    def __init__(self, kind: str, message: str, *, outcome: str = "ERROR", details: dict | None = None):
        super().__init__(message)
        self.kind = kind
        self.outcome = outcome
        self.details = details or {}


def validate_url(url: str, expected_name: str, suffix: str) -> None:
    parsed = urlsplit(url)
    expected_path = f"/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg128/{expected_name}.{suffix}"
    if (
        parsed.scheme != "https"
        or parsed.hostname != HOST
        or parsed.port not in (None, 443)
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path != expected_path
    ):
        raise ValueError("URL is outside the exact pinned PDS Geosciences MOLA object allowlist")


def parse_pds_label(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().upper()
        value = value.split("/*", 1)[0].strip()
        if key and value:
            fields[key] = value.strip().strip('"')
    return fields


def _number(fields: dict[str, str], key: str) -> float:
    if key not in fields:
        raise ValueError(f"PDS label is missing {key}")
    match = re.match(r"^\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))", fields[key])
    if not match:
        raise ValueError(f"PDS label field {key} is not numeric")
    return float(match.group(1))


def validate_label(text: str, kind: str) -> dict[str, str]:
    fields = parse_pds_label(text)
    expected_record_bytes = TOPO_RECORD_BYTES if kind == "topography" else COUNT_RECORD_BYTES
    expected_sample_type = "MSB_INTEGER" if kind == "topography" else "UNSIGNED_INTEGER"
    expected_sample_bits = 16 if kind == "topography" else 8

    exact_strings = {
        "PDS_VERSION_ID": "PDS3",
        "TARGET_NAME": "MARS",
        "INSTRUMENT_ID": "MOLA",
        "PRODUCT_VERSION_ID": "2.0",
        "MAP_PROJECTION_TYPE": "SIMPLE CYLINDRICAL",
        "POSITIVE_LONGITUDE_DIRECTION": "EAST",
        "COORDINATE_SYSTEM_NAME": "PLANETOCENTRIC",
        "SAMPLE_TYPE": expected_sample_type,
    }
    for key, expected in exact_strings.items():
        if fields.get(key, "").upper() != expected:
            raise ValueError(f"{kind} PDS label {key} mismatch: {fields.get(key)!r}")

    exact_numbers = {
        "FILE_RECORDS": FILE_RECORDS,
        "RECORD_BYTES": expected_record_bytes,
        "LINES": FILE_RECORDS,
        "LINE_SAMPLES": LINE_SAMPLES,
        "SAMPLE_BITS": expected_sample_bits,
        "MAP_RESOLUTION": PIXELS_PER_DEGREE,
        "MAXIMUM_LATITUDE": 44,
        "MINIMUM_LATITUDE": 0,
        "WESTERNMOST_LONGITUDE": 0,
        "EASTERNMOST_LONGITUDE": 90,
        "LINE_PROJECTION_OFFSET": 5632.5,
        "SAMPLE_PROJECTION_OFFSET": 23040.5,
    }
    for key, expected in exact_numbers.items():
        if not math.isclose(_number(fields, key), float(expected), rel_tol=0, abs_tol=1e-9):
            raise ValueError(f"{kind} PDS label {key} mismatch")

    if kind == "topography" and fields.get("UNIT", "").upper() != "METER":
        raise ValueError("topography PDS label does not declare metre units")
    return fields


def pixel_index(lat: float, lon: float, *, max_lat: float = 44.0, west_lon: float = 0.0, ppd: int = 128) -> tuple[int, int]:
    if not all(math.isfinite(v) for v in (lat, lon, max_lat, west_lon, float(ppd))) or ppd <= 0:
        raise ValueError("coordinates and resolution must be finite; resolution must be positive")
    if not (0.0 < lat < max_lat and west_lon <= lon < west_lon + 90.0):
        raise ValueError("coordinate lies outside the pinned 44N-to-0N, 0E-to-90E MOLA tile")
    # PDS3 projection offsets place pixel boundaries at the tile edges.
    row = math.floor((max_lat - lat) * ppd + 1.0)
    col = math.floor((lon - west_lon) * ppd + 1.0)
    if not (1 <= row <= FILE_RECORDS and 1 <= col <= LINE_SAMPLES):
        raise ValueError("computed pixel index lies outside the PDS tile")
    return row, col


def make_window(center_row: int, center_col: int, size: int = WINDOW_SIZE) -> dict[str, int]:
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0 or size % 2 != 1:
        raise ValueError("window size must be a positive odd integer")
    half = size // 2
    row_start, row_end = center_row - half, center_row + half
    col_start, col_end = center_col - half, center_col + half
    if row_start < 1 or row_end > FILE_RECORDS or col_start < 1 or col_end > LINE_SAMPLES:
        raise ValueError("sample window extends outside the pinned MOLA tile")
    return {
        "row_start": row_start,
        "row_end": row_end,
        "col_start": col_start,
        "col_end": col_end,
        "height": size,
        "width": size,
    }


def byte_range(row_start: int, row_end: int, record_bytes: int) -> tuple[int, int]:
    if not (1 <= row_start <= row_end <= FILE_RECORDS) or record_bytes <= 0:
        raise ValueError("invalid PDS row range")
    start = (row_start - 1) * record_bytes
    end = row_end * record_bytes - 1
    return start, end


def _get_with_retries(session: requests.Session, url: str, **kwargs):
    for attempt in range(3):
        try:
            return session.get(url, **kwargs)
        except (requests.ConnectionError, requests.Timeout) as exc:
            if attempt == 2:
                raise AcquisitionError(
                    "NETWORK_TRANSIENT",
                    "PDS request failed after three bounded transport attempts",
                    details={"exception_type": type(exc).__name__},
                ) from exc
            time.sleep(1 + attempt)


def fetch_label(session: requests.Session, url: str, name: str) -> tuple[str, dict]:
    validate_url(url, name, "lbl")
    response = _get_with_retries(
        session,
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
        timeout=(10, 30),
        stream=True,
        allow_redirects=False,
    )
    try:
        status = int(response.status_code)
        if status in (403, 404, 410):
            raise AcquisitionError(
                f"HTTP_{status}",
                "Pinned public PDS label returned an HTTP error",
                outcome=f"NEGATIVE_RESULT_HTTP_{status}",
                details={"http_status": status},
            )
        if status != 200:
            raise AcquisitionError(
                f"HTTP_{status}",
                "Pinned PDS label did not return HTTP 200",
                details={"http_status": status},
            )
        declared = response.headers.get("Content-Length")
        if declared and int(declared) > MAX_LABEL_BYTES:
            raise AcquisitionError("LABEL_TOO_LARGE", "PDS label exceeded the 64 KB bound")
        content = response.content
        if len(content) > MAX_LABEL_BYTES:
            raise AcquisitionError("LABEL_TOO_LARGE", "PDS label exceeded the 64 KB bound")
        return content.decode("utf-8"), {
            "http_status": status,
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "content_type": response.headers.get("Content-Type"),
        }
    finally:
        response.close()


def fetch_exact_range(
    session: requests.Session,
    url: str,
    name: str,
    start: int,
    end: int,
    expected_total: int,
) -> tuple[bytes, dict]:
    validate_url(url, name, "img")
    expected_bytes = end - start + 1
    if expected_bytes <= 0 or expected_bytes > MAX_RANGE_BYTES:
        raise ValueError("requested byte range is empty or exceeds the per-object safety bound")
    response = _get_with_retries(
        session,
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/octet-stream",
            "Accept-Encoding": "identity",
            "Range": f"bytes={start}-{end}",
        },
        timeout=(15, 60),
        stream=True,
        allow_redirects=False,
    )
    try:
        status = int(response.status_code)
        if status in (403, 404, 410):
            raise AcquisitionError(
                f"HTTP_{status}",
                "Pinned public PDS raster returned an HTTP error",
                outcome=f"NEGATIVE_RESULT_HTTP_{status}",
                details={"http_status": status},
            )
        if status == 200:
            raise AcquisitionError(
                "RANGE_IGNORED",
                "PDS server ignored the bounded Range request; full raster download was refused",
                outcome="NEGATIVE_RESULT_RANGE_IGNORED",
                details={"http_status": status, "full_download_refused": True},
            )
        if status != 206:
            raise AcquisitionError(
                f"HTTP_{status}",
                "PDS raster did not return HTTP 206 Partial Content",
                details={"http_status": status},
            )

        content_range = response.headers.get("Content-Range", "")
        match = re.fullmatch(r"bytes\s+(\d+)-(\d+)/(\d+)", content_range.strip(), flags=re.IGNORECASE)
        if not match:
            raise AcquisitionError("INVALID_CONTENT_RANGE", "PDS response omitted a valid Content-Range")
        actual_start, actual_end, actual_total = map(int, match.groups())
        if (actual_start, actual_end, actual_total) != (start, end, expected_total):
            raise AcquisitionError(
                "CONTENT_RANGE_MISMATCH",
                "PDS Content-Range does not match the exact pinned row range and label dimensions",
                details={
                    "expected": [start, end, expected_total],
                    "actual": [actual_start, actual_end, actual_total],
                },
            )
        declared = response.headers.get("Content-Length")
        if declared and int(declared) != expected_bytes:
            raise AcquisitionError("CONTENT_LENGTH_MISMATCH", "PDS range Content-Length is inconsistent")
        data = response.content
        if len(data) != expected_bytes:
            raise AcquisitionError(
                "RANGE_BYTE_COUNT_MISMATCH",
                "PDS response byte count does not match the requested inclusive range",
                details={"expected_bytes": expected_bytes, "actual_bytes": len(data)},
            )
        return data, {
            "http_status": status,
            "content_range": content_range,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    finally:
        response.close()


def extract_window(raw_rows: bytes, *, record_bytes: int, line_samples: int, window: dict, kind: str) -> np.ndarray:
    expected = window["height"] * record_bytes
    if len(raw_rows) != expected:
        raise ValueError(f"{kind} range has {len(raw_rows)} bytes; expected {expected}")
    dtype = ">i2" if kind == "topography" else "u1"
    matrix = np.frombuffer(raw_rows, dtype=dtype).reshape(window["height"], line_samples)
    return matrix[:, window["col_start"] - 1 : window["col_end"]].copy()


def summarize_window(topography_m: np.ndarray, counts: np.ndarray) -> dict:
    if topography_m.shape != counts.shape or topography_m.ndim != 2:
        raise ValueError("topography and count windows must have the same two-dimensional shape")
    observed = counts > 0
    observed_counts = counts[observed].astype(np.int64)
    observed_topography = topography_m[observed].astype(np.int64)
    total_bins = int(counts.size)
    observed_bins = int(np.count_nonzero(observed))
    summary = {
        "window_bins": total_bins,
        "observed_bins_count_gt_zero": observed_bins,
        "zero_count_bins": total_bins - observed_bins,
        "observed_bin_fraction": observed_bins / total_bins,
        "count_sum_across_bins": int(observed_counts.sum()) if observed_bins else 0,
        "positive_count_min": int(observed_counts.min()) if observed_bins else None,
        "positive_count_median": float(np.median(observed_counts)) if observed_bins else None,
        "positive_count_max": int(observed_counts.max()) if observed_bins else None,
        "topography_all_bins_min_m": int(topography_m.min()),
        "topography_all_bins_median_m": float(np.median(topography_m)),
        "topography_all_bins_max_m": int(topography_m.max()),
        "topography_observed_bins_min_m": int(observed_topography.min()) if observed_bins else None,
        "topography_observed_bins_median_m": float(np.median(observed_topography)) if observed_bins else None,
        "topography_observed_bins_max_m": int(observed_topography.max()) if observed_bins else None,
        "topography_observed_bins_mean_m": float(np.mean(observed_topography)) if observed_bins else None,
        "topography_observed_bins_std_m": float(np.std(observed_topography)) if observed_bins else None,
        "interpolated_topography_excluded_from_observed_statistics": True,
    }
    return summary


def run_experiment(session: requests.Session | None = None) -> dict:
    session = session or requests.Session()
    close_session = session is not None
    receipt: dict = {
        "experiment": "E545",
        "question": "Does the pinned MOLA 128 ppd topography/count pair contain observed-shot support in a bounded window centered inside the published Jezero CTX/HiRISE overlap envelope?",
        "source": {
            "publisher": "PDS Geosciences Node, Washington University in St. Louis",
            "dataset": "MGS MOLA Mission Experiment Gridded Data Record, version 2.0",
            "topography_image": TOPO_IMG,
            "topography_label": TOPO_LABEL,
            "counts_image": COUNT_IMG,
            "counts_label": COUNT_LABEL,
            "acquisition_start": "1997-09-15",
            "acquisition_stop": "2001-06-30",
            "coordinate_reference": "IAU2000; 3396.0 km spherical reference; simple cylindrical; planetocentric latitude; positive-east longitude",
            "topography_definition": "planetary radius minus GMM3 areoid radius; label-declared metres",
            "counts_definition": "number of MOLA observations in each latitude/longitude bin",
        },
        "window": {
            "center_latitude_planetocentric_deg": CENTER_LAT,
            "center_longitude_positive_east_deg": CENTER_LON,
            "pixels_per_degree": PIXELS_PER_DEGREE,
            "window_size_pixels": WINDOW_SIZE,
            "nominal_equatorial_spacing_m": 463.0,
            "nominal_local_east_west_spacing_m": 463.0 * math.cos(math.radians(CENTER_LAT)),
            "nominal_north_south_spacing_m": 463.0,
        },
        "acquisition": {},
        "experiment_completed": False,
        "experiment_outcome": "NOT_RUN",
        "claim_state": {
            "bounded_mola_range_ingestion": "NOT YET MEASURED",
            "jezero_window_observed_shot_support": "NOT YET MEASURED",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
            "local_validation_advantage": "NOT YET PROVEN",
            "route_safety": "NOT CLAIMED",
        },
        "limitations": [
            "This is one MOLA window, not a cross-body similarity or known-site-recovery experiment.",
            "MOLA uses IAU2000 and a 3396.0 km sphere; the pinned CTX/HiRISE metadata uses Mars 2015 and a 3396.19 km sphere. No reference transformation or raster registration is performed.",
            "MOLA bins with zero observations contain interpolated topography; observed-support statistics use only bins whose companion count is greater than zero.",
            "The 55% equatorial observed-bin statement in the global label is not substituted for the measured local count window.",
            "No raw raster bytes or pixel arrays are written to the repository or uploaded; only a compact metadata/statistics receipt is retained.",
        ],
    }
    try:
        topo_label_text, topo_label_receipt = fetch_label(session, TOPO_LABEL, TOPO_NAME)
        count_label_text, count_label_receipt = fetch_label(session, COUNT_LABEL, COUNT_NAME)
        topo_fields = validate_label(topo_label_text, "topography")
        count_fields = validate_label(count_label_text, "counts")
        receipt["acquisition"]["topography_label"] = topo_label_receipt
        receipt["acquisition"]["counts_label"] = count_label_receipt

        center_row, center_col = pixel_index(CENTER_LAT, CENTER_LON)
        window = make_window(center_row, center_col)
        receipt["window"].update({
            "center_row_1_based": center_row,
            "center_col_1_based": center_col,
            **window,
            "north_edge_latitude_deg": 44.0 - (window["row_start"] - 1) / PIXELS_PER_DEGREE,
            "south_edge_latitude_deg": 44.0 - window["row_end"] / PIXELS_PER_DEGREE,
            "west_edge_longitude_deg": (window["col_start"] - 1) / PIXELS_PER_DEGREE,
            "east_edge_longitude_deg": window["col_end"] / PIXELS_PER_DEGREE,
        })

        topo_start, topo_end = byte_range(window["row_start"], window["row_end"], TOPO_RECORD_BYTES)
        count_start, count_end = byte_range(window["row_start"], window["row_end"], COUNT_RECORD_BYTES)
        if (topo_end - topo_start + 1) + (count_end - count_start + 1) > MAX_TOTAL_RANGE_BYTES:
            raise ValueError("combined MOLA range request exceeds the 1.2 MB experiment bound")

        topo_total = FILE_RECORDS * TOPO_RECORD_BYTES
        count_total = FILE_RECORDS * COUNT_RECORD_BYTES
        topo_raw, topo_range_receipt = fetch_exact_range(
            session, TOPO_IMG, TOPO_NAME, topo_start, topo_end, topo_total
        )
        count_raw, count_range_receipt = fetch_exact_range(
            session, COUNT_IMG, COUNT_NAME, count_start, count_end, count_total
        )
        receipt["acquisition"]["topography_range"] = topo_range_receipt
        receipt["acquisition"]["counts_range"] = count_range_receipt

        topography = extract_window(
            topo_raw,
            record_bytes=TOPO_RECORD_BYTES,
            line_samples=LINE_SAMPLES,
            window=window,
            kind="topography",
        )
        counts = extract_window(
            count_raw,
            record_bytes=COUNT_RECORD_BYTES,
            line_samples=LINE_SAMPLES,
            window=window,
            kind="counts",
        )
        summary = summarize_window(topography, counts)
        receipt["sample_summary"] = summary
        receipt["experiment_completed"] = True
        receipt["experiment_outcome"] = (
            "MOLA_OBSERVED_SUPPORT_MEASURED"
            if summary["observed_bins_count_gt_zero"] > 0
            else "MOLA_ZERO_OBSERVATION_WINDOW_MEASURED"
        )
        receipt["claim_state"]["bounded_mola_range_ingestion"] = "SUPPORTED"
        receipt["claim_state"]["jezero_window_observed_shot_support"] = (
            "SUPPORTED" if summary["observed_bins_count_gt_zero"] > 0 else "NOT SUPPORTED FOR THIS WINDOW"
        )
    except AcquisitionError as exc:
        receipt["experiment_outcome"] = exc.outcome if exc.outcome.startswith("NEGATIVE_RESULT") else "ERROR"
        receipt["error"] = {"kind": exc.kind, "message": str(exc), **exc.details}
        receipt["experiment_completed"] = receipt["experiment_outcome"].startswith("NEGATIVE_RESULT")
    except Exception as exc:
        receipt["experiment_outcome"] = "ERROR"
        receipt["error"] = {"kind": type(exc).__name__, "message": str(exc)}
    finally:
        if close_session:
            session.close()
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path(".artifacts/e545/receipt.json"))
    args = parser.parse_args()
    receipt = run_experiment()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False))
    return 1 if receipt["experiment_outcome"] == "ERROR" else 0


if __name__ == "__main__":
    raise SystemExit(main())
