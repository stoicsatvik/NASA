"""E571: test the PDS-documented LOLA 45-degree latitude-band seam.

Reuses E570's pinned product contract and bounded range reader. It samples
three 11x11 windows at one longitude: the -45 degree seam and controls at
-44.5/-45.5 degrees. Raw raster values are never retained.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import requests

from experiments.e570_lola_gdr_sample import (
    IMAGE_URL,
    LABEL_URL,
    MAX_TOTAL_TRANSFER_BYTES,
    WINDOW_SIZE,
    fetch_label,
    fetch_window,
)

CENTERS = (
    {"id": "seam_baseline", "latitude_deg": -45.0, "longitude_deg_east": 90.0},
    {"id": "north_control", "latitude_deg": -44.5, "longitude_deg_east": 90.0},
    {"id": "south_control", "latitude_deg": -45.5, "longitude_deg_east": 90.0},
)
E570_REPORTED_SEAM_RELIEF_M = 1662.64
METRICS = (
    "radial_height_relief_p95_p05_m",
    "radial_height_mad_m",
    "median_local_slope_deg",
    "p90_local_slope_deg",
)


def overlap_rows(a: dict[str, Any], b: dict[str, Any]) -> int:
    a0, a1 = a["window_rows_zero_based"]
    b0, b1 = b["window_rows_zero_based"]
    return max(0, min(a1, b1) - max(a0, b0) + 1)


def compare_windows(windows: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {item["id"]: item for item in windows}
    required = {"seam_baseline", "north_control", "south_control"}
    if set(by_id) != required:
        raise ValueError(f"expected exactly {sorted(required)}; got {sorted(by_id)}")

    seam = by_id["seam_baseline"]
    north = by_id["north_control"]
    south = by_id["south_control"]
    result: dict[str, Any] = {
        "same_longitude_deg_east": 90.0,
        "window_size_pixels": WINDOW_SIZE,
        "north_seam_shared_rows": overlap_rows(seam, north),
        "south_seam_shared_rows": overlap_rows(seam, south),
        "overlap_fraction_of_each_window": {
            "north": overlap_rows(seam, north) / WINDOW_SIZE,
            "south": overlap_rows(seam, south) / WINDOW_SIZE,
        },
        "metrics": {},
    }
    for metric in METRICS:
        values = [
            seam["descriptor"].get(metric),
            north["descriptor"].get(metric),
            south["descriptor"].get(metric),
        ]
        if any(value is None for value in values):
            result["metrics"][metric] = {
                "seam": values[0],
                "north": values[1],
                "south": values[2],
                "comparison": "NOT_COMPUTABLE",
            }
            continue
        seam_value, north_value, south_value = map(float, values)
        control_mean = (north_value + south_value) / 2.0
        result["metrics"][metric] = {
            "seam": seam_value,
            "north": north_value,
            "south": south_value,
            "control_mean": control_mean,
            "seam_minus_control_mean": seam_value - control_mean,
            "seam_to_control_mean_ratio": (
                seam_value / control_mean if control_mean != 0 else None
            ),
            "seam_exceeds_both_controls": (
                seam_value > north_value and seam_value > south_value
            ),
            "north_south_control_difference": abs(north_value - south_value),
        }
    seam_relief = seam["descriptor"]["radial_height_relief_p95_p05_m"]
    result["e570_reacquisition_check"] = {
        "e570_reported_seam_relief_m_rounded": E570_REPORTED_SEAM_RELIEF_M,
        "e571_reacquired_seam_relief_m": seam_relief,
        "absolute_difference_from_rounded_e570_report_m": abs(
            float(seam_relief) - E570_REPORTED_SEAM_RELIEF_M
        ),
        "comparison_note": "E570 report value is rounded to 0.01 m; this is a repeatability check, not an independent sample.",
    }
    return result


def run() -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "experiment": "E571_LOLA_45_DEGREE_SEAM_CONTROL",
        "date": "2026-11-12",
        "outcome": "NOT_RUN",
        "source": {
            "label_url": LABEL_URL,
            "image_url": IMAGE_URL,
            "parent_experiment": "E570_LOLA_GDR_BOUNDED_REAL_SAMPLE",
        },
        "centers": list(CENTERS),
        "claim_state": {
            "LOLA_GDR_metadata": "SUPPORTED",
            "bounded_LOLA_real_sample_ingestion": "SUPPORTED",
            "local_seam_control_comparison": "NOT YET MEASURED",
            "seam_artifact_attribution": "NOT YET PROVEN",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
        },
        "limitations": [
            "All three windows share one longitude and one analyst-selected location; this is not a spatially representative seam survey.",
            "Each adjacent control overlaps the seam window by three of eleven rows, so windows are not independent replicates.",
            "A descriptor difference is a candidate seam confound, not proof that the seam caused it; natural terrain can vary over the same distance.",
            "LOLA radial height remains relative to the PDS reference sphere; no geoid correction is applied.",
            "No raw raster values or full IMG file are retained.",
        ],
    }
    session = requests.Session()
    try:
        _, label_receipt = fetch_label(session)
        receipt["label"] = label_receipt
        fields = label_receipt["pds_fields"]
        total_bytes = int(label_receipt["content_bytes"])
        windows: list[dict[str, Any]] = []
        receipt["windows"] = windows
        hashes: list[str] = []
        for center in CENTERS:
            item, transferred, digest = fetch_window(session, fields, center)
            total_bytes += transferred
            if total_bytes > MAX_TOTAL_TRANSFER_BYTES:
                raise RuntimeError("E571 total transfer exceeded the inherited 1 MB cap")
            windows.append(item)
            hashes.append(digest)
        receipt["comparison"] = compare_windows(windows)
        receipt["transport"] = {
            "range_requests": len(windows),
            "range_bytes_transferred": sum(
                int(item["range_bytes_transferred"]) for item in windows
            ),
            "label_bytes_transferred": int(label_receipt["content_bytes"]),
            "total_bytes_transferred": total_bytes,
            "total_transfer_cap_bytes": MAX_TOTAL_TRANSFER_BYTES,
            "range_sha256": hashes,
            "full_img_downloaded": False,
            "raw_pixel_values_retained": False,
        }
        receipt["outcome"] = "LOLA_SEAM_AND_ADJACENT_CONTROLS_ACQUIRED"
        receipt["claim_state"]["local_seam_control_comparison"] = "SUPPORTED_FOR_THIS_SINGLE_LOCATION"
        receipt["claim_state"]["seam_artifact_attribution"] = "NOT YET PROVEN"
    except Exception as exc:  # preserve bounded acquisition failures in the receipt
        receipt["outcome"] = "ACQUISITION_FAILED"
        receipt["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        session.close()
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "experiment": result["experiment"],
        "outcome": result["outcome"],
        "windows": len(result.get("windows", [])),
        "range_bytes": result.get("transport", {}).get("range_bytes_transferred"),
        "seam_artifact_attribution": result["claim_state"]["seam_artifact_attribution"],
    }, sort_keys=True))
    return 0 if result["outcome"] == "LOLA_SEAM_AND_ADJACENT_CONTROLS_ACQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
