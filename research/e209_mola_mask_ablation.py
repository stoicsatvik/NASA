"""E209: MOLA MEG004 count-mask sensitivity, using real official rasters only.

No planetary-analogue discovery is claimed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path


def std(values):
    if not values:
        raise ValueError("cannot summarize empty values")
    mean = sum(values) / len(values)
    return math.sqrt(sum((x - mean) ** 2 for x in values) / len(values))


def rank_sensitivity(heights, counts, rows, cols, tile_size=16, min_observed_fraction=0.25):
    if len(heights) != rows * cols or len(counts) != rows * cols:
        raise ValueError("grid shape mismatch")
    if rows % tile_size or cols % tile_size or tile_size < 2:
        raise ValueError("tile_size must divide grid and be >=2")
    if not (0 < min_observed_fraction <= 1):
        raise ValueError("invalid observation threshold")
    valid, excluded, coverage_values = [], 0, []
    for row in range(0, rows, tile_size):
        for col in range(0, cols, tile_size):
            values, measured = [], []
            for y in range(row, row + tile_size):
                offset = y * cols
                for x in range(col, col + tile_size):
                    i = offset + x
                    values.append(heights[i])
                    if counts[i] > 0:
                        measured.append(heights[i])
            coverage = len(measured) / len(values)
            coverage_values.append(coverage)
            if coverage < min_observed_fraction or len(measured) < 2:
                excluded += 1
                continue
            valid.append((f"{row}:{col}", std(values), std(measured), coverage))
    result = {
        "tile_size_pixels": tile_size,
        "min_observed_fraction": min_observed_fraction,
        "total_tiles": len(coverage_values),
        "excluded_tiles": excluded,
        "eligible_tiles": len(valid),
        "tiles_below_50_percent_measured": sum(c < 0.5 for c in coverage_values),
        "mean_tile_observed_fraction": sum(coverage_values) / len(coverage_values),
        "metric": "within-tile elevation standard deviation in metres; not scale-corrected roughness",
    }
    if len(valid) < 2:
        result.update({"top_decile_overlap_fraction": None, "ordinal_rank_correlation": None})
        return result
    by_all = sorted(valid, key=lambda item: (-item[1], item[0]))
    by_measured = sorted(valid, key=lambda item: (-item[2], item[0]))
    k = max(1, math.ceil(len(valid) / 10))
    overlap = len({x[0] for x in by_all[:k]} & {x[0] for x in by_measured[:k]})
    ranks = {x[0]: i for i, x in enumerate(by_measured)}
    n = len(valid)
    sum_sq = sum((i - ranks[x[0]]) ** 2 for i, x in enumerate(by_all))
    result.update({
        "top_decile_k": k,
        "top_decile_overlap_fraction": overlap / k,
        "ordinal_rank_correlation": 1 - 6 * sum_sq / (n * (n * n - 1)),
        "max_rank_displacement": max(abs(i - ranks[x[0]]) for i, x in enumerate(by_all)),
        "mean_all_cells_std_m": sum(x[1] for x in valid) / n,
        "mean_measured_only_std_m": sum(x[2] for x in valid) / n,
    })
    return result


def main():
    from mola_megdr_quality_gate import analyze, read_grid
    parser = argparse.ArgumentParser()
    for flag in ("topography", "counts", "topography-label", "counts-label"):
        parser.add_argument("--" + flag, type=Path, required=True)
    args = parser.parse_args()
    qc = analyze(args.topography, args.counts, args.topography_label, args.counts_label)
    heights, _ = read_grid(args.topography, (720, 1440))
    counts, _ = read_grid(args.counts, (720, 1440))
    results = {
        "experiment": "E209 MOLA interpolation-mask rank sensitivity",
        "source_type": "official NASA PDS MOLA MEG004 raster bytes",
        "labels_sha256": {
            "topography": hashlib.sha256(args.topography_label.read_bytes()).hexdigest(),
            "counts": hashlib.sha256(args.counts_label.read_bytes()).hexdigest(),
        },
        "qc": qc,
        "tile_ablation": rank_sensitivity(heights, counts, 720, 1440),
        "limitations": [
            "Measured-cell selection changes sample size and may introduce selection bias.",
            "Tile standard deviation is not slope or resolution-matched planetary roughness.",
            "Equal-angle tiles have latitude-dependent physical areas.",
            "No Earth or Moon raster is ingested; E001 known-site recovery NOT YET MEASURED.",
            "Cross-body similarity and novel analogue discovery NOT YET PROVEN.",
        ],
    }
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
