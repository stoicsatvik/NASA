"""E273: measured lunar sampling-support ablation against native MOLA.

Research-only, pre-event. Tests a necessary representation assumption, NOT
known-site recovery or evidence of geological analogues.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from research.e212_lola_mola_scale_gate import (
    COLS, ROWS, MOON_RADIUS_KM, MARS_RADIUS_KM, pixel_km, sha256,
)
from research.mola_megdr_quality_gate import metadata

# Frozen from successful E212 real-source receipt (2026-10-24).
EXPECTED = {
    "lola": "330afa2556a86fd05ac6ba2f912f246600fdade35de2a0d90593d50d07b01b65",
    "mola": "25f16fb7aaf857898dcf98bc4f841341a24f8b9f7e98453ca083bc45d897ca2c",
    "counts": "7e920ec43497b4beddf974650471600c7afd4916e2a8dd3500d6b14714365661",
}
MOON_SUPPORT = 4
MARS_SUPPORT = 2
MIN_MOLA_COVERAGE = 0.75


def lunar_windows(z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Aligned 4x4 Moon tiles; 2x2 block means represent coarser support."""
    if z.ndim != 2 or z.shape[0] % 4 or z.shape[1] % 4 or not np.isfinite(z).all():
        raise ValueError("lunar window must be finite and divisible by four")
    windows = z.reshape(z.shape[0] // 4, 4, z.shape[1] // 4, 4)
    windows = windows.transpose(0, 2, 1, 3).reshape(-1, 4, 4)
    coarsened = windows.reshape(-1, 2, 2, 2, 2).mean(axis=(2, 4))
    return windows.std(axis=(1, 2)), coarsened.std(axis=(1, 2))


def martian_windows(z: np.ndarray, observed: np.ndarray) -> tuple[np.ndarray, int]:
    if z.ndim != 2 or z.shape != observed.shape or z.shape[0] % 2 or z.shape[1] % 2:
        raise ValueError("Martian grid/mask must be even and aligned")
    if not np.isfinite(z).all():
        raise ValueError("nonfinite MOLA elevations")
    windows = z.reshape(z.shape[0] // 2, 2, z.shape[1] // 2, 2)
    windows = windows.transpose(0, 2, 1, 3).reshape(-1, 4)
    masks = observed.reshape(observed.shape[0] // 2, 2, observed.shape[1] // 2, 2)
    masks = masks.transpose(0, 2, 1, 3).reshape(-1, 4)
    accepted = masks.mean(axis=1) >= MIN_MOLA_COVERAGE
    vals = np.where(masks[accepted], windows[accepted], np.nan)
    return np.nanstd(vals, axis=1), int((~accepted).sum())


def summarize(x: np.ndarray) -> dict:
    if x.ndim != 1 or not x.size or not np.isfinite(x).all():
        raise ValueError("nonfinite or empty summary")
    return {
        "n": int(x.size),
        "median_m": float(np.median(x)),
        "p10_m": float(np.percentile(x, 10)),
        "p90_m": float(np.percentile(x, 90)),
    }


def top_decile_retention(a: np.ndarray, b: np.ndarray) -> dict:
    if a.shape != b.shape or a.ndim != 1 or a.size < 10:
        raise ValueError("invalid paired ranking")
    k = max(1, int(a.size * 0.1))
    top_a = set(np.argsort(a, kind="stable")[-k:].tolist())
    top_b = set(np.argsort(b, kind="stable")[-k:].tolist())
    return {"top_k": k, "intersection": len(top_a & top_b),
            "retention_fraction": len(top_a & top_b) / k}


def audit(lunar_m: np.ndarray, mars_m: np.ndarray, counts: np.ndarray) -> dict:
    if lunar_m.shape != (ROWS, COLS) or mars_m.shape != (ROWS, COLS) or counts.shape != (ROWS, COLS):
        raise ValueError("unexpected global raster geometry")
    if not np.isfinite(lunar_m).all() or not np.isfinite(mars_m).all() or np.any(counts < 0):
        raise ValueError("invalid raster data")
    moon = lunar_m[320:400]
    mars = mars_m[320:400]
    mask = counts[320:400] > 0
    raw, coarsened = lunar_windows(moon)
    mars_native, rejected = martian_windows(mars, mask)
    moon_ns_km = pixel_km(MOON_RADIUS_KM)[0] * MOON_SUPPORT
    mars_ns_km = pixel_km(MARS_RADIUS_KM)[0] * MARS_SUPPORT
    raw_median = float(np.median(raw))
    coarse_median = float(np.median(coarsened))
    mars_median = float(np.median(mars_native))
    if min(raw_median, mars_median) <= 0:
        raise ValueError("degenerate real-source roughness")
    return {
        "experiment": "E273 real lunar support-aggregation falsification",
        "equatorial_latitude_window_deg": [-10, 10],
        "moon_4px_support_ns_km": moon_ns_km,
        "mars_2px_support_ns_km": mars_ns_km,
        "physical_support_difference_fraction": abs(moon_ns_km - mars_ns_km) / moon_ns_km,
        "moon_native_4x4": summarize(raw),
        "moon_coarsened_2x2_block_means": summarize(coarsened),
        "mars_native_2x2_counts_masked": summarize(mars_native),
        "mars_rejected_low_coverage_windows": rejected,
        "moon_coarsening_median_retained_fraction": coarse_median / raw_median,
        "moon_top_decile_retention": top_decile_retention(raw, coarsened),
        "moon_to_mars_median_roughness_ratio_native": raw_median / mars_median,
        "moon_to_mars_median_roughness_ratio_coarsened": coarse_median / mars_median,
        "moon_coarsened_fraction_exceeding_native": float(np.mean(coarsened > raw + 1e-8)),
        "claim": "SAMPLING SUPPORT SENSITIVITY ONLY; CROSS-BODY SIMILARITY NOT YET PROVEN; E001 NOT YET MEASURED",
        "limitations": [
            "LOLA TIFF is a NASA SVS derived raster without shot-count/coverage mask.",
            "Moon block means simulate spatial averaging, not actual MOLA instrument point-spread or shot sampling.",
            "Equal north-south support does not equalize east-west support away from the equator.",
            "Moon 4x4 tiles and Mars 2x2 tiles have different counts and geographic footprints; distribution comparison is descriptive only.",
            "No Earth candidate labels, negative sites, blind recovery, or physical analogue prediction.",
            "Lunar and Martian vertical datums and geology differ; ratios are NOT a similarity metric.",
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser()
    for name in ("lola", "mola", "counts", "mola-label", "counts-label"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    files = {"lola": args.lola, "mola": args.mola, "counts": args.counts}
    observed_hashes = {name: sha256(path) for name, path in files.items()}
    if observed_hashes != EXPECTED:
        raise ValueError("public source fingerprint changed; inspect before interpreting")
    metadata(args.mola_label, "MEGT90N000CB.IMG")
    metadata(args.counts_label, "MEGC90N000CB.IMG")
    with Image.open(args.lola) as im:
        if im.format != "TIFF" or im.size != (COLS, ROWS) or im.mode != "F":
            raise ValueError("LOLA raster format changed")
        lunar_m = np.asarray(im, dtype=np.float64).copy() * 1000
    mola = np.fromfile(args.mola, dtype=">i2")
    counts = np.fromfile(args.counts, dtype=">i2")
    if mola.size != ROWS * COLS or counts.size != ROWS * COLS:
        raise ValueError("MOLA source size changed")
    result = audit(lunar_m, mola.reshape(ROWS, COLS).astype(float),
                   counts.reshape(ROWS, COLS))
    result["source_sha256"] = observed_hashes
    result["sources"] = {
        "lola": "https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/ldem_4.tif",
        "mola": "https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/meg004/",
    }
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
