from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlsplit

import numpy as np
import rasterio
import requests
from rasterio.errors import RasterioIOError
from rasterio.windows import Window
from rasterio.warp import transform as reproject_xy

BUCKET_HOST = "copernicus-dem-30m.s3.eu-central-1.amazonaws.com"
BASE_URL = f"https://{BUCKET_HOST}/"
RESOLUTION_TOKEN = "10"
WINDOW = 17
HEADER_RANGE_BYTES = 16_384
MAX_TILE_BYTES = 100_000_000
MAX_BLOCK_UNCOMPRESSED_BYTES = 8_000_000
USER_AGENT = "Unified-Parallel-Foundry-E557/1.0"

SITES = (
    {
        "site_id": "lonar_literature_lead",
        "latitude": 19.9750,
        "longitude": 76.5090,
        "role": "literature_lead_not_validated_positive",
    },
    {
        "site_id": "nearby_local_comparison_point",
        "latitude": 19.8000,
        "longitude": 76.3000,
        "role": "nearby_comparison_not_negative_label",
    },
)


class E557Error(RuntimeError):
    def __init__(self, outcome: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.outcome = outcome
        self.details = details or {}


def tile_stem(latitude: float, longitude: float) -> str:
    if not (-90 <= latitude < 90) or not (-180 <= longitude < 180):
        raise ValueError("coordinate outside geographic tile grid")
    south = math.floor(latitude)
    west = math.floor(longitude)
    ns = "N" if south >= 0 else "S"
    ew = "E" if west >= 0 else "W"
    return f"Copernicus_DSM_COG_{RESOLUTION_TOKEN}_{ns}{abs(south):02d}_00_{ew}{abs(west):03d}_00_DEM"


def tile_url(latitude: float, longitude: float) -> str:
    stem = tile_stem(latitude, longitude)
    return f"{BASE_URL}{stem}/{stem}.tif"


def validate_tile_url(url: str, expected_stem: str) -> str:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != BUCKET_HOST
        or parsed.port not in (None, 443)
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path != f"/{expected_stem}/{expected_stem}.tif"
    ):
        raise E557Error("URL_OUTSIDE_ALLOWLIST", "Copernicus URL is outside the exact public tile allowlist")
    return url


def parse_content_range(value: str | None) -> tuple[int, int, int]:
    if not value or not value.startswith("bytes "):
        raise E557Error("CONTENT_RANGE_MISSING", "Range response omitted Content-Range")
    try:
        span, total = value[6:].split("/", 1)
        start, end = span.split("-", 1)
        parsed = (int(start), int(end), int(total))
    except (ValueError, TypeError) as error:
        raise E557Error("CONTENT_RANGE_INVALID", "Content-Range is malformed") from error
    if min(parsed) < 0 or parsed[1] < parsed[0] or parsed[2] <= parsed[1]:
        raise E557Error("CONTENT_RANGE_INVALID", "Content-Range bounds are inconsistent")
    return parsed


def verify_header(session, url: str) -> dict:
    head = session.head(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
        timeout=(15, 45),
        allow_redirects=False,
    )
    if head.status_code in (301, 302, 303, 307, 308):
        raise E557Error("REDIRECT_REFUSED", "Public tile HEAD redirected; redirects are not followed")
    if head.status_code == 404:
        raise E557Error("TILE_NOT_PUBLISHED", "The exact public GLO-30 tile returned HTTP 404")
    if head.status_code == 403:
        raise E557Error("TILE_FORBIDDEN", "The exact public GLO-30 tile returned HTTP 403")
    if head.status_code != 200:
        raise E557Error(f"HEAD_HTTP_{head.status_code}", "Copernicus tile HEAD did not return HTTP 200")
    if head.url != url:
        raise E557Error("HEAD_URL_CHANGED", "HEAD response URL differs from the exact tile URL")
    length = head.headers.get("Content-Length")
    if not length or not length.isdigit():
        raise E557Error("TILE_LENGTH_UNKNOWN", "Copernicus tile did not declare a valid Content-Length")
    size = int(length)
    if size <= 0 or size > MAX_TILE_BYTES:
        raise E557Error("TILE_SIZE_OUTSIDE_BUDGET", "Copernicus tile size is outside the configured safety bound")
    if head.headers.get("Accept-Ranges", "").lower() != "bytes":
        raise E557Error("RANGE_NOT_ADVERTISED", "Copernicus tile did not advertise byte-range support")
    return {
        "http_status": head.status_code,
        "content_length_bytes": size,
        "accept_ranges": head.headers.get("Accept-Ranges"),
        "content_type": head.headers.get("Content-Type"),
        "etag": head.headers.get("ETag"),
        "last_modified": head.headers.get("Last-Modified"),
    }


