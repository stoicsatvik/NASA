"""E291: read-only official Diviner temperature-anomaly source access gate.

This is pre-event dataset feasibility research, NOT a Space Apps solution.
Never infer thermal inertia, pixel coordinates, or Earth/Mars comparability
from an undocumented three-column text file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

MAX_BYTES = 25_000_000
SOURCES = {
    "maximum_temperature_anomaly": "https://luna1.diviner.ucla.edu/~jpierre/diviner/level4_raster_data/diviner_tbol_max_anom.xyz",
    "minimum_temperature_anomaly": "https://luna1.diviner.ucla.edu/~jpierre/diviner/level4_raster_data/diviner_tbol_min_anom.xyz",
}
PROVENANCE = [
    "https://www.diviner.ucla.edu/data",
    "https://www.diviner.ucla.edu/single-post/2018/04/20/new-diviner-level-4-data-products",
    "https://pds-geosciences.wustl.edu/missions/lro/diviner.htm",
]


def parse_numeric_triplets(raw: bytes) -> dict:
    """Shape-only audit: columns deliberately have NO assigned physical units."""
    if not raw or raw.lstrip().lower().startswith((b"<!doctype", b"<html", b"<?xml")):
        raise ValueError("not a numeric XYZ data file")
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError("not UTF-8 numeric XYZ") from exc
    mins = [float("inf")] * 3
    maxs = [float("-inf")] * 3
    count = 0
    for line in lines:
        row = line.strip()
        if not row or row.startswith(("#", "%", ";")):
            continue
        parts = row.replace(",", " ").split()
        if len(parts) != 3:
            raise ValueError("unexpected number of columns")
        try:
            vals = [float(p) for p in parts]
        except ValueError as exc:
            raise ValueError("nonnumeric row") from exc
        if not all(math.isfinite(v) for v in vals):
            raise ValueError("nonfinite numeric value")
        for j, value in enumerate(vals):
            mins[j] = min(mins[j], value)
            maxs[j] = max(maxs[j], value)
        count += 1
    if count < 1:
        raise ValueError("no numeric observations")
    return {
        "rows": count, "columns": 3,
        "column_min_uninterpreted": mins, "column_max_uninterpreted": maxs,
        "units_verified": False, "coordinate_order_verified": False,
    }


def probe(name: str, url: str) -> dict:
    result = {"source_name": name, "url": url, "ingested": False}
    try:
        request = Request(url, headers={
            "User-Agent": "NASA-E291-ReadOnly-Research/1.0",
            "Accept": "text/plain,application/octet-stream",
        })
        with urlopen(request, timeout=45) as response:
            result["http_status"] = response.status
            result["content_type"] = response.headers.get("Content-Type", "")
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("bounded download exceeded 25 MB")
        result["bytes"] = len(raw)
        result["sha256"] = hashlib.sha256(raw).hexdigest()
        result["shape_audit"] = parse_numeric_triplets(raw)
        result["ingested"] = True
        result["status"] = "NUMERIC_TRIPLETS_INGESTED_UNINTERPRETED"
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
        result["status"] = "SOURCE_UNAVAILABLE_OR_UNVERIFIED"
        result["error_type"] = type(exc).__name__
        if isinstance(exc, HTTPError):
            result["http_status"] = exc.code
        result["error"] = str(exc)[:160]
    return result



PDS_STN_BASE = (
    "https://pds-geosciences.wustl.edu/lro/"
    "urn-nasa-pds-lro_diviner_derived1/data_derived_gdr_l3/cylindrical/img/"
)
PDS_STN_NAME = "dgdr_stn_avg_cyl_032_img"


def validate_pds_stn_label(text: str) -> dict:
    """Require exact published geometry, encoding, units and missing value."""
    expected = {
        "LINES": "3840",
        "LINE_SAMPLES": "11520",
        "SAMPLE_TYPE": "LSB_INTEGER",
        "SAMPLE_BITS": "16",
        "UNIT": "K",
        "SCALING_FACTOR": "0.02",
        "OFFSET": "0.00",
        "MISSING_CONSTANT": "-32768",
        "MAP_RESOLUTION": "32",
        "MAP_PROJECTION_TYPE": '"SIMPLE CYLINDRICAL"',
    }
    for key, value in expected.items():
        match = re.search(r"^[ \t]*" + re.escape(key) + r"[ \t]*=[ \t]*(.+)$",
                          text, re.MULTILINE)
        if match is None or match.group(1).strip().split(" <")[0] != value:
            raise ValueError(f"PDS label {key} mismatch")
    if "deviation of rock-free regolith surface" not in text:
        raise ValueError("PDS anomaly semantics absent")
    return {
        "lines": 3840, "line_samples": 11520,
        "sample_type": "LSB_INTEGER", "sample_bits": 16,
        "unit": "K", "scaling_factor": 0.02, "offset": 0.0,
        "missing_constant": -32768, "projection": "SIMPLE CYLINDRICAL",
        "pixels_per_degree": 32,
        "semantic": "NIGHTTIME REGOLITH TEMPERATURE DEVIATION, NOT ABSOLUTE TEMPERATURE",
    }


def probe_pds_stn() -> dict:
    """Read one equatorial 32ppd row by HTTP Range; never fetch full 88MB."""
    label_url = PDS_STN_BASE + PDS_STN_NAME + ".lbl"
    img_url = PDS_STN_BASE + PDS_STN_NAME + ".img"
    result = {"label_url": label_url, "image_url": img_url, "ingested": False}
    try:
        with urlopen(Request(label_url, headers={
            "User-Agent": "NASA-E291-ReadOnly-Research/1.0",
        }), timeout=35) as response:
            label_raw = response.read(20_001)
        if len(label_raw) > 20_000:
            raise ValueError("PDS label exceeds bounded limit")
        metadata = validate_pds_stn_label(label_raw.decode("utf-8"))
        result["label_sha256"] = hashlib.sha256(label_raw).hexdigest()
        result["metadata"] = metadata
        row = 1920  # Near equator, within published +/-60 degree coverage.
        size = metadata["line_samples"] * 2
        start = row * size
        end = start + size - 1
        with urlopen(Request(img_url, headers={
            "User-Agent": "NASA-E291-ReadOnly-Research/1.0",
            "Range": f"bytes={start}-{end}",
        }), timeout=45) as response:
            result["http_status"] = response.status
            content_range = response.headers.get("Content-Range", "")
            if response.status != 206 or not content_range.startswith(f"bytes {start}-{end}/"):
                raise ValueError("server did not honor exact byte-range request")
            raw = response.read(size + 1)
        if len(raw) != size:
            raise ValueError("unexpected sampled-row length")
        values = struct.unpack("<" + str(metadata["line_samples"]) + "h", raw)
        valid = [v * metadata["scaling_factor"] for v in values
                 if v != metadata["missing_constant"]]
        result["sample"] = {
            "row_index": row, "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "valid_cells": len(valid), "missing_cells": len(values) - len(valid),
            "minimum_anomaly_K": min(valid) if valid else None,
            "maximum_anomaly_K": max(valid) if valid else None,
            "sample_is_not_global_coverage": True,
        }
        result["ingested"] = bool(valid)
        result["status"] = "PDS_ROW_INGESTED" if valid else "PDS_ROW_ALL_MISSING"
    except (HTTPError, URLError, TimeoutError, ValueError, UnicodeError, OSError) as exc:
        result["status"] = "PDS_ACCESS_OR_METADATA_UNVERIFIED"
        result["error_type"] = type(exc).__name__
        if isinstance(exc, HTTPError):
            result["http_status"] = exc.code
        result["error"] = str(exc)[:160]
    return result


def audit() -> dict:
    samples = [probe(name, url) for name, url in SOURCES.items()]
    pds = probe_pds_stn()
    return {
        "experiment": "E291 Diviner thermal-anomaly access gate",
        "sources": samples, "pds_stn": pds, "provenance": PROVENANCE,
        "real_pds_thermal_row_ingested": pds["ingested"],
        "access_count": sum(s["ingested"] for s in samples),
        "both_accessible": all(s["ingested"] for s in samples),
        "thermal_units_verified": False,
        "thermal_inertia_estimated": False,
        "instrument_comparability_established": False,
        "e001_known_analogue_recovery": "NOT YET MEASURED",
        "cross_body_similarity": "NOT YET PROVEN",
        "limitations": [
            "UCLA Level 4 temperature anomalies are not THEMIS thermal inertia or absolute temperature.",
            "Text triplets are deliberately not geolocated or assigned units without format metadata.",
            "A successful download is not a physical-descriptor harmonization.",
            "A failed URL is an access observation, not proof the official archive lacks the data.",
            "PDS STN is a nighttime temperature anomaly in K, not absolute surface temperature or thermal inertia.",
            "One equatorial raster row is not global missingness or an independent site benchmark.",
            "No Earth/Moon/Mars known-site labels, negative controls or field data.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit()
    encoded = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n")
    print(encoded)


if __name__ == "__main__":
    main()
