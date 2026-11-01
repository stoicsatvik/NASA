"""Deterministic offline E480 contracts, with archived-source tests when provided."""
import importlib.util
import os
from pathlib import Path
from itertools import combinations, product

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("e480", HERE / "e480_margin_conditioned_mask_null.py")
e480 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e480)


def test_empty_and_full_masks():
    for digit, expected in ((0, 0), (1, 9)):
        rows = tuple((digit,) * 5 for _ in range(5))
        assert e480.geometry(rows)[2] == expected
        for mode in ("row", "column", "both"):
            result = e480.exact_conditioned(rows, mode)
            assert result["total_masks"] == 1
            assert result["one_sided_vertical_tail_probability"] == 1


def test_bad_masks_and_modes():
    with pytest.raises(ValueError):
        e480.geometry(((1, 0),) * 5)
    with pytest.raises(ValueError):
        e480.exact_conditioned(((0,) * 5,) * 5, "unconditional")
    with pytest.raises(ValueError):
        e480.parse_mars_5x5({"observed_mask_rows": ["bad"] * 9, "center_5x5_observed_cells": 0})


def test_independent_both_margin_oracle():
    # Independent brute-force row combinations, filtering column margins only
    # at completion, without the production recursive pruning.
    rows = ((0, 1, 0, 1, 0), (0, 1, 0, 1, 1), (1, 1, 0, 1, 1),
            (1, 0, 0, 1, 1), (1, 0, 0, 1, 1))
    row_counts = [sum(r) for r in rows]
    col_counts = [sum(rows[i][j] for i in range(5)) for j in range(5)]
    opts = [[tuple(int(j in c) for j in range(5)) for c in combinations(range(5), k)] for k in row_counts]
    oracle = []
    for candidate in product(*opts):
        if [sum(candidate[i][j] for i in range(5)) for j in range(5)] == col_counts:
            oracle.append(candidate)
    assert len(oracle) == 12
    observed = e480.geometry(rows)[1] - e480.geometry(rows)[0]
    assert sum(e480.geometry(m)[1] - e480.geometry(m)[0] >= observed for m in oracle) == 2
    result = e480.exact_conditioned(rows, "both")
    assert result["total_masks"] == 12
    assert result["one_sided_vertical_tail_masks"] == 2
    assert result["zero_five_point_masks"] == 12


def test_archived_source_and_three_null_families():
    path = Path(os.environ.get("E480_MARS_SOURCE", HERE / "e472_mars_source.json"))
    if not path.exists():
        pytest.skip("pinned E472 source absent; no synthetic substitution")
    result = e480.evaluate(e480.read_pinned_source(path))
    expected = [
        (11, 2, 8, (100000, 316, 100000), (5, 5, 5), (1, 1, 1)),
        (3, 0, 2, (125, 5, 125), (10, 3, 10), (1, 1, 1)),
        (15, 5, 11, (50000, 489, 25496), (500, 4, 500), (12, 2, 12)),
    ]
    for w, (k, h, v, row, col, both) in zip(result["windows"], expected):
        assert (w["observed_cells"], w["horizontal_edges"], w["vertical_edges"]) == (k, h, v)
        for actual, target in zip(w["nulls"], (row, col, both)):
            assert (actual["total_masks"], actual["one_sided_vertical_tail_masks"],
                    actual["zero_five_point_masks"]) == target
    assert all(w["complete_five_point_stencils"] == 0 for w in result["windows"])
    assert result["windows"][2]["column_margins"][2] == 0


def test_tampered_source_rejected(tmp_path):
    p = tmp_path / "mars.json"
    p.write_text('{"windows": []}')
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        e480.read_pinned_source(p)
