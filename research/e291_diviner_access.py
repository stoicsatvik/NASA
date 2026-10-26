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


def audit() -> dict:
    samples = [probe(name, url) for name, url in SOURCES.items()]
    return {
        "experiment": "E291 Diviner thermal-anomaly access gate",
        "sources": samples, "provenance": PROVENANCE,
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
