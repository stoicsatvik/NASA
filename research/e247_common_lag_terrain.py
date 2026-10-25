"""E247: 15-km physical-lag terrain contrast under sparse sample registration.

Earth-only two-site diagnostic, NOT planetary analogue recovery. At a fixed
30-km square support, compare height differences across half the footprint
in each axis. This is a *long-wavelength contrast* descriptor, NOT roughness.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from research.e243_earth_rank_phase_stress import (
    EXPECTED_SHA, GRIDS, PHASE_PAIRS, SITES_IN_ORDER, _compare, read_patch,
)
from research.e242_earth_sampling_aliasing import (
    WIDTH_KM, block_means, point_sample,
)
from research.e214_earth_dem_site_qc import source_url


def lag_contrast(z: np.ndarray) -> dict[str, float]:
    """RMS height differences across half the physical footprint in x/y.

    The input must cover the same 30-km square; its half-grid offsets then
    approximate 15-km physical lags. Valid even for 2x2, but sample count
    is tiny and must be reported rather than hidden.
    """
    a = np.asarray(z, dtype=float)
    if a.ndim != 2 or min(a.shape) < 2 or not np.isfinite(a).all():
        raise ValueError("Expected finite 2D elevation grid >=2x2")
    dy, dx = a.shape[0] // 2, a.shape[1] // 2
    horizontal = (a[:, dx:] - a[:, :-dx]).ravel()
    vertical = (a[dy:, :] - a[:-dy, :]).ravel()
    x = float(np.sqrt(np.mean(horizontal**2)))
    y = float(np.sqrt(np.mean(vertical**2)))
    both = float(np.sqrt((np.sum(horizontal**2) + np.sum(vertical**2)) /
                         (horizontal.size + vertical.size)))
    if not all(math.isfinite(v) for v in (x, y, both)):
        raise ValueError("Nonfinite contrast")
    return {
        "combined_rms_m": both, "east_west_rms_m": x,
        "north_south_rms_m": y,
        "horizontal_pairs": int(horizontal.size),
        "vertical_pairs": int(vertical.size),
        "lag_fraction_x": dx / a.shape[1],
        "lag_fraction_y": dy / a.shape[0],
    }


def audit(a: np.ndarray, b: np.ndarray) -> dict:
    arrays = [np.asarray(a, dtype=float), np.asarray(b, dtype=float)]
    if any(x.ndim != 2 or min(x.shape) < 32 or not np.isfinite(x).all()
           for x in arrays):
        raise ValueError("Expected finite >=32x32 source patches")
    dense = [lag_contrast(x) for x in arrays]
    metrics = ("combined_rms_m", "east_west_rms_m", "north_south_rms_m")
    out = {}
    for metric in metrics:
        reference = [d[metric] for d in dense]
        if math.isclose(reference[0], reference[1], rel_tol=1e-12, abs_tol=1e-9):
            raise ValueError("Tied dense site ranking; no post-hoc tie break")
        sign = 1 if reference[0] > reference[1] else -1
        by_grid = {}
        for n in GRIDS:
            vals = [[lag_contrast(point_sample(x, n, py, px))[metric]
                     for py, px in PHASE_PAIRS] for x in arrays]
            counts = {"same": 0, "reversed": 0, "tie": 0}
            for u in vals[0]:
                for v in vals[1]:
                    counts[_compare(u, v, sign)] += 1
            if sum(counts.values()) != 256:
                raise AssertionError("Incomplete independent phase enumeration")
            coarse = [lag_contrast(block_means(x, n))[metric] for x in arrays]
            by_grid[str(n)] = {
                "independent_phase_counts": counts,
                "independent_phase_scenarios": 256,
                "block_mean_values_m": coarse,
                "block_mean_rank": _compare(*coarse, sign),
                "point_phase_range_m": [
                    {"min": float(min(v)), "median": float(np.median(v)),
                     "max": float(max(v))} for v in vals
                ],
                "horizontal_pairs_per_phase": n * (n - n//2),
                "vertical_pairs_per_phase": n * (n - n//2),
                "nominal_lag_km": WIDTH_KM / 2,
            }
        out[metric] = {
            "dense_values_m": reference,
            "dense_reference_higher": SITES_IN_ORDER[0] if sign > 0 else SITES_IN_ORDER[1],
            "grid_results": by_grid,
        }
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ghats", required=True, type=Path)
    p.add_argument("--ladakh", required=True, type=Path)
    args = p.parse_args()
    arrays = [read_patch(args.ghats, SITES_IN_ORDER[0]),
              read_patch(args.ladakh, SITES_IN_ORDER[1])]
    print(json.dumps({
        "experiment": "E247 real Earth common physical-lag terrain contrast",
        "sources": {s: source_url(s) for s in SITES_IN_ORDER},
        "source_sha256": EXPECTED_SHA,
        "physical_support_km": WIDTH_KM,
        "nominal_lag_km": WIDTH_KM / 2,
        "source_patch_shapes": [list(x.shape) for x in arrays],
        "dense_pair_counts": [lag_contrast(x) for x in arrays],
        "metrics": audit(*arrays),
        "claim_state": "EARTH LONG-WAVELENGTH CONTRAST ONLY; E001 NOT YET MEASURED; CROSS-BODY SIMILARITY NOT YET PROVEN",
        "limitations": [
            "Two unvalidated Earth leads; no geological analogue positive or negative labels.",
            "Long-wavelength height contrast includes broad-scale slope; NOT a roughness proxy.",
            "2x2 uses only four horizontal/vertical pairs; registration scenarios are not probabilities.",
            "Point samples and block means do not reproduce LOLA/MOLA instrument responses.",
            "Dense/low-resolution lag is approximate: finite grid spacing and sample registration vary.",
            "No lunar/Martian analogue recovery, novel discovery or field validation.",
        ],
    }, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
