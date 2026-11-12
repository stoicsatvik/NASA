"""E575: audit whether published HiRISE alignment numbers are independent control.

This is a source-provenance audit. It does not download or sample a raster and
does not convert relative alignment statistics into absolute accuracy.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def run() -> dict[str, Any]:
    return {
        "experiment": "E575_HIRISE_CONTROL_SOURCE_INDEPENDENCE_AUDIT",
        "date": "2026-11-12",
        "scope": "public-source audit of the pinned 2025 Mars Sample Return HiRISE DTM mosaic",
        "sources": {
            "usgs_msr_product": {
                "url": "https://astrogeology.usgs.gov/search/map/mars-sample-return-terrain-relative-navigation-hirise-dtm-mosaic",
                "doi": "10.5066/P13CPYYU",
                "facts": {
                    "individual_dem_horizontal_alignment_p99_m": 0.9,
                    "individual_dem_vertical_offset_p99_m": 2.3,
                    "mosaic_to_ctx_horizontal_alignment_p93_m": 6.0,
                    "mosaic_to_ctx_horizontal_alignment_p99_m": 10.2,
                    "stereo_pairs_completed": 8,
                    "stereo_pairs_total": 10,
                },
                "reference_role": "individual DEM internal alignment and CTX-relative mosaic alignment",
            },
            "lpsc_2025": {
                "url": "https://www.hou.usra.edu/meetings/lpsc2025/pdf/1627.pdf",
                "title": "HiRISE Digital Elevation Model and Orthoimage Mosaics in Support of Perseverance Operations and Mars Sample Return",
                "facts": {
                    "individual_dem_horizontal_alignment_p99_m": 0.9,
                    "individual_dem_vertical_offset_p99_m": 2.3,
                    "mosaic_to_ctx_horizontal_alignment_p93_m": 6.0,
                    "mosaic_to_ctx_horizontal_alignment_p99_m": 10.2,
                    "inter_mosaic_alignment_p30_m": 1.0,
                    "inter_mosaic_alignment_p80_m": 3.0,
                    "inter_mosaic_alignment_method": "ASP normalized cross-correlation between orthoimages",
                    "localized_offsets_correlate_with": ["dune fields", "smooth texture", "dark regions"],
                    "candidate_causes": ["unresolved source-image jitter", "incorrect camera-model intrinsics"],
                },
                "reference_role": "relative internal and CTX-reference alignment; inter-mosaic check uses orthoimage correlation",
            },
            "usgs_hirise_ard_guidance": {
                "url": "https://stac.astrogeology.usgs.gov/docs/data/mars/hirise_dtms/",
                "facts": {
                    "general_horizontal_accuracy_relative_to_mola_pedr_best_case_m": 100.0,
                    "general_vertical_accuracy_relative_to_mola_pedr_m": 1.3,
                    "mola_shot_footprint_approx_m": 100.0,
                },
                "reference_role": "general HiRISE DTM guidance only; not a 2025 product-specific residual",
            },
        },
        "control_independence_audit": {
            "10_2m_is_absolute_horizontal_accuracy": False,
            "10_2m_is_ctx_relative_p99_alignment": True,
            "0_9m_is_independent_ground_control": False,
            "0_9m_is_internal_individual_dem_alignment": True,
            "1m_3m_inter_mosaic_values_are_independent_ground_control": False,
            "1m_3m_method_uses_orthoimage_correlation": True,
            "mola_pedr_is_an_independent_sensor_family": True,
            "mola_pedr_horizontal_support_sufficient_for_10m_validation": False,
            "2025_product_specific_held_out_mola_horizontal_residual_found": False,
            "independent_horizontal_control_for_pinned_2025_dtm_found": False,
        },
        "interpretation": {
            "supported": [
                "The 2025 mosaic has published internal DEM alignment statistics.",
                "The 2025 mosaic has published CTX-relative alignment percentiles.",
                "The 2025 and Mars-2020 HiRISE mosaics have a published relative orthoimage-alignment check.",
            ],
            "not_established": [
                "Absolute horizontal accuracy of the pinned 2025 DTM.",
                "An independent horizontal control residual for the pinned 2025 DTM.",
                "Route safety or hazard avoidance.",
                "Cross-body similarity or known-site analogue recovery.",
            ],
            "reason": "The published 10.2 m value is relative to CTX. The 1 m/3 m inter-mosaic values come from orthoimage correlation, not an independent ground-control network or DTM-to-ground-truth residual.",
        },
        "challenge_selection": {
            "martian_map_11_score": 4.10,
            "modis_viirs_9_score": 4.00,
            "planetary_analog_10_score": 2.93,
            "ranking_state": "PROVISIONAL; no numeric score change because no frozen score factor changed",
            "challenge_locked": False,
        },
        "claim_state": {
            "repo_operating_system": "SUPPORTED",
            "2025_hirise_internal_alignment": "SUPPORTED AS REPORTED",
            "2025_hirise_ctx_relative_alignment": "SUPPORTED AS REPORTED",
            "independent_horizontal_registration": "NOT YET MEASURED",
            "absolute_horizontal_accuracy": "NOT ESTABLISHED",
            "route_safety": "NOT CLAIMED",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
            "planetary_analog_challenge_superiority": "NOT YET PROVEN",
        },
        "next_gate": "A held-out MOLA PEDR track is an independent sensor-family cross-check but its approximately 100 m shot footprint is too coarse to validate a 10.2 m residual; use it only for gross-error screening. For a 10 m-scale horizontal residual, acquire a separate control network or independently controlled product with documented horizontal uncertainty materially below 10.2 m, then measure held-out multi-patch residuals without fitting a corrective shift to evaluation points.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "experiment": result["experiment"],
        "10_2m_is_ctx_relative_p99_alignment": result["control_independence_audit"]["10_2m_is_ctx_relative_p99_alignment"],
        "independent_horizontal_control_found": result["control_independence_audit"]["independent_horizontal_control_for_pinned_2025_dtm_found"],
        "challenge_ranking_state": result["challenge_selection"]["ranking_state"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
