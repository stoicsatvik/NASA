"""E293: pre-event real-source Diviner STN spatial-missingness falsification.

No cross-body similarity, thermal-inertia inference, field data or Space Apps
solution. Tests whether three E291 row missingness masks resemble exchangeable
independent positions, not whether their causes are known.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import struct
from pathlib import Path
from urllib.request import Request, urlopen

from research.e291_diviner_access import (
    PDS_STN_BASE, PDS_STN_NAME, validate_pds_stn_label,
)

ROWS = (640, 1920, 3200)
EXPECTED_SHA = {
    640: "cd36dd68a19c647e96393a0580eddbbd5fcf68109b16bc4c0b806ed5a2a227b8",
    1920: "a44e547eb91871b97b4ce50e0bffa1189e1e4ce947e59953c622bb866bba87ad",
    3200: "eec2cc72ae43517470a6b49a6cbb9112f04ab0952983f228ac2685dab5aaa91e",
}
WIDTH = 128
PERMUTATIONS = 199


def longest_circular_run(mask: list[bool]) -> int:
    if not mask or not any(mask):
        return 0
    n = len(mask)
    if all(mask):
        return n
    run = best = 0
    for flag in mask + mask:
        run = run + 1 if flag else 0
        best = max(best, run)
    return min(best, n)


def max_circular_window(mask: list[bool], width: int = WIDTH) -> int:
    n = len(mask)
    if not (0 < width <= n):
        raise ValueError("window width outside mask")
    extended = mask + mask[:width - 1]
    current = sum(extended[:width])
    best = current
    for start in range(1, n):
        current += int(extended[start + width - 1]) - int(extended[start - 1])
        best = max(best, current)
    return best


def audit_mask(mask: list[bool], *, seed: int, permutations: int = PERMUTATIONS) -> dict:
    if not mask:
        raise ValueError("empty mask")
    if permutations < 1:
        raise ValueError("at least one permutation required")
    missing = sum(mask)
    observed_run = longest_circular_run(mask)
    observed_window = max_circular_window(mask, min(WIDTH, len(mask)))
    rng = random.Random(seed)
    null_run, null_window = [], []
    shuffled = list(mask)
    for _ in range(permutations):
        rng.shuffle(shuffled)
        null_run.append(longest_circular_run(shuffled))
        null_window.append(max_circular_window(shuffled, min(WIDTH, len(mask))))
    return {
        "cells": len(mask),
        "missing": missing,
        "missing_fraction": missing / len(mask),
        "longest_circular_missing_run_pixels": observed_run,
        "max_missing_in_circular_128px_window": observed_window,
        "window_width_pixels": min(WIDTH, len(mask)),
        "null_longest_run_max": max(null_run),
        "null_window_missing_max": max(null_window),
        "null_longest_run_mean": sum(null_run) / permutations,
        "null_window_missing_mean": sum(null_window) / permutations,
        "permutation_p_run": (1 + sum(x >= observed_run for x in null_run)) / (permutations + 1),
        "permutation_p_window": (1 + sum(x >= observed_window for x in null_window)) / (permutations + 1),
        "null_model": "fixed missing count; uniformly permuted longitude positions, circular wrap",
        "null_permutations": permutations,
    }


def fetch_row(row: int, samples: int) -> bytes:
    size = samples * 2
    start = row * size
    end = start + size - 1
    url = PDS_STN_BASE + PDS_STN_NAME + ".img"
    with urlopen(Request(url, headers={
        "User-Agent": "NASA-E293-ReadOnly-SourceQC/1.0",
        "Range": f"bytes={start}-{end}",
    }), timeout=50) as response:
        content_range = response.headers.get("Content-Range", "")
        if response.status != 206 or not content_range.startswith(f"bytes {start}-{end}/"):
            raise ValueError("PDS did not honor bounded exact byte range")
        raw = response.read(size + 1)
    if len(raw) != size:
        raise ValueError("PDS row byte count mismatch")
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA[row]:
        raise ValueError("E291 source fingerprint changed; do not silently compare")
    return raw


def audit() -> dict:
    label_url = PDS_STN_BASE + PDS_STN_NAME + ".lbl"
    with urlopen(Request(label_url, headers={
        "User-Agent": "NASA-E293-ReadOnly-SourceQC/1.0",
    }), timeout=35) as response:
        raw_label = response.read(20_001)
    if len(raw_label) > 20_000:
        raise ValueError("PDS label too large")
    label_sha = hashlib.sha256(raw_label).hexdigest()
    if label_sha != "254aade12b81b51560bbcce0501948acfe91ea61d878e06f7c66256ff28c20ad":
        raise ValueError("E291 PDS label fingerprint changed")
    metadata = validate_pds_stn_label(raw_label.decode("utf-8"))
    samples = metadata["line_samples"]
    out = []
    for row in ROWS:
        raw = fetch_row(row, samples)
        values = struct.unpack("<" + str(samples) + "h", raw)
        mask = [value == metadata["missing_constant"] for value in values]
        out.append({
            "row_index": row,
            "approx_latitude_deg": 60 - (row + 0.5) / 32,
            "row_sha256": EXPECTED_SHA[row],
            **audit_mask(mask, seed=293_000 + row),
        })
    return {
        "experiment": "E293 Diviner STN spatial missingness vs exchangeable null",
        "label_url": label_url,
        "label_sha256": label_sha,
        "image_url": PDS_STN_BASE + PDS_STN_NAME + ".img",
        "product_semantics": "nighttime rock-free regolith temperature deviation (K), NOT thermal inertia",
        "source_type": "genuine official PDS Diviner rows; no raw image committed",
        "rows": out,
        "interpretation_boundary": (
            "Permutation p-values test only fixed-count spatial exchangeability within each sampled "
            "row, not physical causes, global missingness, instrument independence or cross-body similarity."
        ),
        "e001_known_analogue_recovery": "NOT YET MEASURED",
        "cross_body_similarity": "NOT YET PROVEN",
        "novel_analogue_discovery": "NOT YET PROVEN",
        "challenge_selection_superiority": "NOT YET PROVEN",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit()
    payload = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n")
    print(payload)


if __name__ == "__main__":
    main()
