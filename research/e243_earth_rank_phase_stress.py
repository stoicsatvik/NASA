"""E243: exact two-site rank sensitivity to independent sample registration.

Uses E242's two public SRTM-derived Earth tiles. This is a deterministic
finite-scenario stress test, NOT empirical probabilities, independent samples,
or Moon/Mars analogue recovery. No new geological labels are inferred.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import from_bounds

from research.e214_earth_dem_site_qc import SITES, source_url
from research.e242_earth_sampling_aliasing import (
    PHASES, WIDTH_KM, block_means, footprint_bounds,
    plane_detrended_std, point_sample, sha256,
)

EXPECTED_SHA = {
    "western_ghats_lead": "73523b876c229607f421c529b8c91a5ed7dd9b504ba413064b5ab0fcb193361b",
    "ladakh_lead": "9179642ad2f9ccd90266229b9e9d7c49044bda661ec731d0068879dd607f2c7c",
}
SITES_IN_ORDER = ("western_ghats_lead", "ladakh_lead")
GRIDS = (2, 4, 8, 16)
PHASE_PAIRS = tuple(itertools.product(PHASES, repeat=2))


def read_patch(path: Path, site: str) -> np.ndarray:
    """Fail closed on source drift, missing pixels, wrong CRS or crossed tiles."""
    if site not in EXPECTED_SHA or sha256(path) != EXPECTED_SHA[site]:
        raise ValueError("Unexpected site or source SHA-256; inspect source drift")
    lat, lon = SITES[site]
    bounds = footprint_bounds(lat, lon, WIDTH_KM)
    with rasterio.open(path) as ds:
        if ds.count != 1 or ds.crs is None or ds.crs.to_epsg() != 4326:
            raise ValueError("Expected single-band EPSG:4326 elevation raster")
        if not (ds.bounds.left <= bounds[0] < bounds[2] <= ds.bounds.right
                and ds.bounds.bottom <= bounds[1] < bounds[3] <= ds.bounds.top):
            raise ValueError("30-km patch crosses source tile")
        window = from_bounds(*bounds, transform=ds.transform).round_offsets().round_lengths()
        masked = ds.read(1, window=window, masked=True)
        z = np.asarray(masked.data, dtype=float)
        valid = ~np.ma.getmaskarray(masked)
        if ds.nodata is not None:
            valid &= z != ds.nodata
        if min(z.shape) < 32 or not valid.all() or not np.isfinite(z).all():
            raise ValueError("Invalid or incomplete elevation patch")
        return z


def checkerboard_mode_2x2(z: np.ndarray) -> float:
    """Exact planar-residual SD for a 2x2 array: |a-b-c+d|/4."""
    a = np.asarray(z, dtype=float)
    if a.shape != (2, 2) or not np.isfinite(a).all():
        raise ValueError("Expected finite 2x2 grid")
    return abs(float(a[0, 0] - a[0, 1] - a[1, 0] + a[1, 1])) / 4


def _compare(a: float, b: float, reference_sign: int) -> str:
    if not all(math.isfinite(v) for v in (a, b)) or reference_sign not in (-1, 1):
        raise ValueError("Invalid rank comparison")
    if math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-9):
        return "tie"
    return "same" if (1 if a > b else -1) == reference_sign else "reversed"


def rank_audit(a: np.ndarray, b: np.ndarray) -> dict:
    """Exhaustive phase cross-product. Scenario fractions are not probabilities."""
    arrays = (np.asarray(a, dtype=float), np.asarray(b, dtype=float))
    if any(x.ndim != 2 or min(x.shape) < 32 or not np.isfinite(x).all() for x in arrays):
        raise ValueError("Expected finite >=32x32 Earth patches")
    metrics = {
        "plane_detrended_relief_sd_m": plane_detrended_std,
        "raw_elevation_range_m": lambda x: float(np.ptp(x)),
    }
    output = {}
    for metric_name, metric in metrics.items():
        dense = [metric(x) for x in arrays]
        if math.isclose(dense[0], dense[1], rel_tol=1e-12, abs_tol=1e-9):
            raise ValueError("Dense reference tied; preregister tie policy")
        ref_sign = 1 if dense[0] > dense[1] else -1
        results = {}
        for n in GRIDS:
            sampled = [
                [metric(point_sample(x, n, py, px)) for py, px in PHASE_PAIRS]
                for x in arrays
            ]
            paired = {"same": 0, "reversed": 0, "tie": 0}
            independent = {"same": 0, "reversed": 0, "tie": 0}
            for i in range(len(PHASE_PAIRS)):
                paired[_compare(sampled[0][i], sampled[1][i], ref_sign)] += 1
            for x in sampled[0]:
                for y in sampled[1]:
                    independent[_compare(x, y, ref_sign)] += 1
            if sum(paired.values()) != 16 or sum(independent.values()) != 256:
                raise AssertionError("Incomplete exact phase enumeration")
            coarse = [metric(block_means(x, n)) for x in arrays]
            results[str(n)] = {
                "grid": [n, n],
                "matched_phase_counts": paired,
                "independent_phase_counts": independent,
                "matched_phase_scenarios": 16,
                "independent_phase_scenarios": 256,
                "block_mean_rank": _compare(coarse[0], coarse[1], ref_sign),
                "block_mean_values_m": coarse,
                "phase_range_m": [
                    {"min": min(v), "median": float(np.median(v)), "max": max(v)}
                    for v in sampled
                ],
            }
        output[metric_name] = {
            "dense_values_m": dense,
            "dense_reference_higher": SITES_IN_ORDER[0] if ref_sign > 0 else SITES_IN_ORDER[1],
            "grid_results": results,
        }
    return output


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ghats", required=True, type=Path)
    p.add_argument("--ladakh", required=True, type=Path)
    args = p.parse_args()
    arrays = [read_patch(args.ghats, SITES_IN_ORDER[0]),
              read_patch(args.ladakh, SITES_IN_ORDER[1])]
    result = {
        "experiment": "E243 exact Earth terrain rank sensitivity to independent registration",
        "source_experiment": "E242",
        "source_sha256": EXPECTED_SHA,
        "sources": {s: source_url(s) for s in SITES_IN_ORDER},
        "sites": list(SITES_IN_ORDER),
        "patch_shapes": [list(x.shape) for x in arrays],
        "physical_support_km": WIDTH_KM,
        "metrics": rank_audit(*arrays),
        "claim_state": "EARTH RANK STRESS ONLY; E001 NOT YET MEASURED; CROSS-BODY SIMILARITY NOT YET PROVEN",
        "limitations": [
            "The two sites are unvalidated research leads, not geological analogue labels.",
            "Independent phase cross-products are deterministic scenarios, not observed probabilities.",
            "Both patches are overlapping derived SRTM/Skadi data, not independent sensors.",
            "Raw elevation range includes broad-scale slope and is NOT interchangeable with detrended roughness.",
            "A 2x2 planar residual has one degree of freedom and equals one checkerboard contrast.",
            "No actual LOLA/MOLA instrument point-spread function or lunar/Martian matching is modeled.",
            "No E001 known-site recovery, novel analogue discovery or local validation was performed.",
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
