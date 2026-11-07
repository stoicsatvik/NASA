"""E001 exact within-family label null, independent of planetary evidence.

Preserves positive counts within each family and enumerates all distinct
assignments. Intended for small site cohorts; refuses combinatorial explosion.
"""
from itertools import combinations, product
from math import comb

from experiments.e001_baseline import evaluate


def exact_label_null(rows, features, candidate_policy="all_nonreference",
                     max_assignments=10000):
    """Return exact label-null distribution of top-1 recovery.

    Family membership and numeric descriptors remain fixed. Only positive
    labels are reassigned within families. This is not a site-independent
    external validation and must not be presented as analogue discovery.
    """
    families = sorted({r["family"] for r in rows})
    groups = [[i for i, r in enumerate(rows) if r["family"] == family]
              for family in families]
    counts = [sum(rows[i]["is_analog"] == "1" for i in group)
              for group in groups]
    if any(k < 2 for k in counts):
        raise ValueError("Each family requires at least two positive sites")
    n_assignments = 1
    for group, k in zip(groups, counts):
        n_assignments *= comb(len(group), k)
    if n_assignments > max_assignments:
        raise ValueError("Exact null exceeds max_assignments; use sampled null")
    observed = evaluate(rows, features, candidate_policy)["top_1_rate"]
    null_scores = []
    for choices in product(*(combinations(group, k)
                             for group, k in zip(groups, counts))):
        positives = set(i for choice in choices for i in choice)
        permuted = [dict(row, is_analog=("1" if i in positives else "0"))
                    for i, row in enumerate(rows)]
        null_scores.append(evaluate(permuted, features, candidate_policy)["top_1_rate"])
    return {"observed_top_1_rate": observed,
            "exact_null_assignments": len(null_scores),
            "null_mean_top_1_rate": sum(null_scores) / len(null_scores),
            "one_sided_p": sum(x >= observed for x in null_scores) / len(null_scores),
            "null_scores": null_scores}
