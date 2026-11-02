"""E505: bounded, provenance-preserving NOAA ETOPO2022 Earth DEM ingestion.

This is a DEM access/registration test, not a planetary analogue detector.
The N15E075 tile contains Lonar; coordinates are research sample locations,
not labels or independent evidence of analogue quality.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import numpy as np
import tifffile

URL = ("https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/15s/"
       "15s_surface_elev_gtif/ETOPO_2022_v1_15s_N15E075_surface.tif")
MAX_BYTES = 48 * 1024 * 1024
SITES = {"Lonar_candidate": (19.976, 76.508),
         "Deccan_control": (19.5, 75.5),
         "Northern_control": (27.5, 78.5)}


def bounded_download() -> bytes:
    request = Request(URL, headers={"User-Agent": "SpaceApps-E505-EarthDEM/1.0"})
    with urlopen(request, timeout=60) as response:
        if urlparse(response.geturl()).hostname not in {"www.ngdc.noaa.gov", "ngdc.noaa.gov"}:
            raise ValueError("unapproved redirect host")
        data = response.read(MAX_BYTES + 1)
    if not 1024 < len(data) <= MAX_BYTES:
        raise ValueError("unexpected source length")
    if data[:4] not in (b"II*\x00", b"MM\x00*"):
        raise ValueError("source is not classic TIFF")
    return data


def extract(data: bytes) -> dict:
    with tifffile.TiffFile(io.BytesIO(data)) as tf:
        if len(tf.pages) != 1:
            raise ValueError("expected single-band Earth DEM")
        page = tf.pages[0]
        scale_tag = page.tags.get(33550)
        tie_tag = page.tags.get(33922)
        if scale_tag is None or tie_tag is None:
            raise ValueError("missing georeferencing tags")
        sx, sy, _ = map(float, scale_tag.value[:3])
        tie = tuple(map(float, tie_tag.value[:6]))
        if abs(sx - 1/240) > 1e-6 or abs(sy - 1/240) > 1e-6:
            raise ValueError("unexpected 15 arcsecond resolution")
        if abs(tie[3] - 75.0) > sx or abs(tie[4] - 30.0) > sy:
            raise ValueError(f"tile origin differs from N15E075: tie={tie}, scale={(sx,sy)}")
        a = page.asarray()
        if a.ndim != 2 or a.shape not in ((3600, 3600), (3601, 3601)):
            raise ValueError(f"unexpected tile dimensions: {a.shape}")
        if a.dtype.kind not in "fi":
            raise ValueError("non-numeric elevation")
        raster_type = (getattr(tf, "geotiff_metadata", None) or {}).get("GTRasterTypeGeoKey")
        if raster_type not in (None, 1, "RasterPixelIsArea"):
            raise ValueError("pixel-is-point requires separate coordinate handling")
        finite = np.isfinite(a)
        if not finite.any():
            raise ValueError("no finite elevations")
        sites = {}
        for name, (lat, lon) in SITES.items():
            # TIFF tiepoint is at the upper-left pixel corner for PixelIsArea.
            row = round((tie[4] - lat) / sy - 0.5)
            col = round((lon - tie[3]) / sx - 0.5)
            if not (2 <= row < a.shape[0] - 2 and 2 <= col < a.shape[1] - 2):
                raise ValueError("sample outside valid 5x5 window")
            patch = a[row-2:row+3, col-2:col+3]
            if not np.isfinite(patch).all():
                raise ValueError("non-finite sample patch")
            sites[name] = {
                "requested_lat_lon_deg": [lat, lon],
                "center_row_col": [row, col],
                "center_lat_lon_deg": [tie[4] - (row+0.5)*sy, tie[3] + (col+0.5)*sx],
                "elevation_m": patch.astype(float).tolist(),
            }
        return {"shape": list(a.shape), "dtype": str(a.dtype),
                "finite_cells": int(finite.sum()),
                "min_elevation_m": float(np.min(a[finite])),
                "max_elevation_m": float(np.max(a[finite])),
                "pixel_scale_deg": [sx, sy], "tiepoint": list(tie),
                "raster_type": str(raster_type), "sites": sites}


def run(output: str = "e505_earth_dem.json") -> dict:
    raw = bounded_download()
    result = extract(raw)
    result.update({"source_url": URL, "source_sha256": hashlib.sha256(raw).hexdigest(),
                   "source_bytes": len(raw),
                   "source": "NOAA NCEI ETOPO2022 surface elevation, 15 arcsec",
                   "units": "metres; ETOPO elevation datum, NOT Mars areoid or lunar radius",
                   "claim": "Earth DEM acquisition/registration only; E001 NOT YET MEASURED"})
    Path(output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    import sys
    result = run(sys.argv[1] if len(sys.argv) > 1 else "e505_earth_dem.json")
    print(json.dumps({k: v for k, v in result.items() if k != "sites"}, sort_keys=True))
