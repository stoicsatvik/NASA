"""E221: preregistered ±500m coordinate-jitter audit on real SRTM-derived Earth tiles.

Research leads are NOT analogue labels. This measures descriptor instability only.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from research.e214_earth_dem_site_qc import SITES, R, square_bounds, physical_metrics, sha256, source_url

OFFSETS_KM = (-0.5, -0.25, 0.0, 0.25, 0.5)  # fixed before real-data inspection
WIDTHS_KM = (2.0, 4.0)
FEATURES = ("plane_detrended_relief_std_m", "slope_p90_dimensionless")


def shift_coordinate(lat: float, lon: float, east_km: float, north_km: float) -> tuple[float, float]:
    if not all(map(math.isfinite, (lat, lon, east_km, north_km))) or abs(lat) >= 89:
        raise ValueError("invalid coordinate or shift")
    lat2 = lat + math.degrees(north_km * 1000 / R)
    lon2 = lon + math.degrees(east_km * 1000 / (R * math.cos(math.radians(lat))))
    return lat2, lon2


def window_metrics(ds, lat: float, lon: float, width_km: float) -> dict:
    if ds.count != 1 or ds.crs is None or ds.crs.to_epsg() != 4326:
        raise ValueError("unexpected source bands/CRS")
    west, south, east, north = square_bounds(lat, lon, width_km)
    if not (ds.bounds.left <= west < east <= ds.bounds.right and
            ds.bounds.bottom <= south < north <= ds.bounds.top):
        raise ValueError("window crosses tile boundary: adjacent tile required")
    win = from_bounds(west, south, east, north, transform=ds.transform).round_offsets().round_lengths()
    sample = ds.read(1, window=win, masked=True)
    z = np.asarray(sample.data, dtype=float)
    valid = ~np.ma.getmaskarray(sample)
    if ds.nodata is not None:
        valid &= z != ds.nodata
    dx = abs(ds.transform.a) * math.pi / 180 * R * math.cos(math.radians(lat))
    dy = abs(ds.transform.e) * math.pi / 180 * R
    return physical_metrics(z, valid, dx, dy)


def analyze(paths: dict[str, Path]) -> dict:
    if set(paths) != set(SITES):
        raise ValueError("exactly three preregistered site tiles required")
    rows = []
    sources = {}
    for site in sorted(SITES):
        path = paths[site]
        lat, lon = SITES[site]
        sources[site] = {"url": source_url(site), "sha256": sha256(path),
                         "site_lat_lon": [lat, lon], "source": "Mapzen Skadi SRTM-derived HGT; no per-pixel provenance"}
        with rasterio.open(path) as ds:
            for width in WIDTHS_KM:
                for north in OFFSETS_KM:
                    for east in OFFSETS_KM:
                        shifted_lat, shifted_lon = shift_coordinate(lat, lon, east, north)
                        metrics = window_metrics(ds, shifted_lat, shifted_lon, width)
                        rows.append({"site": site, "window_km": width, "east_offset_km": east,
                                     "north_offset_km": north, "features": {f: metrics[f] for f in FEATURES},
                                     "valid_fraction": metrics["valid_fraction"]})
    summaries = {}
    for site in sorted(SITES):
        summaries[site] = {}
        for width in WIDTHS_KM:
            subset = [r for r in rows if r["site"] == site and r["window_km"] == width]
            center = next(r for r in subset if r["east_offset_km"] == 0 and r["north_offset_km"] == 0)
            summaries[site][str(width)] = {}
            for f in FEATURES:
                vals = np.asarray([r["features"][f] for r in subset])
                ref = center["features"][f]
                summaries[site][str(width)][f] = {
                    "center": ref, "min": float(vals.min()), "max": float(vals.max()),
                    "median": float(np.median(vals)), "std": float(np.std(vals)),
                    "coefficient_of_variation": float(np.std(vals) / np.mean(vals)) if np.mean(vals) else None,
                    "max_abs_relative_change_from_center": float(np.max(np.abs(vals - ref)) / abs(ref)) if ref else None,
                }
    rank_audit = {}
    for width in WIDTHS_KM:
        for f in FEATURES:
            key = f"{width}km/{f}"
            orders = []
            for north in OFFSETS_KM:
                for east in OFFSETS_KM:
                    selected = [r for r in rows if r["window_km"] == width and
                                r["east_offset_km"] == east and r["north_offset_km"] == north]
                    orders.append(tuple(r["site"] for r in sorted(selected, key=lambda r: (-r["features"][f], r["site"]))))
            center_index = OFFSETS_KM.index(0.0) * len(OFFSETS_KM) + OFFSETS_KM.index(0.0)
            rank_audit[key] = {"center_order_descending": list(orders[center_index]),
                               "distinct_orders": len(set(orders)),
                               "fraction_offsets_different_from_center": sum(o != orders[center_index] for o in orders) / len(orders),
                               "orders": {" > ".join(order): orders.count(order) for order in sorted(set(orders))}}
    return {"experiment": "E221 real Earth SRTM-derived geolocation jitter sensitivity",
            "claim_state": "DESCRIPTOR SENSITIVITY ONLY; E001 NOT YET MEASURED; CROSS-BODY SIMILARITY NOT YET PROVEN",
            "preregistered_offsets_km": list(OFFSETS_KM), "preregistered_window_km": list(WIDTHS_KM),
            "sources": sources, "observations": len(rows), "window_measurements": rows, "summaries": summaries, "rank_audit": rank_audit,
            "limitations": ["Research lead coordinates are not independently validated analogue labels.",
                "Mapzen HGT is SRTM-derived/mosaicked, not direct NASADEM or per-pixel instrument evidence.",
                "Nearby shifted windows overlap and are NOT independent replicates or uncertainty confidence intervals.",
                "Offset magnitude is an analyst sensitivity choice, NOT measured geolocation error.",
                "No lunar/Martian site recovery, analogue detection, or novel discovery was performed."]}


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("lonar", "ghats", "ladakh"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    paths = {"lonar_lead": args.lonar, "western_ghats_lead": args.ghats, "ladakh_lead": args.ladakh}
    print(json.dumps(analyze(paths), indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
