"""E573: paired HiRISE support sensitivity to a published 10.2 m alignment envelope.

This is a bounded support-sensitivity experiment, not a registration measurement.
It samples the same 346 observed MOLA point centers in the pinned 2020 and 2025
HiRISE DTMs under deterministic coherent and differential map translations.
Only masks, counts, metadata and source hashes are retained.
"""
from __future__ import annotations

import argparse
import json
import math
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pyproj
import rasterio
import requests
from rasterio.windows import Window

import experiments.e569_paired_hirise_support as e569

MAX_2020_RANGE_BYTES = 16 * 1024 * 1024
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
    stream_member,
)

INNER_RADIUS_M = 5.1
OUTER_RADIUS_M = 10.2
OFFSETS_M = (
    (0.0, 0.0),
    (-INNER_RADIUS_M, 0.0),
    (INNER_RADIUS_M, 0.0),
    (0.0, -INNER_RADIUS_M),
    (0.0, INNER_RADIUS_M),
    (-OUTER_RADIUS_M, 0.0),
    (OUTER_RADIUS_M, 0.0),
    (0.0, -OUTER_RADIUS_M),
    (0.0, OUTER_RADIUS_M),
    (-OUTER_RADIUS_M / math.sqrt(2), -OUTER_RADIUS_M / math.sqrt(2)),
    (-OUTER_RADIUS_M / math.sqrt(2), OUTER_RADIUS_M / math.sqrt(2)),
    (OUTER_RADIUS_M / math.sqrt(2), -OUTER_RADIUS_M / math.sqrt(2)),
    (OUTER_RADIUS_M / math.sqrt(2), OUTER_RADIUS_M / math.sqrt(2)),
)
OFFSETS_M = tuple((round(dx, 9), round(dy, 9)) for dx, dy in OFFSETS_M)
EXPECTED_OBSERVED_POINTS = 346
EXPECTED_2020_VALID = 164
EXPECTED_2025_VALID = 259
USER_AGENT = "Unified-Parallel-Foundry-E573/1.0"


def offset_key(dx: float, dy: float) -> str:
    def token(value: float) -> str:
        return f"{value:+.6f}".replace("+", "p").replace("-", "m").replace(".", "_")
    return f"dx_{token(dx)}_dy_{token(dy)}_m"


