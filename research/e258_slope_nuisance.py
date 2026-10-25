"""E258: falsify slope invariance of E247's stable 15-km terrain contrast.

Two fingerprinted real Earth DEM windows with SYNTHETIC additive planar tilt.
This is a descriptor nuisance audit, not a model of LOLA/MOLA errors or E001.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from research.e242_earth_sampling_aliasing import WIDTH_KM, point_sample, plane_detrended_std
from research.e243_earth_rank_phase_stress import EXPECTED_SHA, GRIDS, PHASE_PAIRS, SITES_IN_ORDER, _compare, read_patch
from research.e247_common_lag_terrain import lag_contrast
from research.e214_earth_dem_site_qc import source_url

SLOPES_M_PER_KM = (2.0, 5.0, 10.0, 20.0, 40.0, 80.0)
DIRECTIONS = {"east": (1, 0), "west": (-1, 0), "north": (0, 1), "south": (0, -1)}
METRIC = "combined_rms_m"


def planar_tilt(z: np.ndarray, east_m_per_km: float, north_m_per_km: float) -> np.ndarray:
    """Add a plane in physical km, preserving vertical units in metres."""
    a = np.asarray(z, dtype=float)
    if a.ndim != 2 or min(a.shape) < 2 or not np.isfinite(a).all():
        raise ValueError("Expected finite 2D terrain grid")
    if not all(math.isfinite(v) for v in (east_m_per_km, north_m_per_km)):
        raise ValueError("Nonfinite tilt")
    y = ((np.arange(a.shape[0]) + 0.5) / a.shape[0] - 0.5) * WIDTH_KM
    x = ((np.arange(a.shape[1]) + 0.5) / a.shape[1] - 0.5) * WIDTH_KM
    return a + north_m_per_km * y[:, None] + east_m_per_km * x[None, :]


def audit(a: np.ndarray, b: np.ndarray) -> dict:
    sources = [np.asarray(a, dtype=float), np.asarray(b, dtype=float)]
    if any(z.ndim != 2 or min(z.shape) < 32 or not np.isfinite(z).all() for z in sources):
        raise ValueError("Expected two complete >=32x32 terrain windows")
    dense = [lag_contrast(z)[METRIC] for z in sources]
    if math.isclose(dense[0], dense[1], rel_tol=1e-12, abs_tol=1e-9):
        raise ValueError("Dense ranking tied")
    ref_sign = 1 if dense[0] > dense[1] else -1
    phase_baseline = {
        n: [[lag_contrast(point_sample(z, n, py, px))[METRIC] for py, px in PHASE_PAIRS]
            for z in sources] for n in GRIDS
    }
    results = []
    for target in (0, 1):
        for slope in SLOPES_M_PER_KM:
            for direction, (east, north) in DIRECTIONS.items():
                tilted = planar_tilt(sources[target], slope * east, slope * north)
                dense_values = dense.copy()
                dense_values[target] = lag_contrast(tilted)[METRIC]
                residual_change = abs(plane_detrended_std(tilted) -
                                      plane_detrended_std(sources[target]))
                by_grid = {}
                for n in GRIDS:
                    phase_values = [
                        lag_contrast(point_sample(tilted, n, py, px))[METRIC]
                        for py, px in PHASE_PAIRS
                    ]
                    unmodified = phase_baseline[n][1 - target]
                    counts = {"same": 0, "reversed": 0, "tie": 0}
                    for u in phase_values:
                        for v in unmodified:
                            left, right = (u, v) if target == 0 else (v, u)
                            counts[_compare(left, right, ref_sign)] += 1
                    if sum(counts.values()) != 256:
                        raise AssertionError("Incomplete phase stress")
                    by_grid[str(n)] = counts
                results.append({
                    "perturbed_site": SITES_IN_ORDER[target],
                    "slope_m_per_km": slope,
                    "direction": direction,
                    "dense_values_m": dense_values,
                    "dense_rank_vs_original": _compare(*dense_values, ref_sign),
                    "detrended_relief_change_m": residual_change,
                    "grid_rank_vs_original_dense": by_grid,
                })
    baseline = {}
    for n, vals in phase_baseline.items():
        counts = {"same": 0, "reversed": 0, "tie": 0}
        for u in vals[0]:
            for v in vals[1]:
                counts[_compare(u, v, ref_sign)] += 1
        baseline[str(n)] = counts
    return {
        "dense_unperturbed_values_m": dense,
        "dense_reference_higher": SITES_IN_ORDER[0] if ref_sign > 0 else SITES_IN_ORDER[1],
        "unperturbed_phase_counts": baseline,
        "synthetic_tilt_scenarios": results,
        "scenario_count": len(results),
        "dense_reversal_count": sum(r["dense_rank_vs_original"] == "reversed" for r in results),
        "per_grid_any_reversal_count": {
            str(n): sum(r["grid_rank_vs_original_dense"][str(n)]["reversed"] > 0
                        for r in results) for n in GRIDS
        },
        "max_planar_residual_change_m": max(r["detrended_relief_change_m"] for r in results),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ghats", required=True, type=Path)
    parser.add_argument("--ladakh", required=True, type=Path)
    args = parser.parse_args()
    arrays = [read_patch(args.ghats, SITES_IN_ORDER[0]),
              read_patch(args.ladakh, SITES_IN_ORDER[1])]
    result = {
        "experiment": "E258 real Earth descriptor sensitivity to synthetic planar tilt",
        "source_sha256": EXPECTED_SHA,
        "sources": {site: source_url(site) for site in SITES_IN_ORDER},
        "physical_support_km": WIDTH_KM,
        "slope_m_per_km_grid": SLOPES_M_PER_KM,
        "directions": list(DIRECTIONS),
        "descriptor": "15-km-lag combined RMS height difference, slope-sensitive",
        "audit": audit(*arrays),
        "claim": "EARTH DESCRIPTOR SLOPE-NUISANCE AUDIT ONLY; E001 NOT YET MEASURED; CROSS-BODY SIMILARITY NOT YET PROVEN",
        "limitations": [
            "Additive tilt is a synthetic controlled transformation, NOT instrument noise or a geological measurement.",
            "Only two unvalidated Earth research leads, not positive/negative planetary analogue labels.",
            "Independent phase combinations are deterministic scenarios, NOT probabilities.",
            "No actual LOLA/MOLA point-spread functions, projection harmonization or Moon/Mars matching.",
            "No field validation, new analogue discovery, or competition solution.",
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
