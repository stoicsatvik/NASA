"""E567: sample the 2025 USGS HiRISE FOM_Confidence raster at frozen MOLA points.

Only the 65.3 MB compressed confidence member is decompressed. The 675.6 MB
DTM and 4.6 GB orthoimage members are never read. Only metadata and summaries
for 346 observed MOLA point centers are retained.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import pyproj
import rasterio
import requests
from rasterio.io import MemoryFile
from rasterio.windows import Window

from experiments.e566_2025_hirise_confidence_archive_audit import (
    ARCHIVE_URL,
    HTTPRangeFile,
)
from experiments.e545_mola_observed_support import (
    COUNT_IMG,
    COUNT_LABEL,
    COUNT_NAME,
    COUNT_RECORD_BYTES,
    FILE_RECORDS,
    LINE_SAMPLES,
    byte_range,
    extract_window,
    fetch_exact_range,
    fetch_label,
    make_window,
    pixel_index,
    validate_label,
)
from experiments.e563_three_way_common_support import (
    MOLA_RADIUS_FALLBACK_M,
    MOLA_WINDOW_SIZE,
    mola_pixel_centers,
)

CONFIDENCE_MEMBER = (
    "MSR_TRN_HiRISE_soc_003_USGS_release_aug2024/mosaics/"
    "MSR_hirise_soc_003_FOM_Confidence_1m_Eqc_latTs0_lon0.tif"
)
EXPECTED_COMPRESSED_BYTES = 65_308_185
EXPECTED_UNCOMPRESSED_BYTES = 66_059_236
MAX_CONFIDENCE_BYTES = 80 * 1024 * 1024
MAX_ARCHIVE_RANGE_BYTES = 100 * 1024 * 1024
CACHE_BLOCK_BYTES = 1024 * 1024
USER_AGENT = "Unified-Parallel-Foundry-E567/1.0"


def summarize_values(values: list[float], inside_count: int, observed_count: int) -> dict:
    array = np.asarray(values, dtype="float64")
    top = Counter(
        str(int(value)) if float(value).is_integer() else format(float(value), ".7g")
        for value in values
    ).most_common(12)
    return {
        "observed_mola_point_centers": int(observed_count),
        "inside_confidence_raster_bounds": int(inside_count),
        "valid_unmasked_confidence_samples": int(array.size),
        "inside_fraction_of_observed": (
            float(inside_count / observed_count) if observed_count else None
        ),
        "valid_fraction_of_observed": (
            float(array.size / observed_count) if observed_count else None
        ),
        "valid_fraction_of_inside": (
            float(array.size / inside_count) if inside_count else None
        ),
        "sample_min": float(array.min()) if array.size else None,
        "sample_median": float(np.median(array)) if array.size else None,
        "sample_mean": float(array.mean()) if array.size else None,
        "sample_max": float(array.max()) if array.size else None,
        "unique_sample_values": int(np.unique(array).size) if array.size else 0,
        "most_common_sample_values": [
            {"value": value, "count": count} for value, count in top
        ],
        "values_are_interpreted_as_calibrated_uncertainty": False,
    }


def sample_confidence(ds, lat: np.ndarray, lon: np.ndarray, observed: np.ndarray) -> dict:
    if ds.driver != "GTiff" or ds.count < 1:
        raise ValueError("confidence member is not a readable single-or-multiband GeoTIFF")
    if ds.crs is None:
        raise ValueError("confidence GeoTIFF has no readable CRS")
    if ds.width <= 0 or ds.height <= 0:
        raise ValueError("confidence GeoTIFF has invalid dimensions")

    source_crs = pyproj.CRS.from_proj4(
        "+proj=longlat +a=" + str(MOLA_RADIUS_FALLBACK_M)
        + " +b=" + str(MOLA_RADIUS_FALLBACK_M)
        + " +no_defs +type=crs"
    )
    transformer = pyproj.Transformer.from_crs(
        source_crs, pyproj.CRS.from_wkt(ds.crs.to_wkt()), always_xy=True
    )
    x, y = transformer.transform(lon, lat, errcheck=True)

    inside_count = 0
    values: list[float] = []
    observed_count = int(np.asarray(observed, dtype=bool).sum())
    for i, j in zip(*np.where(observed)):
        row, col = ds.index(float(x[i, j]), float(y[i, j]))
        if not (0 <= row < ds.height and 0 <= col < ds.width):
            continue
        inside_count += 1
        sample = ds.read(
            1,
            window=Window(int(col), int(row), 1, 1),
            masked=True,
        )
        value = sample[0, 0]
        if np.ma.is_masked(value):
            continue
        numeric = float(value)
        if not np.isfinite(numeric):
            continue
        if ds.nodata is not None and numeric == float(ds.nodata):
            continue
        values.append(numeric)

    transform = ds.transform
    crs_wkt = ds.crs.to_wkt()
    return {
        "driver": ds.driver,
        "width": int(ds.width),
        "height": int(ds.height),
        "band_count": int(ds.count),
        "dtype": list(ds.dtypes),
        "nodata": float(ds.nodata) if ds.nodata is not None else None,
        "units": list(ds.units),
        "descriptions": list(ds.descriptions),
        "block_shapes": [list(shape) for shape in ds.block_shapes],
        "crs": ds.crs.to_string(),
        "crs_wkt_sha256": hashlib.sha256(crs_wkt.encode("utf-8")).hexdigest(),
        "transform": [
            float(transform.a), float(transform.b), float(transform.c),
            float(transform.d), float(transform.e), float(transform.f),
        ],
        "bounds": {
            "left": float(ds.bounds.left),
            "bottom": float(ds.bounds.bottom),
            "right": float(ds.bounds.right),
            "top": float(ds.bounds.top),
        },
        "resolution": [float(ds.res[0]), float(ds.res[1])],
        "dataset_tag_keys": sorted(ds.tags().keys()),
        "band_tag_keys": sorted(ds.tags(1).keys()),
        "sample_summary": summarize_values(values, inside_count, observed_count),
        "sample_method": (
            "346-or-fewer fixed observed-MOLA point centers; point-center lookup only; "
            "MOLA IAU2000 3396000 m sphere coordinates transformed to the raster CRS; "
            "no fitted datum shift"
        ),
        "raw_pixel_values_retained": False,
        "point_coordinates_retained": False,
    }


def run() -> dict:
    receipt = {
        "experiment": "E567_2025_HIRISE_FOM_CONFIDENCE_POINT_SUPPORT",
        "date": "2026-11-12",
        "archive_url": ARCHIVE_URL,
        "confidence_member": CONFIDENCE_MEMBER,
        "expected_compressed_bytes": EXPECTED_COMPRESSED_BYTES,
        "expected_uncompressed_bytes": EXPECTED_UNCOMPRESSED_BYTES,
        "outcome": "NOT_RUN",
        "claim_state": {
            "2025_archive_range_access": "SUPPORTED",
            "confidence_member_presence": "SUPPORTED AT ARCHIVE LEVEL",
            "confidence_geotiff_readable": "NOT YET MEASURED",
            "confidence_georeferencing": "NOT YET MEASURED",
            "confidence_value_semantics": "NOT YET PROVEN",
            "confidence_valid_support_at_observed_mola_points": "NOT YET MEASURED",
            "2025_dtm_valid_support_at_observed_mola_points": "NOT YET MEASURED",
            "replacement_of_2020_hirise_nodata": "NOT YET MEASURED",
            "independent_horizontal_registration": "NOT YET MEASURED",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
            "route_safety": "NOT CLAIMED",
        },
        "limitations": [
            "FOM_Confidence values are retained as raw codes; no calibrated uncertainty or quality interpretation is assumed.",
            "This experiment samples confidence only; it does not read the 2025 DTM values.",
            "The 2025 mosaic is aligned to the CTX reference and is not an independent horizontal control network.",
            "Point-center support is not area coverage and does not establish DTM validity at every point.",
            "No raw raster pixels, full archive, credentials or point coordinates are retained.",
        ],
    }
    session = requests.Session()
    try:
        count_label_text, count_label_receipt = fetch_label(
            session, COUNT_LABEL, COUNT_NAME
        )
        validate_label(count_label_text, "counts")
        center_row, center_col = pixel_index(18.3995, 77.27025)
        window = make_window(center_row, center_col, MOLA_WINDOW_SIZE)
        start, end = byte_range(
            window["row_start"], window["row_end"], COUNT_RECORD_BYTES
        )
        total = FILE_RECORDS * COUNT_RECORD_BYTES
        count_raw, count_range = fetch_exact_range(
            session, COUNT_IMG, COUNT_NAME, start, end, total
        )
        counts = extract_window(
            count_raw,
            record_bytes=COUNT_RECORD_BYTES,
            line_samples=LINE_SAMPLES,
            window=window,
            kind="counts",
        )
        observed = counts > 0
        if not observed.any():
            raise ValueError("frozen MOLA window contains no observed-shot bins")
        lat, lon = mola_pixel_centers(window)

        remote = HTTPRangeFile(
            session,
            ARCHIVE_URL,
            max_total_bytes=MAX_ARCHIVE_RANGE_BYTES,
            cache_block_bytes=CACHE_BLOCK_BYTES,
        )
        with zipfile.ZipFile(remote, mode="r") as archive:
            matches = [info for info in archive.infolist() if info.filename == CONFIDENCE_MEMBER]
            if len(matches) != 1:
                raise ValueError("pinned FOM_Confidence member was not unique in the archive")
            info = matches[0]
            if int(info.compress_size) != EXPECTED_COMPRESSED_BYTES:
                raise ValueError("FOM_Confidence compressed size differs from E566")
            if int(info.file_size) != EXPECTED_UNCOMPRESSED_BYTES:
                raise ValueError("FOM_Confidence uncompressed size differs from E566")
            if info.file_size > MAX_CONFIDENCE_BYTES:
                raise ValueError("confidence member exceeds the 80 MiB uncompressed cap")
            if info.compress_type != zipfile.ZIP_DEFLATED:
                raise ValueError("confidence member compression method changed from deflate")
            with archive.open(info, "r") as member:
                confidence_bytes = member.read(MAX_CONFIDENCE_BYTES + 1)
            if len(confidence_bytes) != info.file_size:
                raise ValueError("confidence member decompressed byte count mismatch")
            if len(confidence_bytes) > MAX_CONFIDENCE_BYTES:
                raise ValueError("confidence member exceeded the 80 MiB uncompressed cap")

        receipt["archive_transport"] = {
            "range_requests": len(remote.ranges),
            "range_bytes_transferred": remote.transferred,
            "range_transfer_cap_bytes": MAX_ARCHIVE_RANGE_BYTES,
            "cache_block_bytes": CACHE_BLOCK_BYTES,
            "zip_member_compressed_bytes": int(info.compress_size),
            "zip_member_uncompressed_bytes": int(info.file_size),
            "zip_compression_method": int(info.compress_type),
            "uncompressed_member_sha256": hashlib.sha256(confidence_bytes).hexdigest(),
            "full_archive_downloaded": False,
            "raw_member_retained": False,
        }
        receipt["mola_source"] = {
            "counts_label": count_label_receipt,
            "counts_range": count_range,
            "window": window,
            "observed_shot_bins": int(observed.sum()),
            "total_bins": int(observed.size),
            "observed_shot_fraction": float(observed.mean()),
            "raw_counts_retained": False,
        }

        with MemoryFile(confidence_bytes) as memory_file:
            with memory_file.open() as ds:
                raster_summary = sample_confidence(ds, lat, lon, observed)
        receipt["confidence_raster"] = raster_summary
        receipt["outcome"] = "CONFIDENCE_POINT_SUPPORT_MEASURED"
        receipt["claim_state"].update(
            {
                "confidence_geotiff_readable": "SUPPORTED FOR THIS PINNED MEMBER",
                "confidence_georeferencing": "SUPPORTED FOR THIS PINNED MEMBER",
                "confidence_valid_support_at_observed_mola_points": (
                    "MEASURED FOR THIS BOUNDED WINDOW"
                ),
            }
        )
    except Exception as exc:
        receipt["outcome"] = "ERROR"
        receipt["error"] = {
            "kind": type(exc).__name__,
            "message": str(exc)[:600],
        }
    finally:
        session.close()
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    receipt = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "experiment": receipt["experiment"],
                "outcome": receipt["outcome"],
                "mola_observed_bins": receipt.get("mola_source", {}).get("observed_shot_bins"),
                "confidence_valid_points": receipt.get("confidence_raster", {}).get("sample_summary", {}).get("valid_unmasked_confidence_samples"),
                "confidence_inside_points": receipt.get("confidence_raster", {}).get("sample_summary", {}).get("inside_confidence_raster_bounds"),
                "range_bytes": receipt.get("archive_transport", {}).get("range_bytes_transferred"),
            },
            sort_keys=True,
        )
    )
    # Preserve access, parser and data-quality failures as explicit experiment outcomes.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
