"""E223: exact independent-site versus common-offset terrain rank sensitivity.

Reads E221's real SRTM-derived window measurements. No new field or sensor
measurements are inferred. Fractions describe finite combinatorial scenarios,
NOT empirical probabilities or independent statistical replicates.
"""
from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter
from pathlib import Path

FEATURES = ("plane_detrended_relief_std_m", "slope_p90_dimensionless")
WINDOWS = (2.0, 4.0)
OFFSETS = (-0.5, -0.25, 0.0, 0.25, 0.5)
EXPECTED_SITES = ("ladakh_lead", "lonar_lead", "western_ghats_lead")
DEFAULT_INPUT = Path(__file__).parent / "results/e221_earth_geolocation_jitter_20261024.json"


def _ordering(sites: tuple[str, ...], values: tuple[float, ...]) -> str:
    if len(set(values)) != len(values):
        raise ValueError("Rank tie: predeclare tie handling before interpreting")
    return ">".join(sites[i] for i in sorted(range(len(sites)), key=lambda i: -values[i]))


def evaluate(source: dict) -> dict:
    """Enumerate all 25^3 independent jitter combinations exactly per metric."""
    sites = tuple(sorted(source["sources"]))
    if sites != EXPECTED_SITES:
        raise ValueError(f"Unexpected sites: {sites!r}")
    rows = source["window_measurements"]
    if len(rows) != 150:
        raise ValueError(f"Expected 150 E221 observations, got {len(rows)}")
    results = {}
    for window in WINDOWS:
        keyed = {}
        for row in rows:
            if row["window_km"] != window:
                continue
            site = row["site"]
            offset = (row["north_offset_km"], row["east_offset_km"])
            if site not in sites or offset in keyed.setdefault(site, {}):
                raise ValueError("Unexpected site or duplicate offset")
            if offset[0] not in OFFSETS or offset[1] not in OFFSETS:
                raise ValueError("Offset outside preregistered grid")
            keyed[site][offset] = row["features"]
        expected_grid = set(itertools.product(OFFSETS, repeat=2))
        if set(keyed) != set(sites) or any(set(keyed[s]) != expected_grid for s in sites):
            raise ValueError("Missing or unexpected site-offset observations")
        offsets = sorted(expected_grid)
        for feature in FEATURES:
            by_site = [
                [float(keyed[s][offset][feature]) for offset in offsets]
                for s in sites
            ]
            if any(not all(__import__("math").isfinite(v) for v in vs) for vs in by_site):
                raise ValueError("Non-finite measurement")
            center_idx = offsets.index((0.0, 0.0))
            center = _ordering(sites, tuple(vs[center_idx] for vs in by_site))
            synchronous = Counter(
                _ordering(sites, tuple(vs[i] for vs in by_site))
                for i in range(len(offsets))
            )
            independent = Counter()
            top = Counter()
            for indices in itertools.product(range(len(offsets)), repeat=len(sites)):
                order = _ordering(sites, tuple(by_site[i][j] for i, j in enumerate(indices)))
                independent[order] += 1
                top[order.split(">")[0]] += 1
            total = len(offsets) ** len(sites)
            key = f"{window:g}km/{feature}"
            results[key] = {
                "center_order": center,
                "independent_combinations": total,
                "independent_order_counts": dict(sorted(independent.items())),
                "independent_center_order_fraction": independent[center] / total,
                "independent_top_fractions": {s: top[s] / total for s in sites},
                "synchronized_order_counts": dict(sorted(synchronous.items())),
                "synchronized_center_order_fraction": synchronous[center] / len(offsets),
            }
    return {
        "experiment": "E223 independent versus synchronized site-jitter exact rank audit",
        "source_experiment": source["experiment"],
        "source_git_blob_sha": "781266d3c61a20411e372c1f81c07dd96e51378e",
        "sites": list(sites),
        "limitations": [
            "All input windows are real SRTM-derived measurements from E221, not independent field validation.",
            "The 25 offset values per site overlap spatially and are NOT independent replicates.",
            "Independent-site combinations are a mathematical scenario stress test, not empirical probabilities.",
            "Uniform weighting over offsets is an analyst assumption, not a measured location-error distribution.",
            "Research-lead coordinates are not independently established planetary analogue labels.",
            "No cross-body site recovery or E001 evaluation is performed.",
        ],
        "comparisons": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    result = evaluate(source)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
