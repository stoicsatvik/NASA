#!/usr/bin/env python3
"""E600A: nominal field-sample versus satellite-pixel support audit.

Inputs are taken from Levy (2026): approximately 500 mL per soil sample,
collected from the upper 10 cm; Landsat 8 OLI at 30 m/pixel and TIRS at
100 m/pixel. The area calculation assumes a uniform 10 cm slab solely to
produce a nominal equivalent footprint. It is not the observed sample
geometry, and it does not create georeferenced sample data.
"""
import json
from math import pi, sqrt

SAMPLE_VOLUME_ML = 500.0
SAMPLE_DEPTH_M = 0.10
OLI_RESOLUTION_M = 30.0
TIRS_RESOLUTION_M = 100.0
EARTH_DRY_TIU = (285.0, 694.0)
MARS_SANDY_ROCKY_TIU = (150.0, 350.0)

volume_m3 = SAMPLE_VOLUME_ML * 1e-6
nominal_sample_area_m2 = volume_m3 / SAMPLE_DEPTH_M
oli_pixel_area_m2 = OLI_RESOLUTION_M**2
tirs_pixel_area_m2 = TIRS_RESOLUTION_M**2
range_overlap = (
    max(EARTH_DRY_TIU[0], MARS_SANDY_ROCKY_TIU[0]),
    min(EARTH_DRY_TIU[1], MARS_SANDY_ROCKY_TIU[1]),
)
overlap_width = max(0.0, range_overlap[1] - range_overlap[0])
earth_range_width = EARTH_DRY_TIU[1] - EARTH_DRY_TIU[0]

result = {
    "experiment": "E600A",
    "date": "2026-11-13",
    "source_doi": "10.1080/15230430.2026.2617687",
    "inputs": {
        "sample_volume_ml_approx": SAMPLE_VOLUME_ML,
        "sample_depth_m_reported_upper_bound": SAMPLE_DEPTH_M,
        "oli_pixel_resolution_m": OLI_RESOLUTION_M,
        "tirs_pixel_resolution_m": TIRS_RESOLUTION_M,
        "earth_dry_physical_tiu_range": list(EARTH_DRY_TIU),
        "mars_sandy_rocky_literature_tiu_range": list(MARS_SANDY_ROCKY_TIU),
    },
    "derived_nominal_support": {
        "assumption": "500 mL represented as a uniform slab spanning exactly 0.10 m depth",
        "sample_area_m2": round(nominal_sample_area_m2, 9),
        "equivalent_square_side_cm": round(sqrt(nominal_sample_area_m2) * 100, 6),
        "equivalent_circle_diameter_cm": round(sqrt(4 * nominal_sample_area_m2 / pi) * 100, 6),
        "oli_pixel_area_m2": oli_pixel_area_m2,
        "tirs_pixel_area_m2": tirs_pixel_area_m2,
        "oli_pixel_to_nominal_sample_area_ratio": round(oli_pixel_area_m2 / nominal_sample_area_m2, 3),
        "tirs_pixel_to_nominal_sample_area_ratio": round(tirs_pixel_area_m2 / nominal_sample_area_m2, 3),
    },
    "range_overlap_only": {
        "earth_dry_tiu_intersection_with_mars_sandy_rocky": list(range_overlap),
        "overlap_width_tiu": overlap_width,
        "fraction_of_earth_dry_range_width": round(overlap_width / earth_range_width, 9),
        "warning": "Range overlap is not a distributional overlap, site match, or analogue score.",
    },
    "interpretation": (
        "Under the stated nominal slab assumption, one 100 m TIRS pixel covers "
        "2,000,000 times the sample-equivalent area; one 30 m OLI pixel covers "
        "180,000 times that area. This quantifies a severe nominal support mismatch, "
        "but the sample geometry is not known precisely and the ratio is not an "
        "observed sampling footprint. A point-sample ATI/TIU calibration is not "
        "admissible from these inputs."
    ),
    "admission": {
        "georeferenced_sample_rows_added": 0,
        "e001_run": False,
        "cross_body_similarity_claim": "NOT_YET_PROVEN",
    },
}

assert abs(nominal_sample_area_m2 - 0.005) < 1e-12
assert abs(tirs_pixel_area_m2 / nominal_sample_area_m2 - 2_000_000) < 1e-9
assert abs(oli_pixel_area_m2 / nominal_sample_area_m2 - 180_000) < 1e-9
assert range_overlap == (285.0, 350.0)
assert abs(overlap_width / earth_range_width - 0.15892420537897312) < 1e-12
assert result["admission"]["georeferenced_sample_rows_added"] == 0

if __name__ == "__main__":
    print(json.dumps(result, indent=2))