def sample_2025_at_offset(
    dataset,
    lat: np.ndarray,
    lon: np.ndarray,
    observed: np.ndarray,
    dx_m: float,
    dy_m: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Return in-bounds and finite/non-nodata masks; never return pixel values."""
    if dataset.driver != "GTiff" or dataset.count < 1:
        raise ValueError("selected member is not a readable GeoTIFF")
    if dataset.crs is None or dataset.width <= 0 or dataset.height <= 0:
        raise ValueError("selected GeoTIFF has incomplete CRS or dimensions")

    source_crs = pyproj.CRS.from_proj4(
        f"+proj=longlat +a={MOLA_RADIUS_FALLBACK_M} "
        f"+b={MOLA_RADIUS_FALLBACK_M} +no_defs +type=crs"
    )
    target_crs = pyproj.CRS.from_wkt(dataset.crs.to_wkt())
    transformer = pyproj.Transformer.from_crs(
        source_crs, target_crs, always_xy=True
    )
    x, y = transformer.transform(lon, lat, errcheck=True)
    inside = np.zeros(observed.shape, dtype=bool)
    valid = np.zeros(observed.shape, dtype=bool)

    for row_index, col_index in zip(*np.where(observed)):
        row, col = dataset.index(
            float(x[row_index, col_index]) + dx_m,
            float(y[row_index, col_index]) + dy_m,
        )
        if not (0 <= row < dataset.height and 0 <= col < dataset.width):
            continue
        inside[row_index, col_index] = True
        sample = dataset.read(
            1,
            window=Window(int(col), int(row), 1, 1),
            masked=True,
        )[0, 0]
        if np.ma.is_masked(sample):
            continue
        value = float(sample)
        if math.isfinite(value) and (
            dataset.nodata is None or value != float(dataset.nodata)
        ):
            valid[row_index, col_index] = True

    if np.any(valid & ~inside):
        raise AssertionError("valid mask contains an out-of-bounds point")
    return inside, valid


def summarize_tabs(tabs: dict[str, dict]) -> dict:
    if not tabs:
        raise ValueError("at least one translation result is required")
    rows = list(tabs.values())
    margins = [
        int(row["net_valid_support_change_2025_minus_2020"])
        for row in rows
    ]
    return {
        "offset_count": len(rows),
        "min_2020_valid": min(int(row["2020_valid"]) for row in rows),
        "max_2020_valid": max(int(row["2020_valid"]) for row in rows),
        "min_2025_valid": min(int(row["2025_valid"]) for row in rows),
        "max_2025_valid": max(int(row["2025_valid"]) for row in rows),
        "min_2025_minus_2020": min(margins),
        "max_2025_minus_2020": max(margins),
        "2025_support_advantage_at_every_tested_offset": min(margins) > 0,
        "margins_by_offset": margins,
    }


def run() -> dict:
    receipt = {
        "experiment": "E573_HIRISE_10_2M_TRANSLATION_ENVELOPE",
        "date": "2026-11-12",
        "outcome": "NOT_RUN",
        "design": {
            "observed_point_source": "same frozen MOLA 33x33 window as E563/E569",
            "expected_observed_points": EXPECTED_OBSERVED_POINTS,
            "2020_range_transfer_cap_bytes": MAX_2020_RANGE_BYTES,
            "translation_offsets_m": [
                {"dx": dx, "dy": dy, "radius": math.hypot(dx, dy)}
                for dx, dy in OFFSETS_M
            ],
            "inner_radius_m": INNER_RADIUS_M,
            "outer_radius_m": OUTER_RADIUS_M,
            "comparison_modes": [
                "common_mode: apply the same coherent map translation to 2020 and 2025",
                "differential_2025: keep 2020 fixed and translate 2025 relative to it",
            ],
        },
        "claim_state": {
            "2025_vs_2020_point_support_difference": "NOT YET RE-MEASURED",
            "support_advantage_under_common_mode_translation": "NOT YET MEASURED",
            "support_advantage_under_2025_only_translation": "NOT YET MEASURED",
            "independent_horizontal_registration": "NOT YET MEASURED",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
            "route_safety": "NOT CLAIMED",
        },
        "limitations": [
            "The 10.2 m value is a published 99th-percentile HiRISE-to-CTX alignment statistic, not a hard bound or a measured MOLA tie.",
            "The 13 deterministic translations are a sensitivity grid, not a probability distribution or confidence region.",
            "The E573 2020 point-window range cap is 16 MiB (the inherited E569 cap was 4 MiB); actual transferred bytes remain bounded and recorded.",
            "Common-mode translations test shared map-frame sensitivity; differential_2025 translations test a 2025-only shift relative to the fixed 2020 mask.",
            "The 2025 mosaic is aligned to CTX and is not an independent horizontal control network.",
            "The denominator is 346 observed MOLA point centers, not area coverage.",
            "No raw elevation values, raster pixels or point coordinates are retained.",
            "Support differences do not establish terrain accuracy, route safety or analogue similarity.",
        ],
    }
    session = requests.Session()
    temp_dir = None
    remote = None
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
        if int(observed.sum()) != EXPECTED_OBSERVED_POINTS:
            raise RuntimeError(
                "frozen MOLA observed-point denominator changed from 346"
            )
        lat, lon = mola_pixel_centers(window)

        # Reuse E569's exact bounded 2020 reader with this experiment's frozen offsets.
        e569.TRANSLATION_OFFSETS_M = OFFSETS_M
        # The wider 13-offset union needs a larger but still bounded range budget.
        e569.MAX_2020_RANGE_BYTES = MAX_2020_RANGE_BYTES
        old_masks, old_transport, old_crs = e569._read_2020_point_masks(
            session, lat, lon, observed
        )

        temp_dir = tempfile.TemporaryDirectory(prefix="e573-hirise-")
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
        remote = None

        with rasterio.open(dtm_path) as dataset:
            new_crs = pyproj.CRS.from_wkt(dataset.crs.to_wkt())
            if not old_crs.equals(new_crs, ignore_axis_order=True):
                raise RuntimeError(
                    "2020 and 2025 HiRISE map CRSs are not parameter-equivalent"
                )
            metadata = {
                "width": int(dataset.width),
                "height": int(dataset.height),
                "dtype": list(dataset.dtypes),
                "nodata": float(dataset.nodata) if dataset.nodata is not None else None,
                "crs": dataset.crs.to_string(),
                "crs_wkt_sha256": __import__("hashlib").sha256(
                    dataset.crs.to_wkt().encode("utf-8")
                ).hexdigest(),
                "transform": [
                    float(dataset.transform.a), float(dataset.transform.b),
                    float(dataset.transform.c), float(dataset.transform.d),
                    float(dataset.transform.e), float(dataset.transform.f),
                ],
                "bounds": {
                    "left": float(dataset.bounds.left),
                    "bottom": float(dataset.bounds.bottom),
                    "right": float(dataset.bounds.right),
                    "top": float(dataset.bounds.top),
                },
                "resolution": [float(dataset.res[0]), float(dataset.res[1])],
            }
            new_masks = {
                offset: sample_2025_at_offset(
                    dataset, lat, lon, observed, offset[0], offset[1]
                )
                for offset in OFFSETS_M
            }

        common_mode_tabs = {}
        differential_tabs = {}
        zero = (0.0, 0.0)
        old_zero = old_masks[zero]
        for offset in OFFSETS_M:
            key = offset_key(*offset)
            new_inside, new_valid = new_masks[offset]
            old = old_masks[offset]
            common_mode_tabs[key] = e569.build_paired_cross_tab(
                old["inside"], old["valid"], new_inside, new_valid
            )
            differential_tabs[key] = e569.build_paired_cross_tab(
                old_zero["inside"], old_zero["valid"], new_inside, new_valid
            )

        baseline_key = offset_key(*zero)
        baseline = common_mode_tabs[baseline_key]
        expected_reproduced = (
            baseline["observed_points"] == EXPECTED_OBSERVED_POINTS
            and baseline["2020_valid"] == EXPECTED_2020_VALID
            and baseline["2025_valid"] == EXPECTED_2025_VALID
        )
        common_summary = summarize_tabs(common_mode_tabs)
        differential_summary = summarize_tabs(differential_tabs)

        receipt["mola_source"] = {
            "counts_label": count_label_receipt,
            "counts_range": count_range,
            "window": window,
            "observed_shot_bins": int(observed.sum()),
            "total_bins": int(observed.size),
            "raw_counts_retained": False,
        }
        old_transport["range_transfer_cap_bytes"] = MAX_2020_RANGE_BYTES
        receipt["2020_hirise"] = old_transport
        receipt["2025_hirise"] = {
            "product_page": "https://astrogeology.usgs.gov/search/map/mars-sample-return-terrain-relative-navigation-hirise-dtm-mosaic",
            "doi": "10.5066/P13CPYYU",
            "archive_url": ARCHIVE_URL,
            "dtm_member_receipt": dtm_receipt,
            "archive_transport": archive_transport,
            "raster_metadata": metadata,
        }
        receipt["crs_comparison"] = {
            "parameter_equivalent_under_pyproj": True,
            "independent_horizontal_control": False,
            "2020_reference_radius_m": old_transport["target_reference_radius_m"],
            "mola_reference_radius_m": MOLA_RADIUS_FALLBACK_M,
            "radius_difference_m": (
                old_transport["target_reference_radius_m"] - MOLA_RADIUS_FALLBACK_M
            ),
        }
        receipt["baseline_reconciliation"] = {
            "observed_points_expected": EXPECTED_OBSERVED_POINTS,
            "observed_points_measured": baseline["observed_points"],
            "2020_valid_expected": EXPECTED_2020_VALID,
            "2020_valid_measured": baseline["2020_valid"],
            "2025_valid_expected": EXPECTED_2025_VALID,
            "2025_valid_measured": baseline["2025_valid"],
            "all_expected_aggregates_reproduced": expected_reproduced,
        }
        receipt["common_mode_translation"] = {
            "interpretation": "same rigid map shift applied to both products relative to MOLA",
            "summary": common_summary,
            "cross_tabs": common_mode_tabs,
        }
        receipt["differential_2025_translation"] = {
            "interpretation": "2020 remains at zero shift; only 2025 is translated relative to it",
            "summary": differential_summary,
            "cross_tabs": differential_tabs,
        }
        receipt["claim_state"]["2025_vs_2020_point_support_difference"] = (
            "MEASURED FOR THIS FROZEN 346-POINT WINDOW"
            if expected_reproduced
            else "MEASURED BUT BASELINE RECONCILIATION FAILED"
        )
        receipt["claim_state"]["support_advantage_under_common_mode_translation"] = (
            "SUPPORTED FOR ALL TESTED OFFSETS"
            if common_summary["2025_support_advantage_at_every_tested_offset"]
            else "NOT ROBUST ACROSS ALL TESTED OFFSETS"
        )
        receipt["claim_state"]["support_advantage_under_2025_only_translation"] = (
            "SUPPORTED FOR ALL TESTED OFFSETS"
            if differential_summary["2025_support_advantage_at_every_tested_offset"]
            else "NOT ROBUST ACROSS ALL TESTED OFFSETS"
        )
        receipt["outcome"] = (
            "BASELINE_REPRODUCED_AND_SUPPORT_ADVANTAGE_ROBUST"
            if expected_reproduced
            and common_summary["2025_support_advantage_at_every_tested_offset"]
            and differential_summary["2025_support_advantage_at_every_tested_offset"]
            else (
                "BASELINE_REPRODUCED_BUT_SUPPORT_ADVANTAGE_NOT_ROBUST"
                if expected_reproduced
                else "BASELINE_RECONCILIATION_FAILED"
            )
        )
    except Exception as exc:
        receipt["outcome"] = "ERROR"
        receipt["error"] = {
            "kind": type(exc).__name__,
            "message": str(exc)[:700],
        }
    finally:
        if remote is not None:
            remote.close()
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
        "common_mode_min_margin": receipt.get("common_mode_translation", {}).get("summary", {}).get("min_2025_minus_2020"),
        "differential_min_margin": receipt.get("differential_2025_translation", {}).get("summary", {}).get("min_2025_minus_2020"),
        "baseline": receipt.get("baseline_reconciliation"),
        "archive_range_bytes": receipt.get("2025_hirise", {}).get("archive_transport", {}).get("range_bytes_transferred"),
    }, sort_keys=True))
    return 0 if receipt["outcome"].startswith("BASELINE_REPRODUCED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
