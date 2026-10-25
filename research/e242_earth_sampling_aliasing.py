"""E242: 30-km Earth sampling-density null for planetary terrain comparisons.

This deliberately degrades real Earth terrain to 4x4 and 2x2 samples, the
approximate counts in 30-km equatorial LOLA/MOLA tiles. NOT a point-spread
function simulation or an analogue-recovery benchmark.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from research.e214_earth_dem_site_qc import SITES, R, source_url

PHASES = (0.125, 0.375, 0.625, 0.875)
SITES_TO_TEST = ("western_ghats_lead", "ladakh_lead")
WIDTH_KM = 30.0
MOON_EQ_TILE_KM = 30.32335042414948
MARS_EQ_TILE_KM = 29.5789674981739

def footprint_bounds(lat: float, lon: float, width_km: float) -> tuple[float, float, float, float]:
    """30-km geodesic approximation, independent of E214's <=20-km QC cap."""
    if not all(math.isfinite(v) for v in (lat, lon, width_km)) or not (-85 < lat < 85 and -180 < lon < 180 and 0 < width_km <= 40):
        raise ValueError("invalid footprint geometry")
    half = width_km * 500 / R
    dlat = math.degrees(half)
    dlon = math.degrees(half / math.cos(math.radians(lat)))
    return lon - dlon, lat - dlat, lon + dlon, lat + dlat

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def plane_detrended_std(z: np.ndarray) -> float:
    """Sample-grid-specific planar detrending; 2x2 has one residual DoF."""
    a = np.asarray(z, dtype=float)
    if a.ndim != 2 or min(a.shape) < 2 or not np.isfinite(a).all():
        raise ValueError("expected finite >=2x2 elevations")
    yy, xx = np.indices(a.shape, dtype=float)
    xx = (xx - (a.shape[1] - 1) / 2) / max(1, a.shape[1] - 1)
    yy = (yy - (a.shape[0] - 1) / 2) / max(1, a.shape[0] - 1)
    X = np.column_stack((xx.ravel(), yy.ravel(), np.ones(a.size)))
    coefficients = np.linalg.lstsq(X, a.ravel(), rcond=None)[0]
    return float(np.std(a.ravel() - X @ coefficients))

def block_means(z: np.ndarray, n: int) -> np.ndarray:
    a = np.asarray(z, dtype=float)
    if a.ndim != 2 or n < 2 or min(a.shape) < n or not np.isfinite(a).all():
        raise ValueError("invalid array or coarse grid")
    rows = np.array_split(np.arange(a.shape[0]), n)
    cols = np.array_split(np.arange(a.shape[1]), n)
    return np.array([[float(a[np.ix_(r, c)].mean()) for c in cols] for r in rows])

def point_sample(z: np.ndarray, n: int, phase_y: float, phase_x: float) -> np.ndarray:
    a = np.asarray(z, dtype=float)
    if a.ndim != 2 or n < 2 or min(a.shape) < n or not np.isfinite(a).all():
        raise ValueError("invalid array or coarse grid")
    if not (0 <= phase_x < 1 and 0 <= phase_y < 1):
        raise ValueError("invalid sampling phase")
    iy = np.floor((np.arange(n) + phase_y) * a.shape[0] / n).astype(int)
    ix = np.floor((np.arange(n) + phase_x) * a.shape[1] / n).astype(int)
    return a[np.ix_(iy, ix)]

def audit(z: np.ndarray) -> dict:
    a = np.asarray(z, dtype=float)
    if a.ndim != 2 or min(a.shape) < 32 or not np.isfinite(a).all():
        raise ValueError("patch must be >=32x32 and fully finite")
    reference = plane_detrended_std(a)
    if reference < 1e-8:
        raise ValueError("degenerate patch: relative comparisons undefined")
    result = {"high_resolution": {"pixels": int(a.size), "detrended_relief_sd_m": reference}}
    for n in (2, 4, 8, 16):
        coarse = plane_detrended_std(block_means(a, n))
        samples = [plane_detrended_std(point_sample(a, n, py, px)) for py in PHASES for px in PHASES]
        result[f"grid_{n}x{n}"] = {
            "sample_count": n * n,
            "block_mean_detrended_relief_sd_m": coarse,
            "block_mean_fraction_of_high_res": coarse / reference,
            "point_sample_phase_count": len(samples),
            "point_sample_detrended_relief_sd_m": {
                "minimum": min(samples), "median": float(np.median(samples)), "maximum": max(samples)},
            "point_sample_fraction_of_high_res": {
                "minimum": min(samples) / reference,
                "median": float(np.median(samples)) / reference,
                "maximum": max(samples) / reference},
        }
    return result

def inspect(path: Path, site: str) -> dict:
    if site not in SITES_TO_TEST:
        raise ValueError("only tile-contained sites supported")
    lat, lon = SITES[site]
    bounds = footprint_bounds(lat, lon, WIDTH_KM)
    with rasterio.open(path) as ds:
        if ds.count != 1 or ds.crs is None or ds.crs.to_epsg() != 4326:
            raise ValueError("expected one EPSG:4326 DEM band")
        if not (ds.bounds.left <= bounds[0] < bounds[2] <= ds.bounds.right and
                ds.bounds.bottom <= bounds[1] < bounds[3] <= ds.bounds.top):
            raise ValueError("patch crosses tile; no silent padding")
        window = from_bounds(*bounds, transform=ds.transform).round_offsets().round_lengths()
        masked = ds.read(1, window=window, masked=True)
        z = np.asarray(masked.data, dtype=float)
        valid = ~np.ma.getmaskarray(masked)
        if ds.nodata is not None:
            valid &= z != ds.nodata
        if not valid.all():
            raise ValueError("nodata in comparison patch; no imputation")
        return {"site": site, "site_lat_lon": [lat, lon], "tile": path.name,
                "sha256": sha256(path), "source": source_url(site),
                "patch_shape": list(z.shape), "valid_fraction": float(valid.mean()),
                "support_width_km": WIDTH_KM, "vertical_units": "metres in derived Skadi HGT",
                "metrics": audit(z)}

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ghats", required=True, type=Path)
    p.add_argument("--ladakh", required=True, type=Path)
    args = p.parse_args()
    sites = [inspect(args.ghats, "western_ghats_lead"), inspect(args.ladakh, "ladakh_lead")]
    print(json.dumps({
        "experiment": "E242 real Earth 30km downsampling aliasing audit",
        "claim_state": "EARTH SAMPLING-DENSITY SENSITIVITY ONLY; E001 NOT YET MEASURED; CROSS-BODY SIMILARITY NOT YET PROVEN",
        "physical_support_km": WIDTH_KM,
        "comparison_rationale": {"lunar_equatorial_4x4_support_km": MOON_EQ_TILE_KM,
                                 "martian_equatorial_2x2_support_km": MARS_EQ_TILE_KM,
                                 "reference": "E212 real-data spherical footprint calculation"},
        "sites": sites,
        "limitations": [
            "Earth tiles are Mapzen Skadi SRTM-derived, not NASADEM or per-pixel provenance audited.",
            "Coarse point samples are NOT instrument point-spread-function simulations.",
            "Block means represent idealized anti-aliasing, not LOLA/MOLA processing.",
            "Only two unvalidated Earth research leads, no positive or negative analogue labels.",
            "2x2 planar detrending has one residual degree of freedom.",
            "No Moon/Mars elevations matched, no labels evaluated, E001 NOT YET MEASURED."
        ]}, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
