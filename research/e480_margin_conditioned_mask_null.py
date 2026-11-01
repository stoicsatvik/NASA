"""E480: exact row/column-margin controls on PDS-derived E472 Mars masks.

This is a conditional binary-mask experiment, NOT a physical instrument model,
terrain slope measurement, or planetary analogue recovery result. No data access
beyond the pinned E472 archived observation masks is required.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations, product
from hashlib import sha256
from json import loads, dumps
from pathlib import Path

SOURCE_SHA256 = "2e70d84ca45cc4730c87e8931194c5ba1cd7a31bdd15e9a7883c5611578c9dfb"


def read_pinned_source(path: str | Path) -> dict:
    raw = Path(path).read_bytes()
    if sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError("E472 Mars source SHA-256 mismatch; refusing unpinned input")
    obj = loads(raw)
    if len(obj.get("windows", [])) != 3:
        raise ValueError("unexpected source cohort")
    return obj


def parse_mars_5x5(window: dict) -> tuple[tuple[int, ...], ...]:
    source = window["observed_mask_rows"]
    if len(source) != 9 or any(not isinstance(row, str) or len(row) != 9 or set(row) - {"0", "1"} for row in source):
        raise ValueError("invalid 9x9 observed-mask geometry")
    rows = tuple(tuple(int(x) for x in row[2:7]) for row in source[2:7])
    if sum(map(sum, rows)) != window["center_5x5_observed_cells"]:
        raise ValueError("5x5 count does not match archived source")
    return rows


def geometry(rows: tuple[tuple[int, ...], ...]) -> tuple[int, int, int]:
    n = len(rows)
    if n != 5 or any(len(row) != n or any(x not in (0, 1) for x in row) for row in rows):
        raise ValueError("expected a 5x5 binary mask")
    horizontal = sum(rows[i][j] * rows[i][j + 1] for i in range(n) for j in range(n - 1))
    vertical = sum(rows[i][j] * rows[i + 1][j] for i in range(n - 1) for j in range(n))
    crosses = sum(rows[i][j] * rows[i - 1][j] * rows[i + 1][j] * rows[i][j - 1] * rows[i][j + 1]
                  for i in range(1, n - 1) for j in range(1, n - 1))
    return horizontal, vertical, crosses


def _options(count: int) -> tuple[tuple[int, ...], ...]:
    if not 0 <= count <= 5:
        raise ValueError("invalid margin")
    return tuple(tuple(int(j in chosen) for j in range(5)) for chosen in combinations(range(5), count))


def exact_conditioned(rows: tuple[tuple[int, ...], ...], mode: str) -> dict:
    """Uniform exact enumeration over binary matrices with fixed row, column, or both margins.

    One-sided statistic D = vertical adjacent pairs - horizontal adjacent pairs.
    Report integer tails, not floating Monte Carlo p-values. Both-margin null
    uses recursive pruning, avoiding enumeration of unconstrained 2^25 grids.
    """
    geometry(rows)  # validate shape
    if mode not in ("row", "column", "both"):
        raise ValueError("invalid conditioning mode")
    row_margins = tuple(map(sum, rows))
    column_margins = tuple(sum(rows[i][j] for i in range(5)) for j in range(5))
    target = geometry(rows)[1] - geometry(rows)[0]
    hist: Counter[int] = Counter()
    zero_cross = 0

    def record(candidate: tuple[tuple[int, ...], ...]) -> None:
        nonlocal zero_cross
        h, v, cross = geometry(candidate)
        hist[v - h] += 1
        zero_cross += (cross == 0)

    if mode == "both":
        options = tuple(_options(k) for k in row_margins)
        def visit(index: int, column_so_far: tuple[int, ...], selected: tuple[tuple[int, ...], ...]) -> None:
            if index == 5:
                if column_so_far == column_margins:
                    record(selected)
                return
            for row in options[index]:
                new = tuple(a + b for a, b in zip(column_so_far, row))
                if any(v > target_col or v + 4 - index < target_col
                       for v, target_col in zip(new, column_margins)):
                    continue
                visit(index + 1, new, selected + (row,))
        visit(0, (0, 0, 0, 0, 0), ())
    else:
        margins = row_margins if mode == "row" else column_margins
        options = tuple(_options(k) for k in margins)
        for parts in product(*options):
            if mode == "row":
                record(parts)
            else:
                record(tuple(tuple(parts[j][i] for j in range(5)) for i in range(5)))

    total = sum(hist.values())
    if total == 0:
        raise ValueError("inconsistent margins")
    tail = sum(count for value, count in hist.items() if value >= target)
    return {
        "conditioning": mode,
        "total_masks": total,
        "observed_vertical_minus_horizontal": target,
        "one_sided_vertical_tail_masks": tail,
        "one_sided_vertical_tail_probability": tail / total,
        "zero_five_point_masks": zero_cross,
        "zero_five_point_probability": zero_cross / total,
        "exact_difference_histogram": {str(k): hist[k] for k in sorted(hist)},
    }


def evaluate(source: dict) -> dict:
    expected = (-0.5, -20, -40)
    results = []
    for w, latitude in zip(source["windows"], expected):
        if w["latitude_deg_requested"] != latitude or w["longitude_deg_requested"] != 45:
            raise ValueError("unexpected site ordering/location")
        rows = parse_mars_5x5(w)
        h, v, cross = geometry(rows)
        row = tuple(map(sum, rows))
        col = tuple(sum(rows[i][j] for i in range(5)) for j in range(5))
        results.append({
            "latitude_deg": latitude, "longitude_deg": 45,
            "mask_rows": ["".join(map(str, r)) for r in rows],
            "row_margins": row, "column_margins": col,
            "observed_cells": sum(row), "horizontal_edges": h, "vertical_edges": v,
            "complete_five_point_stencils": cross,
            "nulls": [exact_conditioned(rows, mode) for mode in ("row", "column", "both")],
        })
    return {
        "schema": "nasa/e480/exact-margin-conditioned-mask-null/v1",
        "source": "Archived E472 artifact 13075465278, official PDS-derived MOLA count masks",
        "source_mars_sha256": SOURCE_SHA256,
        "statistic": "one-sided P(D >= D_observed), D=vertical observed adjacencies minus horizontal observed adjacencies",
        "null": "uniform over binary 5x5 matrices preserving the stated margins; not an instrument-track model",
        "windows": results,
        "claim_states": {
            "mask_geometry_conditioning": "SUPPORTED for these three real-source masks",
            "causal_track_explanation": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "cross_body_similarity": "NOT YET PROVEN",
            "novel_analogue_discovery": "NOT YET PROVEN",
            "local_validation_advantage": "NOT YET PROVEN",
            "challenge_selection_superiority": "NOT YET PROVEN",
        },
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("mars_source", type=Path)
    args = parser.parse_args()
    print(dumps(evaluate(read_pinned_source(args.mars_source)), indent=2))