def read_header_range(session, url: str, expected_size: int) -> dict:
    response = session.get(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "identity",
            "Range": f"bytes=0-{HEADER_RANGE_BYTES - 1}",
        },
        timeout=(15, 45),
        allow_redirects=False,
        stream=True,
    )
    try:
        if response.status_code in (301, 302, 303, 307, 308):
            raise E557Error("REDIRECT_REFUSED", "Range request redirected; redirects are not followed")
        if response.status_code == 200:
            raise E557Error("RANGE_IGNORED", "Server ignored Range; response body was not consumed")
        if response.status_code != 206:
            raise E557Error(f"RANGE_HTTP_{response.status_code}", "Copernicus header range did not return HTTP 206")
        if response.url != url:
            raise E557Error("RANGE_URL_CHANGED", "Range response URL differs from the exact tile URL")
        start, end, total = parse_content_range(response.headers.get("Content-Range"))
        if (start, end, total) != (0, HEADER_RANGE_BYTES - 1, expected_size):
            raise E557Error("CONTENT_RANGE_MISMATCH", "Header range does not match the exact requested span/tile size")
        body = response.raw.read(HEADER_RANGE_BYTES + 1, decode_content=False)
        if len(body) != HEADER_RANGE_BYTES:
            raise E557Error("HEADER_BODY_LENGTH_MISMATCH", "Header range body has an unexpected length")
        if body[:4] not in (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"):
            raise E557Error("TIFF_SIGNATURE_INVALID", "The bounded tile prefix is not a TIFF/BigTIFF header")
        return {
            "http_status": 206,
            "content_range": response.headers.get("Content-Range"),
            "bytes_read": len(body),
            "prefix_sha256": hashlib.sha256(body).hexdigest(),
            "tiff_signature": body[:4].hex(),
        }
    finally:
        response.close()


def _pixel_spacing_m(dataset, latitude: float) -> tuple[float, float]:
    x_size = abs(float(dataset.transform.a))
    y_size = abs(float(dataset.transform.e))
    if dataset.crs and dataset.crs.is_geographic:
        lat = math.radians(latitude)
        dx = x_size * (111412.84 * math.cos(lat) - 93.5 * math.cos(3 * lat))
        dy = y_size * (111132.92 - 559.82 * math.cos(2 * lat) + 1.175 * math.cos(4 * lat))
        return dx, dy
    return x_size, y_size


def summarize_window(values, latitude: float, pixel_spacing: tuple[float, float]) -> dict:
    masked = np.ma.masked_invalid(np.ma.asarray(values, dtype=np.float64))
    valid = np.asarray(masked.compressed(), dtype=np.float64)
    total = int(masked.size)
    result = {
        "window_shape": [int(masked.shape[0]), int(masked.shape[1])],
        "valid_samples": int(valid.size),
        "masked_or_nonfinite_samples": int(total - valid.size),
        "raw_window_retained": False,
        "pixel_spacing_approx_m": {"east_west": pixel_spacing[0], "north_south": pixel_spacing[1]},
    }
    if valid.size == 0:
        result["outcome"] = "NO_VALID_SAMPLES"
        return result
    result.update({
        "elevation_min_m": float(np.min(valid)),
        "elevation_median_m": float(np.median(valid)),
        "elevation_mean_m": float(np.mean(valid)),
        "elevation_population_sd_m": float(np.std(valid)),
        "elevation_max_m": float(np.max(valid)),
        "local_relief_m": float(np.max(valid) - np.min(valid)),
    })
    center = np.ma.filled(masked, np.nan)
    mid_r, mid_c = center.shape[0] // 2, center.shape[1] // 2
    slope = None
    if (
        center.shape[0] >= 3
        and center.shape[1] >= 3
        and np.isfinite(center[mid_r - 1:mid_r + 2, mid_c - 1:mid_c + 2]).all()
    ):
        dx, dy = pixel_spacing
        gy, gx = np.gradient(center, dy, dx)
        slope = float(np.degrees(np.arctan(np.hypot(gx[mid_r, mid_c], gy[mid_r, mid_c]))))
    result["central_slope_deg"] = slope
    return result


def sample_site(dataset, site: dict, max_block_bytes: int = MAX_BLOCK_UNCOMPRESSED_BYTES) -> dict:
    latitude = float(site["latitude"])
    longitude = float(site["longitude"])
    if dataset.crs is None:
        raise E557Error("CRS_MISSING", "Copernicus tile has no CRS")
    if dataset.crs.to_epsg() == 4326 or dataset.crs.is_geographic:
        x, y = longitude, latitude
    else:
        xs, ys = reproject_xy("EPSG:4326", dataset.crs, [longitude], [latitude])
        x, y = xs[0], ys[0]
    row, col = dataset.index(x, y)
    half = WINDOW // 2
    row0, col0 = row - half, col - half
    row1, col1 = row + half + 1, col + half + 1
    if row0 < 0 or col0 < 0 or row1 > dataset.height or col1 > dataset.width:
        raise E557Error("WINDOW_OUTSIDE_TILE", "Frozen sample window crosses the raster boundary")
    block_h, block_w = dataset.block_shapes[0]
    rows_touched = set(range(row0 // block_h, (row1 - 1) // block_h + 1))
    cols_touched = set(range(col0 // block_w, (col1 - 1) // block_w + 1))
    blocks = len(rows_touched) * len(cols_touched)
    bytes_per_sample = max(1, int(dataset.dtypes[0].replace("int", "").replace("uint", "").replace("float", "")) // 8)
    block_uncompressed = block_h * block_w * bytes_per_sample
    if blocks * block_uncompressed > max_block_bytes:
        raise E557Error(
            "BLOCK_READ_BUDGET_EXCEEDED",
            "The COG blocks required for this window exceed the uncompressed read budget",
            {"blocks": blocks, "block_uncompressed_bytes": block_uncompressed, "budget_bytes": max_block_bytes},
        )
    window = Window(col0, row0, WINDOW, WINDOW)
    values = dataset.read(1, window=window, masked=True)
    dx, dy = _pixel_spacing_m(dataset, latitude)
    summary = summarize_window(values, latitude, (dx, dy))
    summary.update({
        "site_id": site["site_id"],
        "site_role": site["role"],
        "latitude": latitude,
        "longitude": longitude,
        "pixel_row": int(row),
        "pixel_column": int(col),
        "window_extent_approx_m": {
            "east_west": (WINDOW - 1) * dx,
            "north_south": (WINDOW - 1) * dy,
        },
        "blocks_touched": blocks,
        "block_shape": [int(block_h), int(block_w)],
        "block_uncompressed_bytes": int(block_uncompressed),
    })
    return summary


def run() -> dict:
    session = requests.Session()
    site0 = SITES[0]
    stem = tile_stem(float(site0["latitude"]), float(site0["longitude"]))
    url = validate_tile_url(tile_url(float(site0["latitude"]), float(site0["longitude"])), stem)
    try:
        head = verify_header(session, url)
        prefix = read_header_range(session, url, head["content_length_bytes"])
        with rasterio.Env(
            GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
            CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
            CPL_VSIL_CURL_USE_HEAD="YES",
            CPL_VSIL_CURL_CACHE_SIZE="0",
            CPL_VSIL_CURL_CHUNK_SIZE="16384",
            GDAL_HTTP_MAX_RETRY="0",
        ):
            with rasterio.open(f"/vsicurl/{url}") as dataset:
                if not dataset.is_tiled:
                    raise E557Error("COG_NOT_TILED", "Raster is not tiled; bounded window access is not accepted")
                if dataset.width < 3600 or dataset.height < 3600:
                    raise E557Error("RASTER_DIMENSIONS_UNEXPECTED", "Raster dimensions are smaller than the expected 1-degree GLO-30 tile")
                if dataset.compression is None:
                    compression = None
                else:
                    compression = str(dataset.compression)
                samples = [sample_site(dataset, site) for site in SITES]
                metadata = {
                    "crs": str(dataset.crs),
                    "epsg": dataset.crs.to_epsg() if dataset.crs else None,
                    "width": int(dataset.width),
                    "height": int(dataset.height),
                    "transform": [float(v) for v in dataset.transform[:6]],
                    "dtype": dataset.dtypes[0],
                    "units": dataset.units[0] if dataset.units else None,
                    "nodata": dataset.nodata,
                    "is_tiled": bool(dataset.is_tiled),
                    "block_shapes": [[int(a), int(b)] for a, b in dataset.block_shapes],
                    "compression": compression,
                    "overview_levels": [int(v) for v in dataset.overviews(1)],
                    "dataset_tags": {k: v for k, v in dataset.tags().items() if k.lower() in {"area_or_point", "product", "source", "version"}},
                }
        return {
            "experiment": "E557 Copernicus GLO-30 public COG sample at Maharashtra analogue literature lead",
            "outcome": "PUBLIC_COG_RANGE_ACCESS_AND_WINDOW_SAMPLE_SUPPORTED",
            "source": {
                "product": "Copernicus DEM GLO-30 Public (2021 release)",
                "publisher": "European Union / ESA Copernicus",
                "bucket": "copernicus-dem-30m",
                "region": "eu-central-1",
                "tile_stem": stem,
                "url": url,
                "license": "Copernicus Licence; attribution required",
                "nominal_resolution": "1 arc-second, approximately 30 m",
                "surface_semantics": "Digital Surface Model (DSM), not a bare-earth DTM",
                "acquisition": "TanDEM-X mission observations from 2011–2015; static 2021 public release",
                "public_access": "anonymous AWS Open Data bucket; no account or API key",
            },
            "access": {
                "head": head,
                "header_range": prefix,
                "full_tile_downloaded": False,
                "raw_tile_retained": False,
                "network_bytes_for_rasterio_window_reads": "NOT EXACTLY MEASURED",
                "rasterio_window_access": "COG tiled block reads; per-window block counts recorded",
            },
            "raster_metadata": metadata,
            "samples": samples,
            "claim_boundary": {
                "public_earth_dem_access": "SUPPORTED for the exact N19/E076 GLO-30 tile",
                "lonar_literature_lead": "NOT A VALIDATED POSITIVE LABEL",
                "nearby_comparison_point": "NOT A VALIDATED NEGATIVE LABEL",
                "terrain_statistics": "MEASURED DESCRIPTIVE DSM WINDOWS ONLY",
                "cross_body_similarity": "NOT YET PROVEN",
                "known_site_recovery": "NOT YET MEASURED",
                "novel_analogue_discovery": "NOT YET PROVEN",
                "local_validation_advantage": "NOT YET PROVEN",
            },
            "limitations": [
                "A 17×17 patch at each point is a descriptive sample, not a site-level terrain distribution.",
                "GLO-30 is a DSM and may include vegetation/buildings; it is not directly interchangeable with bare planetary topography.",
                "The two points do not form independent positive/negative labels.",
                "No MOLA/CTX/HiRISE co-registration, physical-footprint aggregation, E001 ranking or route-safety analysis is performed.",
                "The exact network transfer used by GDAL is not measured; only the bounded header-range bytes and touched COG blocks are reported.",
            ],
            "next_gate": "Verify the GLO-30 DSM semantics and vertical reference against the current product guide; identify a bare-earth/quality-mask path or use this DSM only as a clearly separated auxiliary descriptor, then obtain independent site labels/controls.",
        }
    except E557Error as error:
        return {
            "experiment": "E557 Copernicus GLO-30 public COG sample at Maharashtra analogue literature lead",
            "outcome": error.outcome,
            "message": str(error),
            "details": error.details,
            "source": {
                "product": "Copernicus DEM GLO-30 Public (2021 release)",
                "tile_stem": stem,
                "url": url,
                "public_access": "anonymous AWS Open Data bucket; no account or API key",
            },
            "claim_boundary": {
                "cross_body_similarity": "NOT YET PROVEN",
                "known_site_recovery": "NOT YET MEASURED",
                "novel_analogue_discovery": "NOT YET PROVEN",
                "local_validation_advantage": "NOT YET PROVEN",
            },
            "next_gate": "Preserve the exact access/format failure; do not substitute an unverified tile or infer labels.",
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "experiment": result["experiment"],
        "outcome": result["outcome"],
        "sample_count": len(result.get("samples", [])),
        "tile": result.get("source", {}).get("tile_stem"),
        "file_size": result.get("access", {}).get("head", {}).get("content_length_bytes"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
