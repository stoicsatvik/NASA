"""E001 leakage-resistant leave-one-site-out ranking baseline.

Input CSV columns: site_id, family, is_analog (0/1), and numeric feature columns.
The withheld site is never used to estimate scaling or reference centroids.
This is an evaluation harness, not evidence that any site is an analog.
"""
import argparse
import csv
import json
import math
import random
from pathlib import Path


def load(path, features):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows or len({r["site_id"] for r in rows}) != len(rows):
        raise ValueError("Need nonempty CSV with unique site_id")
    for r in rows:
        if r["is_analog"] not in ("0", "1"):
            raise ValueError("is_analog must be 0 or 1")
        for feature in features:
            value = float(r[feature])
            if not math.isfinite(value):
                raise ValueError("Nonfinite feature: " + feature)
            r[feature] = value
    return rows


def rank_fold(rows, features, withheld, candidate_policy="all_nonreference"):
    """Evaluate against a declared universe. The legacy negatives-only policy is diagnostic only."""
    if candidate_policy not in ("all_nonreference", "legacy_negatives_only"):
        raise ValueError("Unknown candidate_policy")
    train = [r for r in rows if r["site_id"] != withheld["site_id"]]
    refs = [r for r in train if r["is_analog"] == "1" and r["family"] == withheld["family"]]
    controls = [r for r in train if r["is_analog"] == "0"]
    if not refs or not controls:
        raise ValueError("Each fold needs another same-family positive and a negative control")
    means = {f: sum(r[f] for r in train) / len(train) for f in features}
    scales = {f: math.sqrt(sum((r[f] - means[f]) ** 2 for r in train) / len(train)) for f in features}
    scales = {f: (s if s > 1e-12 else 1.0) for f, s in scales.items()}
    center = {f: sum((r[f] - means[f]) / scales[f] for r in refs) / len(refs) for f in features}
    def dist(row):
        return math.sqrt(sum(((row[f] - means[f]) / scales[f] - center[f]) ** 2 for f in features))
    # Same-family reference positives are excluded because they define the query centroid.
    # All remaining sites compete, regardless of their analog label or planetary family.
    candidates = ([r for r in train if r["site_id"] not in {x["site_id"] for x in refs}] + [withheld]
                  if candidate_policy == "all_nonreference" else controls + [withheld])
    ranked = sorted(candidates, key=lambda r: (dist(r), r["site_id"]))
    position = next(i + 1 for i, r in enumerate(ranked) if r["site_id"] == withheld["site_id"])
    return {"site_id": withheld["site_id"], "family": withheld["family"], "rank": position,
            "candidates": len(candidates), "top_1": position == 1,
            "percentile": 1 - (position - 1) / max(1, len(candidates) - 1),
            "candidate_policy": candidate_policy}


def evaluate(rows, features, candidate_policy="all_nonreference"):
    positives = [r for r in rows if r["is_analog"] == "1"]
    if not positives:
        raise ValueError("No positive analog sites")
    folds = [rank_fold(rows, features, r, candidate_policy=candidate_policy) for r in positives]
    return {"features": features, "candidate_policy": candidate_policy, "folds": folds,
            "top_1_rate": sum(r["top_1"] for r in folds) / len(folds),
            "mean_percentile": sum(r["percentile"] for r in folds) / len(folds),
            "random_expected_top_1": sum(1 / r["candidates"] for r in folds) / len(folds)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--features", required=True, help="Comma-separated numeric columns")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--candidate-policy", choices=("all_nonreference", "legacy_negatives_only"), default="all_nonreference")
    args = parser.parse_args()
    features = [f.strip() for f in args.features.split(",") if f.strip()]
    if not features or len(set(features)) != len(features):
        parser.error("Provide distinct features")
    rows = load(args.csv_path, features)
    result = evaluate(rows, features, candidate_policy=args.candidate_policy)
    result["ablations"] = {f: evaluate(rows, [x for x in features if x != f], candidate_policy=args.candidate_policy)
                           for f in features} if len(features) > 1 else {}
    output = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
