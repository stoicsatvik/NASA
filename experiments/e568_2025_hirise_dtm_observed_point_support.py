"""E568: sample the 2025 USGS HiRISE DTM and FOM confidence at frozen MOLA points.

Only the DTM (675.6 MB compressed) and FOM_Confidence (65.3 MB compressed)
ZIP members are streamed to ephemeral files. The full 5.47 GB archive and
4.6 GB orthoimage are never downloaded. Only aggregate sample summaries are
retained; temporary raster files are deleted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import pyproj
import rasterio
import requests
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

DTM_MEMBER = (
    "MSR_TRN_HiRISE_soc_003_USGS_release_aug2024/mosaics/"
    "MSR_hirise_soc_003_DTM_MOLATopography_DeltaGeoid_1m_Eqc_latTs0_lon0_Blend40.tif"
)
CONFIDENCE_MEMBER = (
    "MSR_TRN_HiRISE_soc_003_USGS_release_aug2024/mosaics/"
    "MSR_hirise_soc_003_FOM_Confidence_1m_Eqc_latTs0_lon0.tif"
)
EXPECTED_DTM_COMPRESSED = 675_625_590
EXPECTED_DTM_UNCOMPRESSED = 711_891_990
EXPECTED_CONFIDENCE_COMPRESSED = 65_308_185
EXPECTED_CONFIDENCE_UNCOMPRESSED = 66_059_236
MAX_ARCHIVE_RANGE_BYTES = 850 * 1024 * 1024
MAX_MEMBER_UNCOMPRESSED_BYTES = 800 * 1024 * 1024
CACHE_BLOCK_BYTES = 1024 * 1024
STREAM_CHUNK_BYTES = 4 * 1024 * 1024


def stream_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo, destination: Path, expected_compressed: int, expected_uncompressed: int) -> dict:
    if int(info.compress_size) != expected_compressed:
        raise ValueError("compressed size changed for " + info.filename)
    if int(info.file_size) != expected_uncompressed:
        raise ValueError("uncompressed size changed for " + info.filename)
    if info.compress_type != zipfile.ZIP_DEFLATED:
        raise ValueError("ZIP compression method changed for " + info.filename)
    if info.file_size > MAX_MEMBER_UNCOMPRESSED_BYTES:
        raise ValueError("member exceeds frozen uncompressed byte cap")
    digest = hashlib.sha256()
    total = 0
    with archive.open(info, "r") as source, destination.open("wb") as target:
        while True:
            chunk = source.read(STREAM_CHUNK_BYTES)
            if not chunk:
                break
            total += len(chunk)
            if total > expected_uncompressed or total > MAX_MEMBER_UNCOMPRESSED_BYTES:
                raise ValueError("member decompressed beyond its pinned size")
            digest.update(chunk)
            target.write(chunk)
    if total != expected_uncompressed:
        raise ValueError("member decompressed byte count mismatch")
    return {
        "member": info.filename,
        "compressed_bytes": int(info.compress_size),
        "uncompressed_bytes": int(info.file_size),
        "zip_compression_method": int(info.compress_type),
        "uncompressed_sha256": digest.hexdigest(),
        "crc32": format(info.CRC, "08x"),
        "temporary_file_deleted_after_sampling": True,
    }


def sample_raster(dataset, lat: np.ndarray, lon: np.ndarray, observed: np.ndarray) -> dict:
    if dataset.driver != "GTiff" or dataset.count < 1:
        raise ValueError("selected member is not a readable GeoTIFF")
    if dataset.crs is None:
        raise ValueError("selected GeoTIFF has no readable CRS")
    if dataset.width <= 0 or dataset.height <= 0:
        raise ValueError("selected GeoTIFF has invalid dimensions")

    source_crs = pyproj.CRS.from_proj4(
        "+proj=longlat +a=" + str(MOLA_RADIUS_FALLBACK_M)
        + " +b=" + str(MOLA_RADIUS_FALLBACK_M)
        + " +no_defs +type=crs"
    )
    transformer = pyproj.Transformer.from_crs(
        source_crs, pyproj.CRS.from_wkt(dataset.crs.to_wkt()), always_xy=True
    )
    x, y = transformer.transform(lon, lat, errcheck=True)

    observed_indices = list(zip(*np.where(observed)))
    inside_mask = []
    valid_mask = []
    raw_values = []
    scaled_values = []
    for i, j in observed_indices:
        row, col = dataset.index(float(x[i, j]), float(y[i, j]))
        inside = 0 <= row < dataset.height and 0 <= col < dataset.width
        inside_mask.append(inside)
        valid = False
        if inside:
            sample = dataset.read(
                1,
                window=Window(int(col), int(row), 1, 1),
                masked=True,
            )
            value = sample[0, 0]
            if not np.ma.is_masked(value):
                raw = float(value)
                if np.isfinite(raw) and (
                    dataset.nodata is None or raw != float(dataset.nodata)
                ):
                    valid = True
                    raw_values.append(raw)
                    scale = float(dataset.scales[0]) if dataset.scales else 1.0
                    offset = float(dataset.offsets[0]) if dataset.offsets else 0.0
                    scaled_values.append(raw * scale + offset)
        valid_mask.append(valid)

    raw_array = np.asarray(raw_values, dtype="float64")
    scaled_array = np.asarray(scaled_values, dtype="float64")
    scale = float(dataset.scales[0]) if dataset.scales else 1.0
    offset = float(dataset.offsets[0]) if dataset.offsets else 0.0
    tags = dataset.tags()
    band_tags = dataset.tags(1)
    metadata = {
        "driver": dataset.driver,
        "width": int(dataset.width),
        "height": int(dataset.height),
        "band_count": int(dataset.count),
        "dtype": list(dataset.dtypes),
        "nodata": float(dataset.nodata) if dataset.nodata is not None else None,
        "scale": scale,
        "offset": offset,
        "units": list(dataset.units),
        "descriptions": list(dataset.descriptions),
        "block_shapes": [list(shape) for shape in dataset.block_shapes],
        "crs": dataset.crs.to_string(),
        "crs_wkt_sha256": hashlib.sha256(dataset.crs.to_wkt().encode("utf-8")).hexdigest(),
        "transform": [
            float(dataset.transform.a), float(dataset.transform.b), float(dataset.transform.c),
            float(dataset.transform.d), float(dataset.transform.e), float(dataset.transform.f),
        ],
        "bounds": {
            "left": float(dataset.bounds.left),
            "bottom": float(dataset.bounds.bottom),
            "right": float(dataset.bounds.right),
            "top": float(dataset.bounds.top),
        },
        "resolution": [float(dataset.res[0]), float(dataset.res[1])],
        "dataset_tag_keys": sorted(tags.keys()),
        "band_tag_keys": sorted(band_tags.keys()),
        "gdal_nodata_tag": band_tags.get("GDAL_NODATA"),
    }
    summary = {
        "observed_mola_point_centers": int(np.asarray(observed, dtype=bool).sum()),
        "inside_raster_bounds": int(sum(inside_mask)),
        "valid_unmasked_samples": int(sum(valid_mask)),
        "inside_fraction_of_observed": (
            float(sum(inside_mask) / len(observed_indices)) if observed_indices else None
        ),
        "valid_fraction_of_observed": (
            float(sum(valid_mask) / len(observed_indices)) if observed_indices else None
        ),
        "valid_fraction_of_inside": (
            float(sum(valid_mask) / sum(inside_mask)) if sum(inside_mask) else None
        ),
        "raw_sample_min": float(raw_array.min()) if raw_array.size else None,
        "raw_sample_median": float(np.median(raw_array)) if raw_array.size else None,
        "raw_sample_max": float(raw_array.max()) if raw_array.size else None,
        "scaled_sample_min": float(scaled_array.min()) if scaled_array.size else None,
        "scaled_sample_median": float(np.median(scaled_array)) if scaled_array.size else None,
        "scaled_sample_mean": float(scaled_array.mean()) if scaled_array.size else None,
        "scaled_sample_max": float(scaled_array.max()) if scaled_array.size else None,
        "unique_raw_sample_values": int(np.unique(raw_array).size) if raw_array.size else 0,
        "raw_sample_values_are_retained": False,
        "point_coordinates_are_retained": False,
    }
    return {
        "metadata": metadata,
        "summary": summary,
        "_inside_mask": inside_mask,
        "_valid_mask": valid_mask,
        "_raw_values": raw_values,
    }


def _top_counts(values: list[float]) -> list[dict]:
    counter = Counter(
        str(int(value)) if float(value).is_integer() else format(float(value), ".7g")
        for value in values
    )
    return [{"value": value, "count": count} for value, count in counter.most_common(12)]


def run() -> dict:
    receipt = {
        "experiment": "E568_2025_HIRISE_DTM_AND_FOM_OBSERVED_MOLA_POINT_SUPPORT",
        "date": "2026-11-12",
        "archive_url": ARCHIVE_URL,
        "dtm_member": DTM_MEMBER,
        "confidence_member": CONFIDENCE_MEMBER,
        "outcome": "NOT_RUN",
        "claim_state": {
            "2025_archive_range_access": "SUPPORTED",
            "2025_dtm_member_presence": "SUPPORTED AT ARCHIVE LEVEL",
            "2025_dtm_geotiff_readability": "NOT YET MEASURED",
            "2025_dtm_valid_support_at_observed_mola_points": "NOT YET MEASURED",
            "2025_confidence_support_at_observed_mola_points": "MEASURED IN E567",
            "dtm_confidence_mask_alignment": "NOT YET MEASURED",
            "2025_dtm_support_vs_2020_hirise": "NOT YET MEASURED",
            "independent_horizontal_registration": "NOT YET MEASURED",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
            "route_safety": "NOT CLAIMED",
        },
        "limitations": [
            "This is point-center support at 346 observed MOLA bins, not area coverage.",
            "The 2025 mosaic is aligned to the CTX reference; it is not an independent horizontal control network.",
            "MOLA coordinates are transformed to the raster CRS without a fitted datum shift.",
            "DN scale and offset are applied only as recorded by the GeoTIFF; vertical datum equivalence to other products is not tested.",
            "FOM_Confidence values remain raw categorical codes; no calibrated uncertainty interpretation is assumed.",
            "No raw per-point values, raster pixels, coordinates or temporary GeoTIFFs are retained.",
        ],
    }
    session = requests.Session()
    temp_dir = None
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
        count_total = FILE_RECORDS * COUNT_RECORD_BYTES
        count_raw, count_range = fetch_exact_range(
            session, COUNT_IMG, COUNT_NAME, start, end, count_total
        )
        counts = extract_window(
            count_raw,
            record_bytes=COUNT_RECORD_BYTES,
            line_samples=LINE_SAMPLES,
            window=window,
            kind="counts",
        )
        observed = counts > 0
        if int(observed.sum()) != 346:
            raise ValueError("frozen MOLA observed-point denominator changed from 346")
        lat, lon = mola_pixel_centers(window)

        temp_dir = tempfile.TemporaryDirectory(prefix="e568-hirise-")
        temp_path = Path(temp_dir.name)
        dtm_path = temp_path / "dtm.tif"
        confidence_path = temp_path / "confidence.tif"
        remote = HTTPRangeFile(
            session,
            ARCHIVE_URL,
            max_total_bytes=MAX_ARCHIVE_RANGE_BYTES,
            cache_block_bytes=CACHE_BLOCK_BYTES,
        )
        with zipfile.ZipFile(remote, mode="r") as archive:
            infos = {info.filename: info for info in archive.infolist()}
            if DTM_MEMBER not in infos or CONFIDENCE_MEMBER not in infos:
                raise ValueError("pinned DTM/confidence members missing from archive")
            dtm_receipt = stream_member(
                archive, infos[DTM_MEMBER], dtm_path,
                EXPECTED_DTM_COMPRESSED, EXPECTED_DTM_UNCOMPRESSED,
            )
            confidence_receipt = stream_member(
                archive, infos[CONFIDENCE_MEMBER], confidence_path,
                EXPECTED_CONFIDENCE_COMPRESSED, EXPECTED_CONFIDENCE_UNCOMPRESSED,
            )
        transport = {
            "range_requests": len(remote.ranges),
            "range_bytes_transferred": remote.transferred,
            "range_transfer_cap_bytes": MAX_ARCHIVE_RANGE_BYTES,
            "cache_block_bytes": CACHE_BLOCK_BYTES,
            "full_archive_downloaded": False,
            "orthoimage_member_read": False,
            "temporary_files_deleted_after_sampling": True,
        }
        remote.close()

        with rasterio.open(dtm_path) as dtm, rasterio.open(confidence_path) as confidence:
            dtm_result = sample_raster(dtm, lat, lon, observed)
            confidence_result = sample_raster(confidence, lat, lon, observed)

        dtm_valid = np.asarray(dtm_result["_valid_mask"], dtype=bool)
        fom_valid = np.asarray(confidence_result["_valid_mask"], dtype=bool)
        both_valid = dtm_valid & fom_valid
        confidence_only = fom_valid & ~dtm_valid
        dtm_only = dtm_valid & ~fom_valid
        neither = ~dtm_valid & ~fom_valid
        fom_values = confidence_result["_raw_values"]
        cross_tab = {
            "observed_mola_point_centers": int(observed.sum()),
            "dtm_valid": int(dtm_valid.sum()),
            "confidence_valid": int(fom_valid.sum()),
            "both_valid": int(both_valid.sum()),
            "confidence_valid_but_dtm_invalid": int(confidence_only.sum()),
            "dtm_valid_but_confidence_invalid": int(dtm_only.sum()),
            "both_invalid": int(neither.sum()),
            "fom_raw_code_counts": _top_counts(fom_values),
            "fom_codes_are_interpreted": False,
        }
        receipt["mola_source"] = {
            "counts_label": count_label_receipt,
            "counts_range": count_range,
            "window": window,
            "observed_shot_bins": int(observed.sum()),
            "total_bins": int(observed.size),
            "raw_counts_retained": False,
        }
        receipt["archive_transport"] = transport
        receipt["dtm_member_receipt"] = dtm_receipt
        receipt["confidence_member_receipt"] = confidence_receipt
        receipt["dtm_raster"] = {
            "metadata": dtm_result["metadata"],
            "sample_summary": dtm_result["summary"],
        }
        receipt["confidence_raster"] = {
            "metadata": confidence_result["metadata"],
            "sample_summary": confidence_result["summary"],
        }
        receipt["cross_tab"] = cross_tab
        receipt["outcome"] = "DTM_AND_CONFIDENCE_POINT_SUPPORT_MEASURED"
        receipt["claim_state"].update(
            {
                "2025_dtm_geotiff_readability": "SUPPORTED FOR THIS PINNED MEMBER",
                "2025_dtm_valid_support_at_observed_mola_points": "MEASURED FOR THIS BOUNDED WINDOW",
                "dtm_confidence_mask_alignment": "MEASURED FOR THIS BOUNDED WINDOW",
                "2025_dtm_support_vs_2020_hirise": "MEASURED AGAINST E563 164/346 BASELINE",
            }
        )
    except Exception as exc:
        receipt["outcome"] = "ERROR"
        receipt["error"] = {
            "kind": type(exc).__name__,
            "message": str(exc)[:700],
        }
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()
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
                "dtm_valid_points": receipt.get("dtm_raster", {}).get("sample_summary", {}).get("valid_unmasked_samples"),
                "confidence_valid_points": receipt.get("confidence_raster", {}).get("sample_summary", {}).get("valid_unmasked_samples"),
                "both_valid_points": receipt.get("cross_tab", {}).get("both_valid"),
                "range_bytes": receipt.get("archive_transport", {}).get("range_bytes_transferred"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
