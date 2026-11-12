"""E576: test whether public HRSC evidence can supply independent 10 m-scale control.

This is a deterministic source-admissibility audit. It does not download imagery,
derive new coordinates, or claim route safety.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TARGET_RELATIVE_STATISTIC_M = 10.2


def run() -> dict[str, Any]:
    calibration = {"S1": 145.31, "S2": 144.61}
    validation = {
        "I818": {"S1": 217.017, "S2": 235.313},
        "I863": {"S1": 273.349, "S2": 301.776},
        "I977": {"S1": 178.716, "S2": 286.364},
    }
    validation_values = [value for orbit in validation.values() for value in orbit.values()]
    best_calibration = min(calibration.values())
    best_validation = min(validation_values)

    return {
        "experiment": "E576_HRSC_INDEPENDENT_CONTROL_ADMISSIBILITY",
        "date": "2026-11-12",
        "question": (
            "Can public Mars Express HRSC evidence provide independent horizontal control "
            "with documented accuracy materially below the 10.2 m CTX-relative statistic "
            "reported for the pinned 2025 HiRISE mosaic?"
        ),
        "comparison_gate": {
            "target_relative_statistic_m": TARGET_RELATIVE_STATISTIC_M,
            "target_metric": "99th-percentile CTX-relative mosaic alignment",
            "warning": (
                "This is a scale-screening comparison, not a formal uncertainty ratio: "
                "the HRSC paper reports MOLA-GCP horizontal positional accuracy, while "
                "10.2 m is a CTX-relative alignment percentile."
            ),
        },
        "sources": {
            "li_jiang_2023": {
                "title": "Geometric Calibration of the ESA Mars Express Orbiter High Resolution Stereo Camera",
                "doi": "10.1029/2023EA002971",
                "url": "https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2023EA002971",
                "facts": {
                    "control_source": "MOLA PEDR ground-control points",
                    "calibration_gcp_count": 476,
                    "overlapping_mola_track_count": 126,
                    "overlapping_mola_point_count": 125749,
                    "mola_planimetric_accuracy_order_m": 100.0,
                    "mola_footprint_diameter_m": 168.0,
                    "mola_footprint_spacing_m": 300.0,
                    "calibration_horizontal_accuracy_m": calibration,
                    "validation_horizontal_accuracy_m": validation,
                    "metric": "horizontal positional accuracy assessed against MOLA GCP coordinates",
                },
                "control_role": (
                    "Independent sensor family, but absolute horizontal control is MOLA-GCP "
                    "controlled and remains on the order of hundreds of metres."
                ),
            },
            "kirk_fergason_2020": {
                "title": "Evaluating stereo DTM quality at Jezero Crater, Mars with HRSC, CTX, and HiRISE images",
                "doi": "10.5194/isprs-archives-XLIII-B3-2020-1129-2020",
                "url": "https://isprs-archives.copernicus.org/articles/XLIII-B3-2020/1129/2020/",
                "facts": {
                    "reference_dataset": "mosaicked HiRISE DTM",
                    "evaluated_datasets": ["MEX HRSC", "MRO CTX"],
                    "horizontal_resolution_pixels": [10, 20],
                    "typical_dtm_ground_sample_distance_pixels": [3, 5],
                    "independent_absolute_control_residual_m": None,
                },
                "control_role": (
                    "Relative DTM quality comparison using HiRISE as the reference; "
                    "not an independent absolute horizontal-control network."
                ),
            },
        },
        "derived_screening": {
            "best_hrsc_calibration_accuracy_m": best_calibration,
            "best_hrsc_validation_accuracy_m": best_validation,
            "calibration_scale_ratio_to_10_2m": best_calibration / TARGET_RELATIVE_STATISTIC_M,
            "validation_scale_ratio_to_10_2m": best_validation / TARGET_RELATIVE_STATISTIC_M,
            "ratios_are_formal_uncertainty_comparisons": False,
            "interpretation": (
                "Even as a coarse scale screen, the best reported HRSC horizontal positional "
                "accuracy is about 14 times the 10.2 m target statistic; validation values "
                "are larger. The metrics are not statistically commensurate."
            ),
        },
        "admissibility": {
            "hrsc_is_an_independent_sensor_family": True,
            "published_hrsc_absolute_control_uses_mola_gcps": True,
            "hrsc_absolute_control_materially_below_10_2m": False,
            "kirk_2020_uses_hirise_as_reference": True,
            "kirk_2020_supplies_independent_absolute_control": False,
            "hrsc_admissible_for_10m_horizontal_validation": False,
            "hrsc_useful_for_coarse_cross_sensor_or_gross_error_checks": True,
        },
        "result": "NEGATIVE",
        "interpretation": (
            "HRSC is a genuinely separate sensor family, but the retrieved public absolute "
            "positioning evidence is controlled by MOLA and reports 144.61-145.31 m for the "
            "calibration image and 178.716-301.776 m for validation images. The 2020 USGS/ISPRS "
            "comparison uses HiRISE as its reference and reports horizontal resolution, not "
            "independent absolute registration. HRSC therefore does not satisfy the current "
            "10 m-scale independent-control gate. It remains useful for coarse cross-sensor "
            "comparison and gross-error screening only."
        ),
        "claim_state": {
            "repo_operating_system": "SUPPORTED",
            "internal_hirise_alignment": "SUPPORTED AS REPORTED",
            "independent_horizontal_registration": "NOT YET MEASURED",
            "absolute_horizontal_accuracy_of_pinned_2025_dtm": "NOT ESTABLISHED",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
            "route_safety": "NOT CLAIMED",
            "planetary_analog_challenge_superiority": "NOT YET PROVEN",
        },
        "challenge_selection": {
            "martian_map_11_score": 4.10,
            "modis_viirs_9_score": 4.00,
            "planetary_analog_10_score": 2.93,
            "ranking": "PROVISIONAL",
            "challenge_locked": False,
            "score_changed": False,
        },
        "next_gate": (
            "Find a separate ground-control network or independently controlled product "
            "with documented horizontal uncertainty materially below 10.2 m and no shared "
            "CTX/HiRISE/MOLA control dependency. Do not use HRSC/MOLA as 10 m validation; "
            "retain it only as a coarse independent-sensor cross-check."
        ),
        "limitations": [
            "No new raster or coordinate sample was acquired.",
            "The HRSC accuracy values and the 10.2 m CTX-relative percentile are different metrics.",
            "The 2020 comparison's HiRISE reference prevents it from serving as independent absolute control.",
            "No route-safety, terrain-hazard, cross-body similarity, or analogue-recovery claim is made.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
