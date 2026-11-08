"""Adversarial spatial-block null for the *production* E001 top-1 statistic.

Synthetic diagnostic only. Four close site-pairs separated by large distances.
Two entire pairs are positive; no real planetary sites or measurements.
Run from repository root:
    python -m experiments.e001_production_spatial_null
"""
from itertools import combinations
from math import comb

from experiments.e001_baseline import evaluate
from experiments.e001_exact_label_null import exact_label_null


def fixture():
    return [
        {"site_id": f"pair_{block}_{member}", "family": "Mars",
         "x": 10.0 * block + 0.02 * member,
         "is_analog": "1" if block in (0, 1) else "0"}
        for block in range(4) for member in range(2)
    ]


def block_null(rows):
    """Permute whole spatial blocks; preserve exactly two positive blocks."""
    scores = []
    for selected in combinations(range(4), 2):
        selected = set(selected)
        assigned = [
            dict(row, is_analog="1" if int(row["site_id"].split("_")[1]) in selected else "0")
            for row in rows
        ]
        scores.append(evaluate(assigned, ["x"])["top_1_rate"])
    return scores


def run():
    rows = fixture()
    observed = evaluate(rows, ["x"])["top_1_rate"]
    naive = exact_label_null(rows, ["x"], max_assignments=100)
    spatial = block_null(rows)
    naive_p = naive["one_sided_p"]
    block_p = sum(score >= observed for score in spatial) / len(spatial)
    assert observed == 1.0
    assert naive["exact_null_assignments"] == comb(8, 4) == 70
    assert abs(naive_p - 3 / 70) < 1e-12
    assert len(spatial) == comb(4, 2) == 6
    assert abs(block_p - 3 / 6) < 1e-12
    return {"observed_top_1": observed, "naive_assignments": 70,
            "naive_p": naive_p, "spatial_assignments": 6,
            "spatial_p": block_p}


if __name__ == "__main__":
    print(run())
