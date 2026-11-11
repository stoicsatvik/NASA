"""E554: bounded neighborhood audit around three all-nodata HiRISE windows.

Only mask counts, spatial block summaries, source hashes and transfer metadata
are persisted. Raw pixels are held transiently in memory and never uploaded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import requests
import tifffile

from experiments.e548_hirise_pixel_window import (
    DOI,
    TIFF_URL,
    RangeReader,
    ProbeError,
    _geo_summary,
    _read_small_label,
    _resolve_nodata,
    parse_pds3_label,
)

ROOT = Path(__file__).resolve().parents[1]
PATCHES_PATH = ROOT / "data" / "e550_patch_summaries.json"
EXPECTED_PATCHES = {"x15_y15", "x50_y85", "x85_y85"}
WINDOW_SIZE = 128
BLOCK_SIZE = 16
MAX_TRANSFER_BYTES = 1_000_000
USER_AGENT = "Unified-Parallel-Foundry-E554/1.0"


class E554Error(RuntimeError):
    def __init__(self, outcome: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.outcome = outcome
        self.details = details or {}


def summarize_mask(values: np.ndarray, nodata: float | None, block_size: int = BLOCK_SIZE) -> dict:
    """Return bounded support summaries without retaining raw sample values."""
    array = np.asarray(values)
    if array.shape != (WINDOW_SIZE, WINDOW_SIZE):
        raise ValueError("expected an exact 128x128 neighborhood")
    if block_size < 1 or WINDOW_SIZE % block_size:
        raise ValueError("block size must divide the 128-pixel window")
    if array.dtype.kind not in "fiu":
        raise ValueError("sample array must be numeric")

    finite = np.isfinite(array)
    missing = np.zeros(array.shape, dtype=bool) if nodata is None else array == nodata
    valid = finite & ~missing
    center = valid[32:96, 32:96]
    blocks = []
    for row in range(0, WINDOW_SIZE, block_size):
        block_row = []
        for col in range(0, WINDOW_SIZE, block_size):
            block_row.append(int(valid[row:row + block_size, col:col + block_size].sum()))
        blocks.append(block_row)

    usable = int(valid.sum())
    center_usable = int(center.sum())
    if usable == 0:
        classification = "ALL_NODATA_WITHIN_128M"
    elif center_usable == 0:
        classification = "NODATA_CORE_WITH_NEARBY_SUPPORT"
    else:
        classification = "VALID_SUPPORT_REACHES_CENTER"

    return {
        "window_pixels": int(array.size),
        "finite_pixels": int(finite.sum()),
        "nodata_pixels": int((finite & missing).sum()),
        "nonfinite_pixels": int((~finite).sum()),
        "usable_pixels": usable,
        "usable_fraction": float(usable / array.size),
        "center_64x64_usable_pixels": center_usable,
        "center_64x64_usable_fraction": float(center_usable / center.size),
        "block_size_pixels": block_size,
        "block_grid_rows": len(blocks),
        "block_grid_columns": len(blocks[0]),
        "block_valid_pixel_counts": blocks,
        "classification": classification,
        "raw_pixels_retained": False,
    }


def _load_missing_patches(path: Path = PATCHES_PATH) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    patches = payload.get("patches")
    if not isinstance(patches, list):
        raise E554Error("INVALID_E550_RECEIPT", "E550 patch list is absent")
    missing = [p for p in patches if p.get("common_valid_cells") == 0]
    ids = {p.get("patch_id") for p in missing}
    if ids != EXPECTED_PATCHES:
        raise E554Error(
            "E550_MISSINGNESS_CONTRACT_MISMATCH",
            "E550 must identify exactly the three preregistered unsupported positions",
            {"observed_ids": sorted(str(x) for x in ids)},
        )
    return sorted(missing, key=lambda p: p["patch_id"])


def _read_mask_window(reader: RangeReader, page, window: dict) -> tuple[np.ndarray, str]:
    col, row = int(window["col_off"]), int(window["row_off"])
    width, height = int(window["width"]), int(window["height"])
    if min(col, row) < 0 or min(width, height) <= 0:
        raise E554Error("INVALID_WINDOW", "Invalid raster window")
    if col + width > int(page.imagewidth) or row + height > int(page.imagelength):
        raise E554Error("WINDOW_OUTSIDE_RASTER", "Neighborhood exceeds source raster")
    if int(page.compression) != 1 or page.is_tiled:
        raise E554Error("UNSUPPORTED_TIFF_LAYOUT", "Requires uncompressed strips")
    if np.dtype(page.dtype).kind != "f" or np.dtype(page.dtype).itemsize != 4:
        raise E554Error("UNSUPPORTED_TIFF_SAMPLE", "Requires float32 samples")
    if int(page.samplesperpixel) != 1 or int(page.rowsperstrip) != 1:
        raise E554Error("UNSUPPORTED_STRIP_LAYOUT", "Requires one float32 sample per row strip")

    offsets = tuple(map(int, page.dataoffsets))
    counts = tuple(map(int, page.databytecounts))
    if len(offsets) != int(page.imagelength) or len(counts) != len(offsets):
        raise E554Error("INVALID_STRIP_TABLE", "Unexpected TIFF strip table")
    if any(n != int(page.imagewidth) * 4 for n in counts):
        raise E554Error("INVALID_STRIP_BYTES", "Strip size differs from width × float32")

    rows = []
    digest = hashlib.sha256()
    for raster_row in range(row, row + height):
        start = offsets[raster_row] + col * 4
        amount = width * 4
        if start < offsets[raster_row] or start + amount > offsets[raster_row] + counts[raster_row]:
            raise E554Error("WINDOW_OUTSIDE_STRIP", "Requested bytes exceed row strip")
        reader.seek(start)
        raw = reader.read(amount)
        digest.update(raw)
        rows.append(np.frombuffer(raw, dtype=page.dtype, count=width).copy())
    return np.vstack(rows), digest.hexdigest()


def run() -> dict:
    session = requests.Session()
    label_text, label_receipt = _read_small_label(session)
    label = parse_pds3_label(label_text)

    head = session.head(
        TIFF_URL,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
        timeout=(15, 45),
        allow_redirects=False,
    )
    try:
        if int(head.status_code) != 200:
            raise E554Error(f"TIFF_HEAD_HTTP_{head.status_code}", "Pinned HiRISE TIFF HEAD failed")
        raw_size = head.headers.get("Content-Length", "")
        if not raw_size.isdigit() or int(raw_size) <= 0:
            raise E554Error("TIFF_SIZE_UNKNOWN", "Missing positive TIFF Content-Length")
        size = int(raw_size)
        if head.headers.get("Accept-Ranges", "").lower() != "bytes":
            raise E554Error("RANGE_NOT_ADVERTISED", "Pinned TIFF does not advertise byte ranges")
    finally:
        head.close()

    reader = RangeReader(session, TIFF_URL, size, max_bytes=MAX_TRANSFER_BYTES)
    with tifffile.TiffFile(reader) as tif:
        if not tif.pages:
            raise E554Error("TIFF_NO_PAGES", "HiRISE TIFF has no pages")
        page = tif.pages[0]
        if (int(page.imagewidth), int(page.imagelength)) != (21400, 21488):
            raise E554Error("TIFF_DIMENSION_MISMATCH", "Raster dimensions differ from E548 contract")
        nodata, nodata_source = _resolve_nodata(page, label)
        geo = _geo_summary(page)
        bounds = geo["raster_bounds_map_units"]
        sx, sy = map(float, geo["model_pixel_scale"])
        if sx <= 0 or sy <= 0:
            raise E554Error("INVALID_GEOREFERENCE", "Pixel scales must be positive")

        results = []
        for patch in _load_missing_patches():
            x, y = float(patch["center_x"]), float(patch["center_y"])
            col_center = (x - float(bounds["xmin"])) / sx
            row_center = (float(bounds["ymax"]) - y) / sy
            col_off = int(round(col_center)) - WINDOW_SIZE // 2
            row_off = int(round(row_center)) - WINDOW_SIZE // 2
            window = {
                "col_off": col_off,
                "row_off": row_off,
                "width": WINDOW_SIZE,
                "height": WINDOW_SIZE,
            }
            values, sample_hash = _read_mask_window(reader, page, window)
            results.append({
                "patch_id": patch["patch_id"],
                "map_center_m": {"x": x, "y": y},
                "window": window,
                "window_extent_m_nominal": [WINDOW_SIZE, WINDOW_SIZE],
                "window_sample_sha256": sample_hash,
                "support": summarize_mask(values, nodata),
            })

        geospatial = {
            "model_pixel_scale": list(geo["model_pixel_scale"]),
            "model_tiepoint": list(geo["model_tiepoint"]),
            "raster_bounds_map_units": bounds,
            "projected_crs_geokey": geo["projected_crs_code"],
            "projection_transform_geokey": geo["projection_transform_code"],
        }

    return {
        "experiment": "E554 bounded HiRISE nodata-neighborhood audit",
        "outcome": "THREE_NEIGHBORHOODS_MEASURED",
        "source": {
            "publisher": "USGS Astrogeology Science Center",
            "doi": DOI,
            "product": "Mars 2020 TRN HiRISE DTM mosaic (2020)",
            "tiff_url": TIFF_URL,
            "pds3_label_url": "pinned by E548 helper",
            "label_sha256": label_receipt["sha256"],
            "nodata_value": nodata,
            "nodata_source": nodata_source,
        },
        "design": {
            "positions": sorted(EXPECTED_PATCHES),
            "window_pixels": [WINDOW_SIZE, WINDOW_SIZE],
            "nominal_ground_extent_m": [WINDOW_SIZE, WINDOW_SIZE],
            "block_size_pixels": BLOCK_SIZE,
            "central_diagnostic_window_pixels": [64, 64],
            "no_imputation": True,
            "no_registration_fit": True,
            "no_raw_pixel_persistence": True,
            "transfer_cap_bytes": MAX_TRANSFER_BYTES,
        },
        "georeferencing": geospatial,
        "neighborhoods": results,
        "transport": {
            "range_requests": len(reader.ranges),
            "bytes_transferred": reader.transferred,
            "transfer_cap_bytes": MAX_TRANSFER_BYTES,
        },
        "interpretation": {
            "classification_rule": (
                "A valid pixel in the 128x128 neighborhood indicates nearby product support; "
                "an all-nodata neighborhood establishes only a local support gap, not its physical cause."
            ),
            "cause_of_original_nodata": "NOT DETERMINED",
            "original_E550_support": "THREE_PATCHES_ALL_NODATA",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
            "route_safety": "NOT CLAIMED",
        },
        "limitations": [
            "The neighborhood is centered on the preregistered E550 map coordinate, not a new analogue candidate.",
            "The 128x128 window is a support diagnostic, not a new elevation comparison.",
            "Nodata may reflect footprint exclusion, masking, invalid terrain or another product rule.",
            "No raw pixels are persisted; only mask counts, block counts and hashes are retained.",
            "This experiment cannot distinguish an unsurveyed area from a masked/invalid terrain area without independent source provenance.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run()
    except (E554Error, ProbeError) as exc:
        result = {
            "experiment": "E554 bounded HiRISE nodata-neighborhood audit",
            "outcome": getattr(exc, "outcome", "SOURCE_OR_GEOMETRY_ERROR"),
            "message": str(exc),
            "details": getattr(exc, "details", {}),
            "interpretation": {
                "cause_of_original_nodata": "NOT DETERMINED",
                "cross_body_similarity": "NOT YET PROVEN",
                "known_site_recovery": "NOT YET MEASURED",
            },
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "experiment": result["experiment"],
        "outcome": result["outcome"],
        "neighborhoods": [
            {
                "patch_id": item["patch_id"],
                "usable_pixels": item["support"]["usable_pixels"],
                "center_64x64_usable_pixels": item["support"]["center_64x64_usable_pixels"],
                "classification": item["support"]["classification"],
            }
            for item in result.get("neighborhoods", [])
        ],
        "range_requests": result.get("transport", {}).get("range_requests"),
        "bytes_transferred": result.get("transport", {}).get("bytes_transferred"),
    }, sort_keys=True))
    return 0 if result["outcome"] == "THREE_NEIGHBORHOODS_MEASURED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
