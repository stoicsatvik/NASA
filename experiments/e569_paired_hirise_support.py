"""E569: paired 2020/2025 HiRISE point-support comparison at frozen MOLA bins.

The experiment reconstructs the 2020 point mask from bounded HTTP ranges,
reacquires only the 2025 DTM member, and compares both products at the same
346 observed MOLA point centers. It retains masks only in memory and emits
aggregate cross-tabs plus a fixed +/-6 m map-translation sensitivity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pyproj
import rasterio
import requests
import tifffile

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
from experiments.e548_hirise_pixel_window import (
    LABEL_URL,
    TIFF_URL,
    RangeReader,
    _geo_summary,
    _read_small_label,
    _resolve_nodata,
    parse_pds3_label,
)
from experiments.e563_three_way_common_support import (
    MOLA_RADIUS_FALLBACK_M,
    MOLA_WINDOW_SIZE,
    build_hirise_crs,
    mola_pixel_centers,
    point_indices,
)
from experiments.e566_2025_hirise_confidence_archive_audit import (
    ARCHIVE_URL,
    HTTPRangeFile,
)
from experiments.e568_2025_hirise_dtm_observed_point_support import (
    CACHE_BLOCK_BYTES,
    DTM_MEMBER,
    EXPECTED_DTM_COMPRESSED,
    EXPECTED_DTM_UNCOMPRESSED,
    MAX_ARCHIVE_RANGE_BYTES,
    sample_raster,
    stream_member,
)

TRANSLATION_OFFSETS_M = (
    (-6.0, -6.0), (-6.0, 0.0), (-6.0, 6.0),
    (0.0, -6.0), (0.0, 0.0), (0.0, 6.0),
    (6.0, -6.0), (6.0, 0.0), (6.0, 6.0),
)
MAX_2020_RANGE_BYTES = 4 * 1024 * 1024
USER_AGENT = "Unified-Parallel-Foundry-E569/1.0"


def valid_sample(value: float, nodata: float | None) -> bool:
    numeric = float(value)
    return math.isfinite(numeric) and (nodata is None or numeric != float(nodata))


def build_row_range_plan(index_sets: list[tuple[np.ndarray, np.ndarray, np.ndarray]]) -> dict[int, tuple[int, int]]:
    """Coalesce all in-bounds point columns by TIFF strip row."""
    ranges: dict[int, list[int]] = {}
    for rows, cols, inside in index_sets:
        for row, col, keep in zip(rows, cols, inside):
            if not bool(keep):
                continue
            r, c = int(row), int(col)
            if r not in ranges:
                ranges[r] = [c, c]
            else:
                ranges[r][0] = min(ranges[r][0], c)
                ranges[r][1] = max(ranges[r][1], c)
    return {row: (bounds[0], bounds[1]) for row, bounds in sorted(ranges.items())}


def build_paired_cross_tab(
    old_inside: list[bool] | np.ndarray,
    old_valid: list[bool] | np.ndarray,
    new_inside: list[bool] | np.ndarray,
    new_valid: list[bool] | np.ndarray,
) -> dict:
    old_in = np.asarray(old_inside, dtype=bool)
    old_ok = np.asarray(old_valid, dtype=bool)
    new_in = np.asarray(new_inside, dtype=bool)
    new_ok = np.asarray(new_valid, dtype=bool)
    if len({old_in.size, old_ok.size, new_in.size, new_ok.size}) != 1:
        raise ValueError("paired point masks must have equal lengths")
    if np.any(old_ok & ~old_in) or np.any(new_ok & ~new_in):
        raise ValueError("valid point mask marks an out-of-bounds point")
    shared = old_in & new_in
    both_valid = old_ok & new_ok
    old_only = old_ok & ~new_ok
    new_only = new_ok & ~old_ok
    union_valid = old_ok | new_ok
    return {
        "observed_points": int(old_ok.size),
        "2020_inside_bounds": int(old_in.sum()),
        "2025_inside_bounds": int(new_in.sum()),
        "both_inside_bounds": int(shared.sum()),
        "2020_only_footprint": int((old_in & ~new_in).sum()),
        "2025_only_footprint": int((new_in & ~old_in).sum()),
        "both_outside_bounds": int((~old_in & ~new_in).sum()),
        "2020_valid": int(old_ok.sum()),
        "2025_valid": int(new_ok.sum()),
        "both_valid": int(both_valid.sum()),
        "2020_valid_only": int(old_only.sum()),
        "2025_valid_only": int(new_only.sum()),
        "both_invalid": int((~old_ok & ~new_ok).sum()),
        "both_valid_within_shared_footprint": int((shared & both_valid).sum()),
        "2020_only_valid_within_shared_footprint": int((shared & old_only).sum()),
        "2025_only_valid_within_shared_footprint": int((shared & new_only).sum()),
        "both_nodata_within_shared_footprint": int((shared & ~old_ok & ~new_ok).sum()),
        "2025_valid_where_2020_outside": int((~old_in & new_ok).sum()),
        "2020_valid_where_2025_outside": int((~new_in & old_ok).sum()),
        "net_valid_support_change_2025_minus_2020": int(new_ok.sum() - old_ok.sum()),
        "paired_gain_minus_loss": int(new_only.sum() - old_only.sum()),
        "validity_jaccard": (
            float(both_valid.sum() / union_valid.sum()) if union_valid.any() else None
        ),
        "validity_masks_identical": bool(np.array_equal(old_ok, new_ok)),
    }


def _read_2020_point_masks(
    session: requests.Session,
    lat: np.ndarray,
    lon: np.ndarray,
    observed: np.ndarray,
) -> tuple[dict[tuple[float, float], dict], dict]:
    label_text, label_receipt = _read_small_label(session)
    label = parse_pds3_label(label_text)
    old_crs, crs_parameters = build_hirise_crs(label)

    head = session.head(
        TIFF_URL,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
        timeout=(15, 45),
        allow_redirects=False,
    )
    try:
        if int(head.status_code) != 200:
            raise RuntimeError("2020 HiRISE TIFF HEAD did not return HTTP 200")
        raw_size = head.headers.get("Content-Length", "")
        if not raw_size.isdigit() or int(raw_size) <= 0:
            raise RuntimeError("2020 HiRISE TIFF has no positive Content-Length")
        size = int(raw_size)
        if head.headers.get("Accept-Ranges", "").lower() != "bytes":
            raise RuntimeError("2020 HiRISE TIFF does not advertise byte ranges")
    finally:
        head.close()

    reader = RangeReader(session, TIFF_URL, size, max_bytes=MAX_2020_RANGE_BYTES)
    shift_results: dict[tuple[float, float], dict] = {}
    sample_digest = hashlib.sha256()
    with tifffile.TiffFile(reader) as tif:
        if not tif.pages:
            raise RuntimeError("2020 HiRISE TIFF has no image page")
        page = tif.pages[0]
        if (int(page.imagewidth), int(page.imagelength)) != (21400, 21488):
            raise RuntimeError("2020 HiRISE TIFF dimensions differ from the pinned product")
        if (
            int(page.compression) != 1
            or page.is_tiled
            or int(page.rowsperstrip) != 1
            or page.dtype.kind != "f"
            or page.dtype.itemsize != 4
            or int(page.samplesperpixel) != 1
        ):
            raise RuntimeError("2020 HiRISE TIFF is not the pinned uncompressed one-row float32 layout")

        offsets = tuple(map(int, page.dataoffsets))
        counts = tuple(map(int, page.databytecounts))
        if len(offsets) != int(page.imagelength) or len(counts) != len(offsets):
            raise RuntimeError("2020 HiRISE TIFF strip table length mismatch")
        if any(count != int(page.imagewidth) * 4 for count in counts):
            raise RuntimeError("2020 HiRISE TIFF strip byte counts changed")
        nodata, nodata_source = _resolve_nodata(page, label)
        geo = _geo_summary(page)
        bounds = geo["raster_bounds_map_units"]
        sx, sy = map(float, geo["model_pixel_scale"])
        source_crs = pyproj.CRS.from_proj4(
            "+proj=longlat +a=" + str(MOLA_RADIUS_FALLBACK_M)
            + " +b=" + str(MOLA_RADIUS_FALLBACK_M)
            + " +no_defs +type=crs"
        )
        transformer = pyproj.Transformer.from_crs(
            source_crs, old_crs, always_xy=True
        )
        x, y = transformer.transform(lon[observed], lat[observed], errcheck=True)

        index_sets = []
        for dx, dy in TRANSLATION_OFFSETS_M:
            rows, cols, inside = point_indices(
                np.asarray(x) + dx,
                np.asarray(y) + dy,
                xmin=float(bounds["xmin"]),
                ymax=float(bounds["ymax"]),
                pixel_width=sx,
                pixel_height=sy,
                width=int(page.imagewidth),
                height=int(page.imagelength),
            )
            index_sets.append((rows, cols, inside))

        row_plan = build_row_range_plan(index_sets)
        planned_bytes = sum((last - first + 1) * 4 for first, last in row_plan.values())
        if planned_bytes <= 0 or planned_bytes > MAX_2020_RANGE_BYTES:
            raise RuntimeError("2020 HiRISE point-window plan exceeds the 4 MiB range cap")

        row_buffers: dict[int, tuple[int, np.ndarray]] = {}
        for row, (first_col, last_col) in row_plan.items():
            start = offsets[row] + first_col * 4
            length = (last_col - first_col + 1) * 4
            if start < offsets[row] or start + length > offsets[row] + counts[row]:
                raise RuntimeError("2020 HiRISE point range crosses its TIFF strip")
            reader.seek(start)
            payload = reader.read(length)
            if len(payload) != length:
                raise RuntimeError("2020 HiRISE point range returned the wrong byte count")
            sample_digest.update(payload)
            values = np.frombuffer(payload, dtype=page.dtype, count=last_col - first_col + 1)
            row_buffers[row] = (first_col, values)

        for (dx, dy), (rows, cols, inside) in zip(TRANSLATION_OFFSETS_M, index_sets):
            valid = np.zeros(len(rows), dtype=bool)
            for index in np.flatnonzero(inside):
                row = int(rows[index])
                col = int(cols[index])
                first_col, values = row_buffers[row]
                value = float(values[col - first_col])
                valid[index] = valid_sample(value, nodata)
            shift_results[(dx, dy)] = {
                "inside": np.asarray(inside, dtype=bool),
                "valid": valid,
            }

    transport = {
        "source_url": TIFF_URL,
        "product_page": "https://astrogeology.usgs.gov/search/map/Mars/Mars2020/JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40",
        "doi": "10.5066/P9REJ9JN",
        "label": label_receipt,
        "tiff_size_bytes": size,
        "range_requests": len(reader.ranges),
        "range_bytes_transferred": reader.transferred,
        "range_transfer_cap_bytes": MAX_2020_RANGE_BYTES,
        "point_row_ranges": len(row_plan),
        "planned_sample_bytes": planned_bytes,
        "sampled_bytes_sha256": sample_digest.hexdigest(),
        "raw_point_values_retained": False,
        "point_coordinates_retained": False,
        "nodata": nodata,
        "nodata_source": nodata_source,
        "crs_parameters": crs_parameters,
        "geo_metadata": {
            "model_pixel_scale": geo["model_pixel_scale"],
            "projected_crs_code": geo["projected_crs_code"],
            "projection_transform_code": geo["projection_transform_code"],
            "raster_type_code": geo["raster_type_code"],
            "pixel_is_area": geo["pixel_is_area"],
            "raster_bounds_map_units": geo["raster_bounds_map_units"],
        },
        "source_reference_radius_m": MOLA_RADIUS_FALLBACK_M,
        "target_reference_radius_m": float(crs_parameters["reference_radius_a_m"]),
    }
    return shift_results, transport, old_crs


def run() -> dict:
    receipt = {
        "experiment": "E569_PAIRED_2020_2025_HIRISE_SUPPORT_AT_FROZEN_MOLA_POINTS",
        "date": "2026-11-12",
        "outcome": "NOT_RUN",
        "claim_state": {
            "paired_2020_vs_2025_point_support_change": "NOT YET MEASURED",
            "translation_sensitivity": "NOT YET MEASURED",
            "independent_horizontal_registration": "NOT YET MEASURED",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
            "local_validation_advantage": "NOT YET PROVEN",
            "route_safety": "NOT CLAIMED",
        },
        "limitations": [
            "The denominator is the same 346 observed MOLA point centers, not area coverage.",
            "The 2025 mosaic is aligned to CTX and is not an independent horizontal control network.",
            "The +/-6 m map-translation grid is a sensitivity diagnostic, not a fitted correction or registration measurement.",
            "MOLA and HiRISE reference-sphere radii differ by 190 m; the transformation is recorded, not empirically validated.",
            "Vertical datum equivalence and elevation accuracy are not tested.",
            "No raw point elevations, raster pixels or point coordinates are retained.",
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
        count_raw, count_range = fetch_exact_range(
            session,
            COUNT_IMG,
            COUNT_NAME,
            start,
            end,
            FILE_RECORDS * COUNT_RECORD_BYTES,
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
            raise RuntimeError("frozen MOLA observed-point denominator changed from 346")
        lat, lon = mola_pixel_centers(window)

        old_masks, old_transport, old_crs = _read_2020_point_masks(
            session, lat, lon, observed
        )
        temp_dir = tempfile.TemporaryDirectory(prefix="e569-hirise-")
        dtm_path = Path(temp_dir.name) / "2025_dtm.tif"
        remote = HTTPRangeFile(
            session,
            ARCHIVE_URL,
            max_total_bytes=MAX_ARCHIVE_RANGE_BYTES,
            cache_block_bytes=CACHE_BLOCK_BYTES,
        )
        with zipfile.ZipFile(remote, mode="r") as archive:
            infos = {info.filename: info for info in archive.infolist()}
            if DTM_MEMBER not in infos:
                raise RuntimeError("pinned 2025 DTM member is missing from the archive")
            dtm_receipt = stream_member(
                archive,
                infos[DTM_MEMBER],
                dtm_path,
                EXPECTED_DTM_COMPRESSED,
                EXPECTED_DTM_UNCOMPRESSED,
            )
        archive_transport = {
            "range_requests": len(remote.ranges),
            "range_bytes_transferred": remote.transferred,
            "range_transfer_cap_bytes": MAX_ARCHIVE_RANGE_BYTES,
            "full_archive_downloaded": False,
            "orthoimage_member_read": False,
            "confidence_member_read": False,
            "temporary_dtm_deleted_after_sampling": True,
        }
        remote.close()

        with rasterio.open(dtm_path) as dataset:
            new_result = sample_raster(dataset, lat, lon, observed)
            new_inside = np.asarray(new_result["_inside_mask"], dtype=bool)
            new_valid = np.asarray(new_result["_valid_mask"], dtype=bool)
            new_crs = pyproj.CRS.from_wkt(dataset.crs.to_wkt())
            new_metadata = new_result["metadata"]

        cross_tabs = {}
        for dx, dy in TRANSLATION_OFFSETS_M:
            old = old_masks[(dx, dy)]
            cross_tabs[f"dx_{int(dx)}_dy_{int(dy)}_m"] = build_paired_cross_tab(
                old["inside"], old["valid"], new_inside, new_valid
            )

        baseline = cross_tabs["dx_0_dy_0_m"]
        old_valid_counts = [
            cross_tabs[f"dx_{int(dx)}_dy_{int(dy)}_m"]["2020_valid"]
            for dx, dy in TRANSLATION_OFFSETS_M
        ]
        old_crs_equivalent = old_crs.equals(new_crs, ignore_axis_order=True)

        receipt["mola_source"] = {
            "counts_label": count_label_receipt,
            "counts_range": count_range,
            "window": window,
            "observed_shot_bins": int(observed.sum()),
            "total_bins": int(observed.size),
            "raw_counts_retained": False,
        }
        receipt["2020_hirise"] = old_transport
        receipt["2025_hirise"] = {
            "product_page": "https://astrogeology.usgs.gov/search/map/mars-sample-return-terrain-relative-navigation-hirise-dtm-mosaic",
            "doi": "10.5066/P13CPYYU",
            "archive_url": ARCHIVE_URL,
            "dtm_member_receipt": dtm_receipt,
            "archive_transport": archive_transport,
            "raster_metadata": {
                "width": new_metadata["width"],
                "height": new_metadata["height"],
                "dtype": new_metadata["dtype"],
                "nodata": new_metadata["nodata"],
                "scale": new_metadata["scale"],
                "offset": new_metadata["offset"],
                "crs": new_metadata["crs"],
                "transform": new_metadata["transform"],
                "bounds": new_metadata["bounds"],
                "resolution": new_metadata["resolution"],
            },
            "inside_bounds": int(new_inside.sum()),
            "valid_samples": int(new_valid.sum()),
        }
        receipt["crs_comparison"] = {
            "parameter_equivalent_under_pyproj": bool(old_crs_equivalent),
            "2020_reference_radius_m": old_transport["target_reference_radius_m"],
            "mola_reference_radius_m": MOLA_RADIUS_FALLBACK_M,
            "radius_difference_m": old_transport["target_reference_radius_m"] - MOLA_RADIUS_FALLBACK_M,
            "independent_horizontal_control": False,
        }
        receipt["paired_cross_tabs"] = cross_tabs
        receipt["translation_sensitivity_summary"] = {
            "offsets_m": [{"dx": dx, "dy": dy} for dx, dy in TRANSLATION_OFFSETS_M],
            "2020_valid_support_min": int(min(old_valid_counts)),
            "2020_valid_support_max": int(max(old_valid_counts)),
            "2020_valid_support_at_zero_shift": int(baseline["2020_valid"]),
            "2025_valid_support_fixed": int(new_valid.sum()),
            "paired_net_gain_min": int(min(
                value["net_valid_support_change_2025_minus_2020"]
                for value in cross_tabs.values()
            )),
            "paired_net_gain_max": int(max(
                value["net_valid_support_change_2025_minus_2020"]
                for value in cross_tabs.values()
            )),
            "sensitivity_is_not_registration_evidence": True,
        }
        expected_reproduced = (
            baseline["2020_valid"] == 164
            and baseline["2025_valid"] == 259
            and baseline["observed_points"] == 346
        )
        receipt["aggregate_reconciliation"] = {
            "E563_2020_valid_count_reproduced": baseline["2020_valid"] == 164,
            "E568_2025_valid_count_reproduced": baseline["2025_valid"] == 259,
            "frozen_observed_denominator_reproduced": baseline["observed_points"] == 346,
            "all_three_expected_aggregates_reproduced": expected_reproduced,
        }
        receipt["claim_state"]["paired_2020_vs_2025_point_support_change"] = (
            "MEASURED FOR THIS FROZEN 346-POINT WINDOW"
            if expected_reproduced
            else "MEASURED BUT PRIOR AGGREGATE RECONCILIATION FAILED"
        )
        receipt["claim_state"]["translation_sensitivity"] = (
            "MEASURED FOR FIXED +/-6 M MAP SHIFTS"
        )
        receipt["outcome"] = (
            "PAIRED_SUPPORT_AND_TRANSLATION_SENSITIVITY_MEASURED"
            if expected_reproduced
            else "PAIRED_SUPPORT_MEASURED_WITH_AGGREGATE_MISMATCH"
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
    print(json.dumps({
        "experiment": receipt["experiment"],
        "outcome": receipt["outcome"],
        "paired_net_gain": receipt.get("paired_cross_tabs", {}).get("dx_0_dy_0_m", {}).get("net_valid_support_change_2025_minus_2020"),
        "2020_valid": receipt.get("paired_cross_tabs", {}).get("dx_0_dy_0_m", {}).get("2020_valid"),
        "2025_valid": receipt.get("paired_cross_tabs", {}).get("dx_0_dy_0_m", {}).get("2025_valid"),
        "range_bytes_2020": receipt.get("2020_hirise", {}).get("range_bytes_transferred"),
        "range_bytes_2025": receipt.get("2025_hirise", {}).get("archive_transport", {}).get("range_bytes_transferred"),
    }, sort_keys=True))
    return 0 if receipt["outcome"].startswith("PAIRED_SUPPORT") else 1


if __name__ == "__main__":
    raise SystemExit(main())
