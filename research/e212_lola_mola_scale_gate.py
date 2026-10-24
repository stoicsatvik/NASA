"""E212: real LOLA/MOLA ingestion and equal-angle vs equal-distance audit.

This is a provenance/representation falsification, NOT a planetary analogue model.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import numpy as np
from PIL import Image

ROWS, COLS, PPD = 720, 1440, 4
MOON_RADIUS_KM = 1737.4
MARS_RADIUS_KM = 3389.5
LOLA_SOURCE = "https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/ldem_4.tif"
MOLA_SOURCE = "https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/meg004/"

def pixel_km(radius_km: float, latitude_deg: float = 0) -> tuple[float, float]:
    if radius_km <= 0 or not -90 <= latitude_deg <= 90:
        raise ValueError("invalid spherical geometry")
    lat_km = radius_km * math.pi / 180 / PPD
    return lat_km, lat_km * math.cos(math.radians(latitude_deg))

def tile_std(grid: np.ndarray, observed: np.ndarray, size: int, minimum: float = 0.75) -> np.ndarray:
    if grid.shape != observed.shape or grid.ndim != 2 or size < 2:
        raise ValueError("grid/mask/size mismatch")
    rows, cols = grid.shape
    if rows % size or cols % size:
        raise ValueError("tile size does not divide region")
    tiles = grid.reshape(rows // size, size, cols // size, size).transpose(0, 2, 1, 3).reshape(-1, size * size)
    mask = observed.reshape(rows // size, size, cols // size, size).transpose(0, 2, 1, 3).reshape(-1, size * size)
    valid = (mask.mean(axis=1) >= minimum) & (mask.sum(axis=1) >= 2)
    vals = np.where(mask[valid], tiles[valid], np.nan)
    return np.nanstd(vals, axis=1)

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def run(lola: Path, mola: Path, counts: Path, mola_label: Path, counts_label: Path) -> dict:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from research.mola_megdr_quality_gate import metadata
    metadata(mola_label, "MEGT90N000CB.IMG")
    metadata(counts_label, "MEGC90N000CB.IMG")
    with Image.open(lola) as im:
        if im.format != "TIFF" or im.size != (COLS, ROWS) or im.mode != "F":
            raise ValueError(f"unexpected LOLA TIFF encoding: {im.format}, {im.mode}, {im.size}")
        # NASA SVS documents float TIFF units as kilometers relative to 1737.4-km sphere.
        lunar_m = np.asarray(im, dtype=np.float64).copy() * 1000.0
    mars_m = np.fromfile(mola, dtype=">i2")
    counts_arr = np.fromfile(counts, dtype=">i2")
    if mars_m.size != ROWS * COLS or counts_arr.size != ROWS * COLS:
        raise ValueError("MOLA binary length mismatch")
    if np.any(counts_arr < 0):
        raise ValueError("negative MOLA counts")
    mars_m = mars_m.reshape(ROWS, COLS).astype(np.float64)
    counts_arr = counts_arr.reshape(ROWS, COLS)
    if not np.isfinite(lunar_m).all():
        raise ValueError("nonfinite lunar elevations; no silent imputation")
    # Equatorial +/-10 degrees minimizes latitude-dependent pixel-width distortion.
    lunar_eq = lunar_m[320:400]
    mars_eq = mars_m[320:400]
    observed_eq = counts_arr[320:400] > 0
    moon_4 = tile_std(lunar_eq, np.ones_like(lunar_eq, dtype=bool), 4)
    mars_2 = tile_std(mars_eq, observed_eq, 2)
    mars_4 = tile_std(mars_eq, observed_eq, 4)
    moon_px = pixel_km(MOON_RADIUS_KM)[0]
    mars_px = pixel_km(MARS_RADIUS_KM)[0]
    return {
        "experiment": "E212 real LOLA/MOLA raster ingestion and physical-footprint gate",
        "claim_state": "REAL LUNAR INGESTION ONLY; CROSS-BODY SIMILARITY NOT YET PROVEN; E001 NOT YET MEASURED",
        "sources": {"lola": LOLA_SOURCE, "mola": MOLA_SOURCE},
        "sha256": {"lola_tiff": sha256(lola), "mola_megt": sha256(mola), "mola_megc": sha256(counts), "mola_label": sha256(mola_label), "counts_label": sha256(counts_label)},
        "grid_shape": [ROWS, COLS],
        "latitude_window_deg": [-10, 10],
        "lola_vertical_unit": "km relative to lunar 1737.4-km sphere in TIFF; converted to m",
        "mola_vertical_unit": "m above MOLA areoid",
        "lola_coverage": "NOT MEASURED: NASA SVS derivative has no per-bin observation-count mask",
        "mola_equatorial_observed_fraction": float(observed_eq.mean()),
        "equatorial_pixel_north_south_km": {"moon": moon_px, "mars": mars_px},
        "equal_angle_4px_footprint_km": {"moon": moon_px * 4, "mars": mars_px * 4},
        "approx_equal_distance_footprint_km": {"moon_4px": moon_px * 4, "mars_2px": mars_px * 2},
        "physical_footprint_ratio_equal_angle": mars_px / moon_px,
        "tile_std_m": {
            "moon_4px": {"n": int(moon_4.size), "median": float(np.median(moon_4))},
            "mars_2px_masked": {"n": int(mars_2.size), "median": float(np.median(mars_2))},
            "mars_4px_masked": {"n": int(mars_4.size), "median": float(np.median(mars_4))},
        },
        "limitations": [
            "LOLA SVS TIFF is an official derived visualization product, not independently masked shot-level data.",
            "Equal-distance tiles still have unequal sample counts (Moon 16, Mars 4) and different instrument smoothing.",
            "MOLA and LOLA vertical datums differ; subtracting local means removes offsets but not instrument bias.",
            "Latitude affects east-west pixel scale; only +/-10 degrees examined.",
            "No Earth reference, independent known-site labels or E001 recovery performed.",
            "Numerical roughness summaries do NOT establish analogues or cross-body similarity.",
        ],
    }

def main() -> None:
    p = argparse.ArgumentParser()
    for name in ("lola", "mola", "counts", "mola-label", "counts-label"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(run(args.lola, args.mola, args.counts, args.mola_label, args.counts_label), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
