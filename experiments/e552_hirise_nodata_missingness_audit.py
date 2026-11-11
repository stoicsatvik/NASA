"""E552: classify unsupported E550 HiRISE windows using independent nodata provenance."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "e550_patch_support_provenance.json"


def all_nodata_sha256(value: float, shape: tuple[int, int]) -> str:
    """Hash a little-endian float32 window filled with the pinned nodata value."""
    if len(shape) != 2 or any(int(x) <= 0 for x in shape):
        raise ValueError("window shape must contain two positive dimensions")
    encoded = struct.pack("<f", float(value))
    return hashlib.sha256(encoded * (int(shape[0]) * int(shape[1]))).hexdigest()


def analyze(path: Path = DATA) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    source = payload["source"]
    if source["hirise_doi"] != "10.5066/P9REJ9JN":
        raise ValueError("E549 and E550 must reference the same pinned HiRISE product")
    shape = tuple(source["sample_shape"])
    expected = all_nodata_sha256(source["nodata_value"], shape)
    if expected != source["all_nodata_window_sha256"]:
        raise ValueError("pinned all-nodata digest does not reproduce")

    patches = payload["patches"]
    if len(patches) != 9 or len({p["patch_id"] for p in patches}) != 9:
        raise ValueError("expected nine unique E550 grid positions")

    classified = []
    for patch in patches:
        window = patch["hirise_window"]
        if (window["width"], window["height"]) != (shape[1], shape[0]):
            raise ValueError("E550 patch window shape changed")
        if patch["ctx_valid_cells"] != 25:
            raise ValueError("E550 CTX support contract changed")
        digest = patch["hirise_sample_sha256"]
        common = patch["common_valid_cells"]
        if common == 0 and digest == expected:
            classification = "ALL_NODATA_WINDOW"
        elif common == 25 and digest != expected:
            classification = "NON_NODATA_CONTENT_WITH_FULL_COMMON_SUPPORT"
        else:
            classification = "MIXED_OR_UNRESOLVED"
        classified.append({
            "patch_id": patch["patch_id"],
            "fraction_x": patch["fraction_x"],
            "fraction_y": patch["fraction_y"],
            "common_valid_cells": common,
            "sample_sha256": digest,
            "classification": classification,
        })

    unsupported = [p for p in classified if p["classification"] == "ALL_NODATA_WINDOW"]
    measured = [p for p in classified if p["classification"] == "NON_NODATA_CONTENT_WITH_FULL_COMMON_SUPPORT"]
    unresolved = [p for p in classified if p["classification"] == "MIXED_OR_UNRESOLVED"]
    if len(unsupported) != 3 or len(measured) != 6 or unresolved:
        raise ValueError("E550 support pattern differs from the frozen three/all-nodata, six/measured contract")

    return {
        "experiment": "E552 E550 HiRISE nodata missingness provenance audit",
        "source": source,
        "all_nodata_digest_reproduced": True,
        "all_nodata_window_count": len(unsupported),
        "full_common_support_window_count": len(measured),
        "unresolved_window_count": len(unresolved),
        "unsupported_patch_ids": [p["patch_id"] for p in unsupported],
        "classified_patches": classified,
        "spatial_missingness": {
            "grid_positions": 9,
            "unsupported_positions": len(unsupported),
            "row_counts_by_y_fraction": {
                str(y): sum(p["fraction_y"] == y for p in unsupported)
                for y in (0.15, 0.50, 0.85)
            },
            "interpretation": "descriptive support pattern only; no missingness mechanism is inferred",
        },
        "claim_state": {
            "three_unsupported_windows_are_byte_identical_all_nodata": "SUPPORTED_BY_CROSS_RECEIPT_HASH",
            "cause_of_nodata": "NOT DETERMINED",
            "six_patch_residuals": "MEASURED",
            "nine_position_common_support": "PARTIAL; SIX OF NINE POSITIONS",
            "E551_exchangeability": "CONDITIONAL ON SIX MEASURED PATCHES; NOT GENERALIZED TO NINE",
            "spatial_gradient": "NOT SUPPORTED BY E551 SIX-PATCH EXACT NULL",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "route_safety": "NOT CLAIMED",
        },
        "limitations": [
            "The audit uses compact E549/E550 receipts and a SHA-256 equality check, not retained raw raster pixels.",
            "Identical all-nodata windows establish the stored byte pattern, not why the source DTM has no valid samples there.",
            "The six-patch permutation result remains conditional on the six measured locations and cannot be generalized to the full nine-position grid.",
            "No new raster acquisition, pixel decoding, registration fit, correction surface or cross-body inference is performed.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    result = analyze()
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
