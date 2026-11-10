"""E001 synthetic spatial-scale sensitivity using the production evaluator.

Run: python -m experiments.e001_spatial_scale_sensitivity
No real planetary samples; not a calibrated spatial inference procedure.
"""
from itertools import combinations
from experiments.e001_baseline import evaluate
from experiments.e001_exact_label_null import exact_label_null


def probe(block_gap, within_pair_offset):
    if block_gap <= 0 or within_pair_offset <= 0:
        raise ValueError("Both distances must be positive")
    rows = [
        {"site_id": f"pair_{b}_{m}", "family": "Mars",
         "x": block_gap * b + within_pair_offset * m,
         "is_analog": "1" if b in (0, 1) else "0"}
        for b in range(4) for m in range(2)
    ]
    observed = evaluate(rows, ["x"])["top_1_rate"]
    unrestricted = exact_label_null(rows, ["x"], max_assignments=100)
    blocked_scores = []
    for chosen in combinations(range(4), 2):
        chosen = set(chosen)
        reassigned = [
            dict(r, is_analog="1" if int(r["site_id"].split("_")[1]) in chosen else "0")
            for r in rows
        ]
        blocked_scores.append(evaluate(reassigned, ["x"])["top_1_rate"])
    return {
        "gap": block_gap, "offset": within_pair_offset,
        "offset_to_gap": within_pair_offset / block_gap,
        "observed_top_1": observed,
        "unrestricted_p": unrestricted["one_sided_p"],
        "blocked_p": sum(s >= observed for s in blocked_scores) / len(blocked_scores),
        "unrestricted_n": unrestricted["exact_null_assignments"],
        "blocked_n": len(blocked_scores),
    }


def run():
    results = [probe(gap, offset)
               for gap in (0.03, 0.1, 1.0, 10.0, 100.0)
               for offset in (0.001, 0.02, 0.1, 1.0)]
    assert len(results) == 20
    assert all(r["unrestricted_n"] == 70 and r["blocked_n"] == 6 for r in results)
    # Reproduce the original E001 production spatial-null fixture.
    original = probe(10.0, 0.02)
    assert original["observed_top_1"] == 1.0
    assert abs(original["unrestricted_p"] - 3 / 70) < 1e-12
    assert abs(original["blocked_p"] - 3 / 6) < 1e-12
    # A near-overlapping-pair geometry destroys the apparent recovery signal.
    collapse = probe(0.03, 0.1)
    assert collapse["observed_top_1"] == 0.0
    assert collapse["unrestricted_p"] == collapse["blocked_p"] == 1.0
    # Under this particular grid, no block-preserving null reaches p < 0.05.
    assert all(r["blocked_p"] >= 0.05 for r in results)
    return results


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2, sort_keys=True))
