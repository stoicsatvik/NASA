"""E340: arithmetic-only, source-frozen Ibex/Gale morphometry audit.

Independent literature check, NOT a site-recovery model or Space Apps solution.
"""
from __future__ import annotations

import json
from decimal import Decimal

SOURCE = "https://ntrs.nasa.gov/citations/20260000452"
PDF = "https://ntrs.nasa.gov/api/citations/20260000452/downloads/Bretzfelder_IbexDunes_finalsubmit_Jan142026.pdf"
DOI = "10.1016/j.aeolia.2026.101032"

# Bretzfelder et al. (2026), accepted manuscript, section 4.1.3.
# Earth LiDAR measurement tolerance is in section 3.5; not a CI for the mean.
EARTH_MEAN_WAVELENGTH_M = Decimal("0.71")
MARS_MEAN_WAVELENGTH_M = Decimal("2.20")
EARTH_LIDAR_MEASUREMENT_TOLERANCE_M = Decimal("0.02")


def evaluate() -> dict:
    earth = EARTH_MEAN_WAVELENGTH_M
    mars = MARS_MEAN_WAVELENGTH_M
    tolerance = EARTH_LIDAR_MEASUREMENT_TOLERANCE_M
    if not (earth > tolerance >= 0 and mars > 0):
        raise ValueError("source measurements must be positive and Earth interval nonempty")
    low, high = earth - tolerance, earth + tolerance
    return {
        "experiment": "E340 literature-only morphometry mismatch audit",
        "source": {
            "ntrs": SOURCE,
            "pdf": PDF,
            "doi": DOI,
            "measurement_sections": {
                "earth_lidar_precision": "3.5",
                "mars_navcam_case_studies": "3.6",
                "paired_mean_wavelengths": "4.1.3",
            },
            "mars_rover_sols": [706, 1788],
        },
        "inputs": {
            "earth_ibex_reported_mean_wavelength_m": str(earth),
            "mars_gale_reported_mean_wavelength_m": str(mars),
            "earth_lidar_individual_measurement_tolerance_m": str(tolerance),
            "mars_mean_uncertainty_m": None,
            "earth_samples_per_field_reported_range": [3, 32],
            "mars_examples": 2,
        },
        "derived": {
            "mars_minus_earth_mean_m": str(mars - earth),
            "mars_to_earth_mean_wavelength_ratio": str(mars / earth),
            "ratio_if_earth_mean_shifted_by_lidar_tolerance": {
                "lower": str(mars / high),
                "upper": str(mars / low),
            },
        },
        "interpretation": [
            "Published morphologic analogue examples differ substantially in raw mean wavelength.",
            "The ratio interval is conditional on the reported Mars point estimate and is NOT a confidence interval.",
            "Published source describes comparable ripple heights, not wavelength equality.",
            "Mars image-derived examples are single bedforms, Earth field means pool 3-32 measurements; not independent matched site labels.",
            "No cross-body similarity model, recovery benchmark, new field observation, or contest solution was run.",
        ],
        "claim_state": {
            "raw_wavelength_equality": "REJECTED for these source-reported exemplar means",
            "physically_generalizable_analogue_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
        },
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, sort_keys=True))
