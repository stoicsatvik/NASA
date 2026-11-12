"""E581: inspect one pinned Mars CTX DTM COG and sample deterministic pixel windows.

The source raster is downloaded into memory only. No raw raster or pixel array
is persisted; the receipt contains metadata and aggregate window statistics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_URL = "https://stac.astrogeology.usgs.gov/api/search"
COLLECTION = "mro_ctx_controlled_usgs_dtms"
ITEM_ID = "P18_007925_1987_XN_18N282W__P19_008650_1987_XI_18N282W"
MAX_SEARCH_BYTES = 1_000_000
MAX_RASTER_BYTES = 25_000_000
TIMEOUT_SECONDS = 60
SAMPLE_WINDOW = 64
USER_AGENT = "UnifiedParallelFoundry-E581-CTX-COG-sample/1.0"
ALLOWED_HOSTS = {
    "stac.astrogeology.usgs.gov",
    "astrogeo-ard.s3-us-west-2.amazonaws.com",
    "astrogeo-ard.s3.amazonaws.com",
    "astrogeo-ard.s3.us-west-2.amazonaws.com",
    "s3.us-west-2.amazonaws.com",
}


class ProbeError(RuntimeError):
    pass


def build_search_payload() -> dict:
    return {
        "collections": [COLLECTION],
        "ids": [ITEM_ID],
        "limit": 1,
    }


def safe_url_summary(url: str) -> dict:
    parsed = urllib.parse.urlsplit(url)
    return {
        "scheme": parsed.scheme,
        "host": parsed.hostname,
        "path": parsed.path,
        "query_key_names": sorted({
            key.lower()
            for key, _ in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        }),
        "query_values_stored": False,
    }


def validate_public_url(url: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in ALLOWED_HOSTS
        or parsed.username
        or parsed.password
    ):
        raise ProbeError("URL outside pinned public HTTPS host allowlist")


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_bounded(
    url: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict | None = None,
    max_bytes: int,
) -> dict:
    validate_public_url(url)
    request_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json,application/json,image/tiff,*/*",
    }
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    opener = urllib.request.build_opener(SafeRedirectHandler())
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > max_bytes:
                return {
                    "status": response.status,
                    "headers": response.headers,
                    "payload": b"",
                    "bytes_read": 0,
                    "declared_bytes": int(declared),
                    "final_url": response.geturl(),
                    "too_large": True,
                }
            payload = response.read(max_bytes + 1)
            bytes_read = len(payload)
            too_large = bytes_read > max_bytes
            if too_large:
                payload = b""
            final_url = response.geturl()
            validate_public_url(final_url)
            return {
                "status": response.status,
                "headers": response.headers,
                "payload": payload,
                "bytes_read": bytes_read,
                "declared_bytes": int(declared) if declared else None,
                "final_url": final_url,
                "too_large": too_large,
            }
    except urllib.error.HTTPError as error:
        return {
            "status": error.code,
            "headers": error.headers,
            "payload": b"",
            "bytes_read": 0,
            "declared_bytes": None,
            "final_url": error.geturl(),
            "too_large": False,
        }


def parse_item(document: dict) -> tuple[dict, str, dict]:
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise ProbeError("pinned item search did not return a STAC FeatureCollection")
    features = document.get("features")
    if not isinstance(features, list) or len(features) != 1:
        raise ProbeError("pinned item search must return exactly one feature")
    feature = features[0]
    if feature.get("id") != ITEM_ID or feature.get("collection") != COLLECTION:
        raise ProbeError("STAC search returned a different item or collection")
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        properties = {}
    assets = feature.get("assets")
    if not isinstance(assets, dict):
        assets = {}
    dtm = assets.get("dtm")
    if not isinstance(dtm, dict) or not isinstance(dtm.get("href"), str):
        raise ProbeError("pinned item has no DTM asset href")
    href = dtm["href"]
    validate_public_url(href)

    bands = dtm.get("raster:bands")
    if not isinstance(bands, list):
        bands = []
    wkt = properties.get("proj:wkt2")
    summary = {
        "id": feature.get("id"),
        "collection": feature.get("collection"),
        "datetime": properties.get("datetime"),
        "geometry_type": (feature.get("geometry") or {}).get("type"),
        "bbox": feature.get("bbox"),
        "proj_epsg": properties.get("proj:epsg"),
        "proj_shape": properties.get("proj:shape"),
        "proj_transform": properties.get("proj:transform"),
        "proj_wkt2_sha256": hashlib.sha256(wkt.encode("utf-8")).hexdigest() if isinstance(wkt, str) else None,
        "proj_wkt2_present": isinstance(wkt, str) and bool(wkt),
        "dtm_asset_type": dtm.get("type"),
        "dtm_asset_roles": dtm.get("roles"),
        "dtm_raster_bands": bands,
        "asset_keys": sorted(assets.keys()),
        "dtm_href": safe_url_summary(href),
    }
    return summary, href, dtm


def _unit_from_metadata(dataset, asset: dict) -> tuple[str | None, str]:
    stac_bands = asset.get("raster:bands")
    if isinstance(stac_bands, list) and stac_bands and isinstance(stac_bands[0], dict):
        value = stac_bands[0].get("unit")
        if isinstance(value, str) and value.strip():
            return value.strip(), "stac:raster:bands[0].unit"
    units = getattr(dataset, "units", ())
    if units and isinstance(units[0], str) and units[0].strip():
        return units[0].strip(), "GeoTIFF band unit"
    tags = dataset.tags(1)
    for key in ("UNITTYPE", "UNIT", "UNITS", "VERTICAL_UNITS"):
        value = tags.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip(), f"GeoTIFF tag {key}"
    return None, "not reported"


def inspect_geotiff(payload: bytes, item_summary: dict, asset: dict) -> dict:
    try:
        import numpy as np
        import rasterio
        from rasterio.io import MemoryFile
        from rasterio.windows import Window
    except ImportError as error:
        raise ProbeError("rasterio and numpy are required for E581 inspection") from error

    with MemoryFile(payload) as memory_file:
        with memory_file.open() as dataset:
            height, width = dataset.height, dataset.width
            transform = list(dataset.transform.to_gdal())
            stac_shape = item_summary.get("proj_shape")
            stac_transform = item_summary.get("proj_transform")
            shape_matches = stac_shape == [height, width]
            transform_matches = False
            if isinstance(stac_transform, list) and len(stac_transform) == 6:
                transform_matches = all(
                    math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-7)
                    for a, b in zip(stac_transform, transform)
                )

            crs = dataset.crs
            crs_wkt = crs.to_wkt() if crs else None
            linear_units = getattr(crs, "linear_units", None) if crs else None
            vertical_unit, vertical_unit_source = _unit_from_metadata(dataset, asset)
            unit_normalized = vertical_unit.lower().strip() if vertical_unit else ""
            vertical_metres = unit_normalized in {
                "m", "meter", "meters", "metre", "metres"
            }
            horizontal_normalized = linear_units.lower().strip() if isinstance(linear_units, str) else ""
            horizontal_metres = horizontal_normalized in {
                "m", "meter", "meters", "metre", "metres"
            }
            slope_units_confirmed = vertical_metres and horizontal_metres

            windows = []
            centers = [
                (width // 4, height // 2, "west_mid"),
                (width // 2, height // 2, "center"),
                (3 * width // 4, height // 2, "east_mid"),
                (width // 2, height // 4, "north_mid"),
                (width // 2, 3 * height // 4, "south_mid"),
            ]
            dx = abs(float(dataset.res[0]))
            dy = abs(float(dataset.res[1]))
            for center_col, center_row, label in centers:
                col_off = max(0, min(width - SAMPLE_WINDOW, center_col - SAMPLE_WINDOW // 2))
                row_off = max(0, min(height - SAMPLE_WINDOW, center_row - SAMPLE_WINDOW // 2))
                window = Window(col_off, row_off, min(SAMPLE_WINDOW, width), min(SAMPLE_WINDOW, height))
                masked = dataset.read(1, window=window, masked=True).astype("float64")
                values = masked.compressed()
                total = int(masked.size)
                valid_count = int(values.size)
                result = {
                    "label": label,
                    "row_off": int(row_off),
                    "col_off": int(col_off),
                    "height": int(window.height),
                    "width": int(window.width),
                    "valid_count": valid_count,
                    "nodata_fraction": (1.0 - valid_count / total) if total else None,
                    "vertical_unit": vertical_unit or "unknown",
                    "min": float(np.min(values)) if valid_count else None,
                    "max": float(np.max(values)) if valid_count else None,
                    "mean": float(np.mean(values)) if valid_count else None,
                    "std": float(np.std(values, ddof=0)) if valid_count else None,
                    "p05": float(np.percentile(values, 5)) if valid_count else None,
                    "p50": float(np.percentile(values, 50)) if valid_count else None,
                    "p95": float(np.percentile(values, 95)) if valid_count else None,
                    "slope_degrees": None,
                    "slope_p95_degrees": None,
                }
                if slope_units_confirmed and valid_count:
                    array = np.ma.filled(masked, np.nan)
                    gy, gx = np.gradient(array, dy, dx)
                    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
                    finite = slope[np.isfinite(slope)]
                    if finite.size:
                        result["slope_degrees"] = float(np.mean(finite))
                        result["slope_p95_degrees"] = float(np.percentile(finite, 95))
                windows.append(result)

            return {
                "driver": dataset.driver,
                "width": width,
                "height": height,
                "band_count": dataset.count,
                "dtype": dataset.dtypes[0] if dataset.count else None,
                "nodata": dataset.nodata,
                "band_units": list(dataset.units),
                "vertical_unit": vertical_unit or "unknown",
                "vertical_unit_source": vertical_unit_source,
                "vertical_unit_confirmed_metres": vertical_metres,
                "crs_present": crs is not None,
                "crs_epsg": crs.to_epsg() if crs else None,
                "crs_linear_units": linear_units,
                "crs_wkt_sha256": hashlib.sha256(crs_wkt.encode("utf-8")).hexdigest() if crs_wkt else None,
                "transform_gdal": transform,
                "resolution": [dx, dy],
                "bounds": list(dataset.bounds),
                "is_tiled": dataset.is_tiled,
                "block_shapes": [list(shape) for shape in dataset.block_shapes],
                "compression": dataset.compression.value if dataset.compression else None,
                "stac_shape_matches_raster": shape_matches,
                "stac_transform_matches_raster": transform_matches,
                "slope_computed": slope_units_confirmed,
                "sample_windows": windows,
                "valid_pixels_sampled": sum(window["valid_count"] for window in windows),
            }


def audit() -> dict:
    receipt = {
        "experiment": "E581",
        "collection": COLLECTION,
        "pinned_item_id": ITEM_ID,
        "search_url": safe_url_summary(API_URL),
        "search_payload": build_search_payload(),
        "credentials_used": False,
        "raw_item_json_stored": False,
        "raw_raster_stored": False,
        "raw_pixel_arrays_stored": False,
        "decision": "ACQUISITION_NOT_ATTEMPTED",
    }
    search = fetch_bounded(
        API_URL,
        method="POST",
        data=json.dumps(build_search_payload()).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        max_bytes=MAX_SEARCH_BYTES,
    )
    receipt["search_http_status"] = search["status"]
    receipt["search_response_bytes"] = search["bytes_read"]
    receipt["search_final_url"] = safe_url_summary(search["final_url"])
    if search["status"] != 200:
        receipt["decision"] = "STAC_SEARCH_FAILURE"
        return receipt
    if search["too_large"]:
        receipt["decision"] = "STAC_SEARCH_EXCEEDS_1MB_CAP"
        return receipt

    try:
        document = json.loads(search["payload"].decode("utf-8"))
    except Exception as error:
        raise ProbeError("STAC search response is not valid UTF-8 JSON") from error
    item_summary, href, asset = parse_item(document)
    receipt["item"] = item_summary

    raster = fetch_bounded(href, max_bytes=MAX_RASTER_BYTES)
    receipt["raster_http_status"] = raster["status"]
    receipt["raster_content_type"] = raster["headers"].get("Content-Type")
    receipt["raster_declared_bytes"] = raster.get("declared_bytes")
    receipt["raster_bytes_read"] = raster["bytes_read"]
    receipt["raster_url"] = safe_url_summary(raster["final_url"])
    if raster["status"] != 200:
        receipt["decision"] = "DTM_DOWNLOAD_FAILURE"
        return receipt
    if raster["too_large"]:
        receipt["decision"] = "DTM_EXCEEDS_25MB_CAP"
        return receipt

    receipt["raster_sha256"] = hashlib.sha256(raster["payload"]).hexdigest()
    receipt["raster_inspection"] = inspect_geotiff(raster["payload"], item_summary, asset)
    receipt["decision"] = (
        "PINNED_COG_PIXEL_WINDOWS_SAMPLED"
        if receipt["raster_inspection"]["valid_pixels_sampled"] > 0
        else "PINNED_COG_OPENED_NO_VALID_SAMPLE_PIXELS"
    )
    return receipt


def summarize_receipt(receipt: dict) -> dict:
    inspection = receipt.get("raster_inspection")
    if not isinstance(inspection, dict):
        inspection = {}
    item = receipt.get("item")
    if not isinstance(item, dict):
        item = {}
    return {
        "experiment": receipt.get("experiment", "E581"),
        "decision": receipt.get("decision"),
        "item_id": item.get("id"),
        "raster_http_status": receipt.get("raster_http_status"),
        "raster_bytes_read": receipt.get("raster_bytes_read"),
        "raster_sha256": receipt.get("raster_sha256"),
        "shape": [inspection.get("height"), inspection.get("width")] if inspection else None,
        "dtype": inspection.get("dtype"),
        "nodata": inspection.get("nodata"),
        "vertical_unit": inspection.get("vertical_unit"),
        "stac_shape_matches_raster": inspection.get("stac_shape_matches_raster"),
        "stac_transform_matches_raster": inspection.get("stac_transform_matches_raster"),
        "valid_pixels_sampled": inspection.get("valid_pixels_sampled", 0),
        "slope_computed": inspection.get("slope_computed", False),
        "credentials_used": False,
        "raw_raster_stored": False,
        "raw_pixel_arrays_stored": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(".artifacts/e581/ctx-cog-summary.json"))
    args = parser.parse_args()
    try:
        receipt = audit()
    except Exception as error:
        receipt = {
            "experiment": "E581",
            "pinned_item_id": ITEM_ID,
            "decision": "ACQUISITION_OR_INSPECTION_ERROR",
            "error_type": type(error).__name__,
            "error_message": str(error)[:300],
            "credentials_used": False,
            "raw_raster_stored": False,
            "raw_pixel_arrays_stored": False,
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summarize_receipt(receipt), sort_keys=True))


if __name__ == "__main__":
    main()
