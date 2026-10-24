"""E210: independent higher-resolution MOLA MEG016 count-mask test."""
from __future__ import annotations
import argparse
from array import array
import hashlib
import json
from pathlib import Path
import re
import sys
from e209_mola_mask_ablation import latitude_coverage, region_ablation

BASE = "https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/meg016/"
ROWS, COLS = 2880, 5760


def field(label, key):
    match = re.search(r"(?m)^\s*" + re.escape(key) + r"\s*=\s*(.*?)\s*$", label)
    if not match:
        raise ValueError("missing PDS field " + key)
    return match.group(1).strip().strip('"')


def validate_label(label, product, is_topography):
    expected = {
        "PRODUCT_ID": product.upper(), "PRODUCT_VERSION_ID": "2.0",
        "SAMPLE_TYPE": "MSB_INTEGER", "SAMPLE_BITS": "16",
        "LINES": str(ROWS), "LINE_SAMPLES": str(COLS),
        "RECORD_BYTES": str(COLS * 2),
        "MAP_PROJECTION_TYPE": "SIMPLE CYLINDRICAL",
        "COORDINATE_SYSTEM_NAME": "PLANETOCENTRIC",
        "POSITIVE_LONGITUDE_DIRECTION": "EAST",
        "MAP_RESOLUTION": "16.0", "LINE_PROJECTION_OFFSET": "1440.5",
        "SAMPLE_PROJECTION_OFFSET": "2880.5",
    }
    for key, expected_value in expected.items():
        actual = field(label, key).split(" <")[0]
        if actual != expected_value:
            raise ValueError(f"{product}: invalid {key}: {actual!r} != {expected_value!r}")
    if is_topography and field(label, "UNIT") != "METER":
        raise ValueError("unexpected elevation units")


def decode_msb16(blob, expected_samples):
    if len(blob) != expected_samples * 2:
        raise ValueError(f"expected {expected_samples*2} bytes, got {len(blob)}")
    values = array("h")
    if values.itemsize != 2:
        raise RuntimeError("host short is not 16-bit")
    values.frombytes(blob)
    if sys.byteorder == "little":
        values.byteswap()
    return values


def main():
    parser = argparse.ArgumentParser()
    for key in ("topography", "counts", "topography-label", "counts-label"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    top_label = args.topography_label.read_text("ascii")
    count_label = args.counts_label.read_text("ascii")
    validate_label(top_label, "MEGT90N000EB.IMG", True)
    validate_label(count_label, "MEGC90N000EB.IMG", False)
    raw_top, raw_counts = args.topography.read_bytes(), args.counts.read_bytes()
    top = decode_msb16(raw_top, ROWS * COLS)
    counts = decode_msb16(raw_counts, ROWS * COLS)
    if any(c < 0 for c in counts):
        raise ValueError("negative observation counts: stop and inspect encoding")
    observed = sum(c > 0 for c in counts)
    results = {
        "experiment": "E210 MEG016 resolution falsification of E209 coarse mask null",
        "source": BASE, "shape": [ROWS, COLS], "pixels_per_degree": 16,
        "elevation_unit": "m above MOLA areoid",
        "counts_unit": "ground-return observations per bin",
        "topography_sha256": hashlib.sha256(raw_top).hexdigest(),
        "counts_sha256": hashlib.sha256(raw_counts).hexdigest(),
        "topography_label_sha256": hashlib.sha256(args.topography_label.read_bytes()).hexdigest(),
        "counts_label_sha256": hashlib.sha256(args.counts_label.read_bytes()).hexdigest(),
        "total_cells": ROWS * COLS, "observed_cells": observed,
        "interpolated_cells": ROWS * COLS - observed,
        "observed_fraction": observed / (ROWS * COLS),
        "latitude_5deg_coverage": latitude_coverage(counts, ROWS, COLS, band_rows=80),
        "global_ablation": region_ablation(top, counts, ROWS, COLS, 0, ROWS, (16, 32, 64)),
        "equatorial_plus_minus_16_deg": region_ablation(top, counts, ROWS, COLS, 1184, 1696, (16, 32, 64)),
        "limitations": [
            "16ppd still uses interpolated topography where MEGC=0.",
            "Elevation standard deviation is not physical-scale-normalized roughness.",
            "Changing measured-cell sample size can bias standard deviation.",
            "No Moon or Earth dataset ingested; E001 NOT YET MEASURED.",
            "No cross-body analogue discovery established.",
        ],
    }
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
