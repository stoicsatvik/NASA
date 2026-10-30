"""E430: support-change self-retrieval on E214 real Earth DEM summary only.

This is a negative control for descriptor stability, NOT E001 or analogue recovery.
Run: python research/e430_earth_support_self_retrieval.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

SOURCE = Path(__file__).parent / "results/e214_earth_skadi_real_data_20261024.json"
FEATURES = (
    "plane_detrended_relief_std_m",
    "slope_p50_dimensionless",
    "slope_p90_dimensionless",
    "elevation_range_m",
)
SITES = ("lonar_lead", "western_ghats_lead", "ladakh_lead")


def load_pairs(path: Path = SOURCE):
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not str(raw.get("experiment", "")).startswith("E214 real Earth"):
        raise ValueError("Unexpected provenance: E214 source required")
    rows = raw["sites"]
    if len(rows) != 6:
        raise ValueError("Expected exactly six E214 site-window records")
    indexed = {}
    for row in rows:
        key = (row["site"], row["physical_window_km"])
        if key in indexed or key[0] not in SITES or key[1] not in (2, 4):
            raise ValueError("Duplicate or unexpected site/support")
        values = tuple(float(row["metrics"][f]) for f in FEATURES)
        if any(not math.isfinite(v) or v <= 0 for v in values):
            raise ValueError("All four source features must be positive finite")
        indexed[key] = values
    if set(indexed) != {(s, km) for s in SITES for km in (2, 4)}:
        raise ValueError("Incomplete site/support coverage")
    return indexed


def retrieval(indexed, mode="pooled_z", omit=None):
    if mode not in ("pooled_z", "log_ratio"):
        raise ValueError("Unsupported frozen distance")
    if omit is not None and omit not in FEATURES:
        raise ValueError("Unknown ablation feature")
    dims = [i for i, f in enumerate(FEATURES) if f != omit]
    pool = list(indexed.values())
    std = {}
    for i in dims:
        mean = sum(x[i] for x in pool) / len(pool)
        sigma = math.sqrt(sum((x[i] - mean) ** 2 for x in pool) / len(pool))
        if sigma <= 0:
            raise ValueError("Zero-variance descriptor")
        std[i] = sigma
    out = []
    for site in SITES:
        query = indexed[(site, 2)]
        scores = []
        for candidate in SITES:
            target = indexed[(candidate, 4)]
            distance = math.sqrt(sum(
                (math.log(query[i] / target[i]) if mode == "log_ratio"
                 else (query[i] - target[i]) / std[i]) ** 2
                for i in dims
            ))
            scores.append((distance, candidate))
        scores.sort(key=lambda x: (x[0], x[1]))
        out.append({
            "query": site,
            "nearest": scores[0][1],
            "same_site": scores[0][1] == site,
            "ranked": [{"site": name, "distance": round(d, 8)} for d, name in scores],
        })
    return {"top1": sum(r["same_site"] for r in out), "n": len(out), "rows": out}


def main():
    pairs = load_pairs()
    results = {}
    for mode in ("pooled_z", "log_ratio"):
        results[mode] = {
            "all_features": retrieval(pairs, mode),
            "ablations": {f: retrieval(pairs, mode, f) for f in FEATURES},
        }
    print(json.dumps({
        "experiment": "E430",
        "source": str(SOURCE),
        "claim": "EARTH SUPPORT STABILITY ONLY; E001 NOT YET MEASURED",
        "results": results,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
