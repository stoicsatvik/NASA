"""E226: cross-footprint Earth-site identity retrieval sanity check.

Uses 150 previously measured, overlapping SRTM-derived E221 windows.
Site identity is NOT an independent planetary analogue label.
"""
from __future__ import annotations
import argparse
import itertools
import json
import math
from collections import Counter
from pathlib import Path

SITES = ("ladakh_lead", "lonar_lead", "western_ghats_lead")
OFFSETS = (-0.5, -0.25, 0.0, 0.25, 0.5)
WINDOWS = (2.0, 4.0)
FEATURES = ("plane_detrended_relief_std_m", "slope_p90_dimensionless")
ABLATIONS = {"relief_only": (0,), "slope_only": (1,), "both": (0, 1)}
DEFAULT_INPUT = Path(__file__).parent / "results/e221_earth_geolocation_jitter_20261024.json"


def evaluate(source: dict) -> dict:
    if tuple(sorted(source["sources"])) != SITES:
        raise ValueError("Unexpected site set")
    keyed = {}
    for row in source["window_measurements"]:
        site = row["site"]
        window = float(row["window_km"])
        offset = (float(row["north_offset_km"]), float(row["east_offset_km"]))
        if site not in SITES or window not in WINDOWS or any(v not in OFFSETS for v in offset):
            raise ValueError("Unexpected site/window/offset")
        key = (site, window, offset)
        if key in keyed:
            raise ValueError("Duplicate measurement")
        vals = tuple(float(row["features"][f]) for f in FEATURES)
        if any(not math.isfinite(v) or v < 0 for v in vals):
            raise ValueError("Non-finite or negative feature")
        keyed[key] = vals
    expected = set(itertools.product(SITES, WINDOWS, itertools.product(OFFSETS, repeat=2)))
    if set(keyed) != expected:
        raise ValueError("Incomplete measurement grid")

    comparisons = {}
    for reference_window in WINDOWS:
        refs = [keyed[(s, reference_window, (0.0, 0.0))] for s in SITES]
        means = [sum(r[j] for r in refs) / len(refs) for j in range(2)]
        sds = [math.sqrt(sum((r[j] - means[j]) ** 2 for r in refs) / len(refs)) for j in range(2)]
        if any(sd == 0 for sd in sds):
            raise ValueError("Unidentifiable reference feature scale")
        for query_window in WINDOWS:
            queries = [(s, keyed[(s, query_window, offset)]) for s in SITES
                       for offset in itertools.product(OFFSETS, repeat=2)
                       if offset != (0.0, 0.0)]
            if len(queries) != 72:
                raise AssertionError("Center query leakage or missing observations")
            for label, active in ABLATIONS.items():
                confusion = Counter()
                winners = []
                for true_site, query in queries:
                    distances = [sum(((query[j] - ref[j]) / sds[j]) ** 2 for j in active)
                                 for ref in refs]
                    best = min(distances)
                    if sum(d == best for d in distances) != 1:
                        raise ValueError("Exact nearest-neighbor tie")
                    selected = distances.index(best)
                    winners.append(selected)
                    confusion[(true_site, SITES[selected])] += 1
                correct = sum(confusion[(s, s)] for s in SITES)
                permutations = [sum(1 for (s, _), w in zip(queries, winners)
                                    if SITES[perm[w]] == s)
                                for perm in itertools.permutations(range(len(SITES)))]
                if sum(permutations) != 2 * len(queries):
                    raise AssertionError("Invalid exact label-permutation accounting")
                key = f"query_{query_window:g}km__reference_{reference_window:g}km__{label}"
                comparisons[key] = {
                    "correct": correct,
                    "total": len(queries),
                    "accuracy": correct / len(queries),
                    "correct_by_site": {s: confusion[(s, s)] for s in SITES},
                    "confusion": {f"{a}->{b}": confusion[(a, b)] for a in SITES for b in SITES},
                    "exact_reference_label_permutation_correct": permutations,
                    "reference_only_feature_sd": {FEATURES[j]: sds[j] for j in active},
                }
    return {
        "experiment": "E226 exploratory cross-footprint Earth site-identity retrieval sanity gate",
        "source_experiment": source["experiment"],
        "source_git_blob_sha": "781266d3c61a20411e372c1f81c07dd96e51378e",
        "random_expected_correct": 24,
        "queries_per_case": 72,
        "reference_definition": "one zero-offset reference per site at selected footprint",
        "query_definition": "24 nonzero-offset overlapping windows per site",
        "scaling": "reference-only population standard deviation per feature",
        "limitations": [
            "Only three geographically distinct unvalidated research leads; site identity is not an analogue label.",
            "Overlapping windows are NOT independent observations or a blinded generalization test.",
            "Same-footprint comparisons share the source tile and center reference.",
            "Exact three-label permutations are sensitivity checks, NOT statistical significance tests.",
            "No lunar/Martian target, E001 recovery, or cross-body similarity measurement.",
            "Exploratory analysis after inspecting E221/E223; NOT preregistered.",
        ],
        "comparisons": comparisons,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate(json.loads(args.input.read_text(encoding="utf-8")))
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
