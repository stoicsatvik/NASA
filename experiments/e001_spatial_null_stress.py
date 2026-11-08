"""Synthetic falsification of naive site-label exchangeability under spatial clustering.

This is an adversarial statistical diagnostic, not planetary evidence.
"""
from itertools import combinations
from math import comb


def nearest_positive_score(positive, x):
    """Fraction of positives whose nearest other site is also positive."""
    positive = set(positive)
    return sum(
        min((abs(x[i] - x[j]), j) for j in range(len(x)) if j != i)[1] in positive
        for i in positive
    ) / len(positive)


def null_distribution(x, positives, blocks):
    n, k = len(x), len(positives)
    observed = nearest_positive_score(positives, x)
    unrestricted = [nearest_positive_score(c, x) for c in combinations(range(n), k)]
    unique_blocks = sorted(set(blocks))
    selected_blocks = {blocks[i] for i in positives}
    if any(
        set(i for i, b in enumerate(blocks) if b == block) - set(positives)
        for block in selected_blocks
    ):
        raise ValueError("positives must be unions of complete spatial blocks")
    restricted = []
    for selection in combinations(unique_blocks, len(selected_blocks)):
        ids = [i for i, b in enumerate(blocks) if b in selection]
        if len(ids) == k:
            restricted.append(nearest_positive_score(ids, x))
    return {
        "observed": observed,
        "unrestricted_assignments": len(unrestricted),
        "unrestricted_p": sum(s >= observed for s in unrestricted) / len(unrestricted),
        "block_assignments": len(restricted),
        "block_p": sum(s >= observed for s in restricted) / len(restricted),
    }


def test_spatial_confounded_null():
    # Ten close pairs, separated by large gaps; five complete pairs positive.
    # Label clustering is an artifact of block selection, not geological similarity.
    x = [10 * b + d * 0.01 for b in range(10) for d in (0, 1)]
    blocks = [b for b in range(10) for _ in (0, 1)]
    positives = list(range(10))
    result = null_distribution(x, positives, blocks)
    assert result["unrestricted_assignments"] == comb(20, 10)
    assert result["block_assignments"] == comb(10, 5)
    assert result["observed"] == 1.0
    assert result["block_p"] == 1.0
    assert result["unrestricted_p"] < 0.05
    return result


if __name__ == "__main__":
    print(test_spatial_confounded_null())
