"""E458: nominal pixel-support sensitivity for official LOLA/MOLA catalog products.

Catalog metadata only. No high-resolution raster bytes or analogue labels are used.
Pixel spacing is not independent measured terrain resolution.
"""
from __future__ import annotations

import json
import math

RADII_KM = {"moon": 1737.4, "mars": 3396.19}
PRODUCT_PPD = (4, 16, 64, 128)
WINDOWS_KM = (2.0, 4.0)
SOURCE_URLS = {
    "moon": "https://ode.rsl.wustl.edu/MArs/pagehelp/Content/Missions_Instruments/Lunar%20Reconnaissance%20Orbiter%20%28LRO%29/LOLA/GDR/GDRDEM.htm",
    "mars": "https://pds-geosciences.wustl.edu/missions/mgs/megdr.html",
}


def pixel_spacing_km(body: str, ppd: int) -> float:
    if body not in RADII_KM or type(ppd) is not int or ppd not in PRODUCT_PPD:
        raise ValueError("unrecognized body or product resolution")
    return 2.0 * math.pi * RADII_KM[body] / (360.0 * ppd)


def evaluate(threshold: float = 4.0) -> dict:
    if not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or threshold <= 0:
        raise ValueError("threshold must be finite and positive")
    rows = []
    for width in WINDOWS_KM:
        for body in ("moon", "mars"):
            for ppd in PRODUCT_PPD:
                spacing = pixel_spacing_km(body, ppd)
                spans = width / spacing
                rows.append({
                    "window_km": width, "body": body, "pixels_per_degree": ppd,
                    "nominal_equatorial_pixel_spacing_km": spacing,
                    "nominal_pixel_spans": spans,
                    "passes_nominal_threshold": spans >= threshold,
                    "measured_site_coverage": None,
                    "effective_spatial_resolution_km": None,
                })
    paired = {}
    for width in WINDOWS_KM:
        paired[str(int(width))] = [ppd for ppd in PRODUCT_PPD if all(
            next(r for r in rows if r["window_km"] == width and r["body"] == body and r["pixels_per_degree"] == ppd)["passes_nominal_threshold"]
            for body in ("moon", "mars")
        )]
    return {
        "experiment": "E458", "evidence_type": "official_catalog_metadata_only",
        "nominal_threshold_pixel_spans": float(threshold),
        "body_radius_km": RADII_KM, "source_urls": SOURCE_URLS,
        "rows": rows, "paired_same_ppd_pass": paired,
        "known_analogue_recovery": "NOT YET MEASURED",
        "cross_body_similarity": "NOT YET PROVEN",
        "site_coverage_and_effective_resolution": "NOT YET MEASURED",
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, sort_keys=True, allow_nan=False))
