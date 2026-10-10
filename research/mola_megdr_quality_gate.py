"""Quality-gated reader for official MOLA MEG004 paired gridded products.

The topography grid interpolates empty cells. The paired counts grid distinguishes
actual ground-return bins from interpolated values. No analogue claims are made.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

ARCHIVE = "https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg004/"


def metadata(label: Path, product: str) -> dict:
    text = label.read_text(encoding="ascii")

    def field(name: str) -> str:
        match = re.search(r"(?m)^\\s*" + re.escape(name) + r"\\s*=\\s*(.*?)\\s*$", text)
        if not match:
            raise ValueError(f"missing {name} in {label}")
        return match.group(1).strip().strip('"')

    if field("PRODUCT_ID").upper() != product.upper():
        raise ValueError("wrong product label")
    if field("PRODUCT_VERSION_ID") != "2.0":
        raise ValueError("not final MEGDR version")
    if field("SAMPLE_TYPE") != "MSB_INTEGER" or int(field("SAMPLE_BITS")) != 16:
        raise ValueError("unsupported binary representation")
    if field("MAP_PROJECTION_TYPE") != "SIMPLE CYLINDRICAL":
        raise ValueError("unsupported projection")
    if field("COORDINATE_SYSTEM_NAME") != "PLANETOCENTRIC":
        raise ValueError("unsupported latitude system")
    if field("POSITIVE_LONGITUDE_DIRECTION") != "EAST":
        raise ValueError("unsupported longitude convention")
    if float(field("MAP_RESOLUTION").split()[0]) != 4.0:
        raise ValueError("unexpected pixels per degree")
    lines, samples = int(field("LINES")), int(field("LINE_SAMPLES"))
    if (lines, samples) != (720, 1440):
        raise ValueError("unexpected MEG004 dimensions")
    if int(field("RECORD_BYTES")) != samples * 2:
        raise ValueError("row-byte mismatch")
    return {"lines": lines, "samples": samples}


def read_grid(path: Path, shape: tuple[int, int]) -> tuple[tuple[int, ...], str]:
    blob = path.read_bytes()
    expected = shape[0] * shape[1] * 2
    if len(blob) != expected:
        raise ValueError(f"{path.name}: expected {expected} bytes, got {len(blob)}")
    return struct.unpack(f">{shape[0] * shape[1]}h", blob), hashlib.sha256(blob).hexdigest()


def analyze(
    topography: Path, counts: Path, topography_label: Path,
    counts_label: Path, min_count: int = 1,
) -> dict:
    if min_count < 1:
        raise ValueError("min_count must be >= 1")
    top_meta = metadata(topography_label, "MEGT90N000CB.IMG")
    count_meta = metadata(counts_label, "MEGC90N000CB.IMG")
    if top_meta != count_meta:
        raise ValueError("topography/count grids not aligned")
    shape = (top_meta["lines"], top_meta["samples"])
    heights, top_sha = read_grid(topography, shape)
    shot_counts, count_sha = read_grid(counts, shape)
    if any(count < 0 for count in shot_counts):
        raise ValueError("negative counts: investigate format before analysis")
    observed = [height for height, count in zip(heights, shot_counts) if count >= min_count]
    return {
        "source": ARCHIVE,
        "topography_sha256": top_sha,
        "counts_sha256": count_sha,
        "shape": list(shape),
        "topography_unit": "m above MOLA areoid",
        "counts_unit": "ground-return shots per bin",
        "min_count": min_count,
        "total_cells": len(heights),
        "observed_cells": sum(count > 0 for count in shot_counts),
        "interpolated_cells": sum(count == 0 for count in shot_counts),
        "retained_cells": len(observed),
        "retained_fraction": len(observed) / len(heights),
        "retained_topography_min_m": min(observed) if observed else None,
        "retained_topography_max_m": max(observed) if observed else None,
        "claim_state": "MEGDR ingestion only; cross-body similarity NOT YET PROVEN",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topography", type=Path, required=True)
    parser.add_argument("--counts", type=Path, required=True)
    parser.add_argument("--topography-label", type=Path, required=True)
    parser.add_argument("--counts-label", type=Path, required=True)
    parser.add_argument("--min-count", type=int, default=1)
    args = parser.parse_args()
    print(json.dumps(analyze(
        args.topography, args.counts, args.topography_label,
        args.counts_label, args.min_count,
    ), indent=2))


if __name__ == "__main__":
    main()
