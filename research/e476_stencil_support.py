"""E476: conservative observation-mask admissibility for local terrain stencils.

Input is the archived E472 GitHub Actions artifact's e472_mars_source.json and
 e472_moon_source.json. No raster downloads, interpolation, or analogue labels.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
from pathlib import Path

SOURCE_SHA256 = {
    "mars": "2e70d84ca45cc4730c87e8931194c5ba1cd7a31bdd15e9a7883c5611578c9dfb",
    "moon": "a4ed427e5996b8ef115e0bf8130f615089248bae8d89ec43cdd6fa2bf80f96c4",
}


def load_pinned(path: Path, body: str) -> dict:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256[body]:
        raise ValueError(f"{body}: unrecognized E472 source artifact")
    payload = json.loads(raw)
    expected = ("nasa/e463/mola128-bounded-real-data-coverage/v1" if body == "mars"
                else "nasa/e469/lola128-bounded-count-coverage/v1")
    if payload.get("schema") != expected or len(payload.get("windows", [])) != 3:
        raise ValueError("wrong source schema or frozen window population")
    return payload


def mask(rows: list[str], width: int) -> tuple[tuple[int, ...], ...]:
    if len(rows) != width or any(type(r) is not str or len(r) != width
                                 or set(r) - {"0", "1"} for r in rows):
        raise ValueError("invalid square binary observation mask")
    return tuple(tuple(int(c) for c in row) for row in rows)


def support(a: tuple[tuple[int, ...], ...]) -> dict:
    n = len(a)
    if n < 3 or any(len(row) != n or any(x not in (0, 1) for x in row) for row in a):
        raise ValueError("invalid support grid")
    full = sum(all(a[y + dy][x + dx] for dy in (-1, 0, 1)
                   for dx in (-1, 0, 1)) for y in range(1, n - 1)
                   for x in range(1, n - 1))
    cross = sum(all(a[y + dy][x + dx] for dy, dx in
                    ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)))
                for y in range(1, n - 1) for x in range(1, n - 1))
    horizontal = sum(a[y][x] * a[y][x + 1]
                     for y in range(n) for x in range(n - 1))
    vertical = sum(a[y][x] * a[y + 1][x]
                   for y in range(n - 1) for x in range(n))
    return {"observed": sum(map(sum, a)), "cells": n * n,
            "eligible_centers": (n - 2) ** 2, "full_3x3_centers": full,
            "five_point_cross_centers": cross,
            "horizontal_observed_edges": horizontal,
            "vertical_observed_edges": vertical}


def fixed_count_shuffle_null(n: int, k: int, observed_delta: int,
                             draws: int = 20000, seed: int = 476) -> dict:
    if not 0 <= k <= n * n or draws < 1:
        raise ValueError("invalid null population")
    rng = random.Random(seed)
    extremes = 0
    for _ in range(draws):
        chosen = set(rng.sample(range(n * n), k))
        a = tuple(tuple(int(y * n + x in chosen) for x in range(n)) for y in range(n))
        result = support(a)
        delta = result["vertical_observed_edges"] - result["horizontal_observed_edges"]
        extremes += abs(delta) >= abs(observed_delta)
    return {"draws": draws, "seed": seed, "extreme_draws": extremes,
            "two_sided_mc_tail_plus_one": (extremes + 1) / (draws + 1),
            "null": "uniform fixed-count cell shuffle; not a physical instrument model"}


def evaluate(mars: dict, moon: dict, draws: int = 20000) -> dict:
    results = []
    for mw, lw in zip(mars["windows"], moon["windows"]):
        if (mw["latitude_deg_requested"], mw["longitude_deg_requested"]) != (
                lw["latitude_deg_requested"], lw["longitude_deg_requested"]):
            raise ValueError("unmatched locations")
        for body, w in (("moon", lw), ("mars", mw)):
            original = mask(w["observed_mask_rows"], 9)
            if sum(map(sum, original)) != w[("observed_cells" if body == "moon" else "measured_cells")]:
                raise ValueError("source mask count mismatch")
            a = original if body == "moon" else tuple(row[2:7] for row in original[2:7])
            stats = support(a)
            if body == "mars" and stats["observed"] != w["center_5x5_observed_cells"]:
                raise ValueError("Martian central support mismatch")
            delta = stats["vertical_observed_edges"] - stats["horizontal_observed_edges"]
            results.append({"body": body, "latitude_deg": w["latitude_deg_requested"],
                            "longitude_deg": w["longitude_deg_requested"],
                            "nominal_window": "9x9" if body == "moon" else "5x5",
                            **stats, "vertical_minus_horizontal_edges": delta,
                            "fixed_count_shuffle": fixed_count_shuffle_null(len(a), stats["observed"],
                                                                         delta, draws)})
    return {"schema": "nasa/e476/observed-stencil-admissibility/v1",
            "source": "E472 archived official PDS-derived count masks, artifact 13075465278",
            "source_sha256": SOURCE_SHA256, "windows": results,
            "claim": "Conservative complete-observation stencil admissibility at six nonrandom windows only",
            "known_site_recovery": "NOT YET MEASURED", "cross_body_similarity": "NOT YET PROVEN",
            "limitations": ["Observation counts >0 do not establish independent resolution",
                            "Full stencil support is a necessary, not sufficient, condition for a measured-only centered finite-difference descriptor",
                            "A count-zero grid may have interpolated elevation; this analysis intentionally excludes it",
                            "Fixed-count shuffle null ignores instrument track geometry; p-values exploratory and conditional",
                            "Three selected sites per body are not global or analogue-labelled samples"]}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("mars", type=Path)
    p.add_argument("moon", type=Path)
    p.add_argument("--draws", type=int, default=20000)
    args = p.parse_args()
    print(json.dumps(evaluate(load_pinned(args.mars, "mars"),
                              load_pinned(args.moon, "moon"), args.draws), indent=2))


if __name__ == "__main__":
    main()
