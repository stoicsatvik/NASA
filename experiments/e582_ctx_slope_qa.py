"""E582: source-backed metre inference, multi-baseline slope and CTX QA metrics.

The source raster is held in memory only. The unit inference is explicitly
separated from missing TIFF/STAC band-unit metadata.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
from pathlib import Path

import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.windows import Window

from experiments.e581_ctx_cog_pixel_sample import (
    API_URL,
    COLLECTION,
    ITEM_ID,
    MAX_RASTER_BYTES,
    MAX_SEARCH_BYTES,
    ProbeError,
    build_search_payload,
    fetch_bounded,
    parse_item,
    safe_url_summary,
    validate_public_url,
)

VERTICAL_UNIT_INFERENCE = "m"
VERTICAL_UNIT_SOURCE = (
    "documented processing chain: ASP point2dem DEM heights are in metres; "
    "USGS CTX processing applies dem_geoid to express heights relative to the Mars areoid. "
    "This is not encoded in this COG's band-unit metadata."
)
SLOPE_BASELINES = ("adjacent_pixel", "approximately_200m")


def summarize_numeric(values: np.ndarray) -> dict:
    values = np.asarray(values, dtype="float64")
    values = values[np.isfinite(values)]
    if values.size == 0:
        return {"valid_count": 0, "mean": None, "median": None, "p95": None, "max": None}
    return {
        "valid_count": int(values.size),
        "mean": float(np.mean(values)),
        "median": float(np.percentile(values, 50)),
        "p95": float(np.percentile(values, 95)),
        "max": float(np.max(values)),
    }


def slope_adjacent(masked: np.ma.MaskedArray, dx: float, dy: float) -> dict:
    data = np.ma.filled(masked, np.nan).astype("float64")
    valid = (~np.ma.getmaskarray(masked)) & np.isfinite(data)
    if data.shape[0] < 2 or data.shape[1] < 2:
        return {"baseline_m": None, **summarize_numeric(np.array([]))}
    dzdx = (data[:-1, 1:] - data[:-1, :-1]) / dx
    dzdy = (data[1:, :-1] - data[:-1, :-1]) / dy
    support = valid[:-1, :-1] & valid[:-1, 1:] & valid[1:, :-1]
    slopes = np.degrees(np.arctan(np.hypot(dzdx[support], dzdy[support])))
    return {"baseline_m": float((dx + dy) / 2.0), **summarize_numeric(slopes)}


def slope_approximately_200m(
    masked: np.ma.MaskedArray, dx: float, dy: float, half_span_pixels: int = 5
) -> dict:
    data = np.ma.filled(masked, np.nan).astype("float64")
    valid = (~np.ma.getmaskarray(masked)) & np.isfinite(data)
    k = half_span_pixels
    if data.shape[0] <= 2 * k or data.shape[1] <= 2 * k:
        return {"baseline_m": float(2 * k * (dx + dy) / 2.0), **summarize_numeric(np.array([]))}
    left = data[k:-k, :-2*k]
    right = data[k:-k, 2*k:]
    top = data[:-2*k, k:-k]
    bottom = data[2*k:, k:-k]
    support = (
        valid[k:-k, :-2*k]
        & valid[k:-k, 2*k:]
        & valid[:-2*k, k:-k]
        & valid[2*k:, k:-k]
    )
    dzdx = (right - left) / (2 * k * dx)
    dzdy = (bottom - top) / (2 * k * dy)
    slopes = np.degrees(np.arctan(np.hypot(dzdx[support], dzdy[support])))
    return {
        "baseline_m": float(2 * k * (dx + dy) / 2.0),
        **summarize_numeric(slopes),
    }


def parse_qa_metrics(payload: bytes) -> dict:
    digest = hashlib.sha256(payload).hexdigest()
    text = payload.decode("utf-8", errors="replace")
    metrics = {}
    # First try simple key/value text lines.
    for line in text.splitlines():
        match = re.match(
            r"^\s*([A-Za-z][A-Za-z0-9 _./()-]{0,80}?)\s*[:=]\s*"
            r"(-?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*$",
            line,
        )
        if match:
            key = re.sub(r"[^a-z0-9]+", "_", match.group(1).strip().lower()).strip("_")
            metrics[key] = float(match.group(2))
    # Then try a one-row CSV if no key/value metrics were found.
    if not metrics:
        try:
            rows = list(csv.DictReader(io.StringIO(text)))
            if rows:
                for key, value in rows[0].items():
                    if key and value:
                        try:
                            metrics[re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_")] = float(value)
                        except ValueError:
                            continue
        except Exception:
            pass
    return {
        "bytes": len(payload),
        "sha256": digest,
        "line_count": len(text.splitlines()),
        "parsed_metrics": metrics,
        "raw_text_stored": False,
        "parsed_any_numeric_metric": bool(metrics),
    }


def inspect_raster(payload: bytes, item_summary: dict, dtm_asset: dict) -> dict:
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
            linear_units = getattr(crs, "linear_units", None) if crs else None
            if not isinstance(linear_units, str) or linear_units.lower() not in {
                "metre", "meter", "meters", "metres", "m"
            }:
                raise ProbeError(f"horizontal CRS units are not metres: {linear_units!r}")

            # Keep direct metadata separate from the source-derived vertical-unit inference.
            bands = dtm_asset.get("raster:bands")
            bands = bands if isinstance(bands, list) else []
            stac_band_unit = bands[0].get("unit") if bands and isinstance(bands[0], dict) else None
            tif_band_units = list(dataset.units)
            metadata_unit_present = bool(stac_band_unit) or any(
                isinstance(value, str) and value.strip() for value in tif_band_units
            )
            dx, dy = abs(float(dataset.res[0])), abs(float(dataset.res[1]))

            windows = []
            centers = [
                (width // 4, height // 2, "west_mid"),
                (width // 2, height // 2, "center"),
                (3 * width // 4, height // 2, "east_mid"),
                (width // 2, height // 4, "north_mid"),
                (width // 2, 3 * height // 4, "south_mid"),
            ]
            for center_col, center_row, label in centers:
                col_off = max(0, min(width - 64, center_col - 32))
                row_off = max(0, min(height - 64, center_row - 32))
                window = Window(col_off, row_off, min(64, width), min(64, height))
                masked = dataset.read(1, window=window, masked=True).astype("float64")
                values = masked.compressed()
                total = int(masked.size)
                valid_count = int(values.size)
                slope20 = slope_adjacent(masked, dx, dy)
                slope200 = slope_approximately_200m(masked, dx, dy, half_span_pixels=5)
                windows.append({
                    "label": label,
                    "row_off": int(row_off),
                    "col_off": int(col_off),
                    "window_shape": [int(window.height), int(window.width)],
                    "valid_count": valid_count,
                    "nodata_fraction": (1.0 - valid_count / total) if total else None,
                    "elevation_unit": VERTICAL_UNIT_INFERENCE,
                    "elevation_unit_source": "documented_processing_chain_inference",
                    "raw_value_min": float(np.min(values)) if valid_count else None,
                    "raw_value_max": float(np.max(values)) if valid_count else None,
                    "raw_value_mean": float(np.mean(values)) if valid_count else None,
                    "slope_adjacent_pixel": slope20,
                    "slope_approximately_200m": slope200,
                })

            wkt = crs.to_wkt() if crs else None
            return {
                "driver": dataset.driver,
                "width": width,
                "height": height,
                "band_count": dataset.count,
                "dtype": dataset.dtypes[0] if dataset.count else None,
                "nodata": dataset.nodata,
                "stac_band_unit": stac_band_unit,
                "geotiff_band_units": tif_band_units,
                "vertical_unit": VERTICAL_UNIT_INFERENCE,
                "vertical_unit_source": VERTICAL_UNIT_SOURCE,
                "vertical_unit_metadata_present": metadata_unit_present,
                "horizontal_crs_linear_units": linear_units,
                "crs_epsg": crs.to_epsg() if crs else None,
                "crs_wkt_sha256": hashlib.sha256(wkt.encode("utf-8")).hexdigest() if wkt else None,
                "transform_gdal": transform,
                "resolution_m": [dx, dy],
                "stac_shape_matches_raster": shape_matches,
                "stac_transform_matches_raster": transform_matches,
                "is_tiled": dataset.is_tiled,
                "block_shapes": [list(shape) for shape in dataset.block_shapes],
                "compression": dataset.compression.value if dataset.compression else None,
                "slope_baselines": list(SLOPE_BASELINES),
                "sample_windows": windows,
                "valid_pixels_sampled": sum(item["valid_count"] for item in windows),
                "slope_note": (
                    "Slope values depend on documented metre inference; short-baseline slopes "
                    "are highly sensitive to 3-5 m vertical precision and are not route-safety results."
                ),
            }


def audit() -> dict:
    receipt = {
        "experiment": "E582",
        "collection": COLLECTION,
        "pinned_item_id": ITEM_ID,
        "vertical_unit_inference": VERTICAL_UNIT_SOURCE,
        "credentials_used": False,
        "raw_item_json_stored": False,
        "raw_raster_stored": False,
        "raw_pixel_arrays_stored": False,
        "raw_qa_text_stored": False,
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
    receipt["search_url"] = safe_url_summary(search["final_url"])
    if search["status"] != 200 or search["too_large"]:
        receipt["decision"] = "STAC_SEARCH_FAILURE_OR_CAP"
        return receipt

    document = json.loads(search["payload"].decode("utf-8"))
    item_summary, dtm_href, dtm_asset = parse_item(document)
    receipt["item"] = item_summary
    assets = document["features"][0].get("assets")
    assets = assets if isinstance(assets, dict) else {}
    qa_asset = assets.get("qa_metrics")
    qa_result = {"decision": "QA_ASSET_NOT_PRESENT"}
    if isinstance(qa_asset, dict) and isinstance(qa_asset.get("href"), str):
        qa_href = qa_asset["href"]
        validate_public_url(qa_href)
        qa_response = fetch_bounded(qa_href, max_bytes=1_000_000)
        qa_result = {
            "decision": "QA_ASSET_ACQUIRED" if qa_response["status"] == 200 and not qa_response["too_large"] else "QA_ASSET_ACCESS_FAILURE",
            "http_status": qa_response["status"],
            "content_type": qa_response["headers"].get("Content-Type"),
            "url": safe_url_summary(qa_response["final_url"]),
        }
        if qa_response["status"] == 200 and not qa_response["too_large"]:
            qa_result.update(parse_qa_metrics(qa_response["payload"]))
    receipt["qa_metrics"] = qa_result

    raster = fetch_bounded(dtm_href, max_bytes=MAX_RASTER_BYTES)
    receipt["raster_http_status"] = raster["status"]
    receipt["raster_bytes_read"] = raster["bytes_read"]
    receipt["raster_declared_bytes"] = raster.get("declared_bytes")
    receipt["raster_content_type"] = raster["headers"].get("Content-Type")
    receipt["raster_url"] = safe_url_summary(raster["final_url"])
    if raster["status"] != 200 or raster["too_large"]:
        receipt["decision"] = "DTM_DOWNLOAD_FAILURE_OR_CAP"
        return receipt

    receipt["raster_sha256"] = hashlib.sha256(raster["payload"]).hexdigest()
    receipt["raster_inspection"] = inspect_raster(raster["payload"], item_summary, dtm_asset)
    receipt["decision"] = "SLOPE_AND_QA_SAMPLED"
    return receipt


def summarize_receipt(receipt: dict) -> dict:
    inspection = receipt.get("raster_inspection")
    if not isinstance(inspection, dict):
        inspection = {}
    qa = receipt.get("qa_metrics")
    if not isinstance(qa, dict):
        qa = {}
    return {
        "experiment": receipt.get("experiment", "E582"),
        "decision": receipt.get("decision"),
        "item_id": (receipt.get("item") or {}).get("id") if isinstance(receipt.get("item"), dict) else None,
        "raster_sha256": receipt.get("raster_sha256"),
        "valid_pixels_sampled": inspection.get("valid_pixels_sampled", 0),
        "vertical_unit": inspection.get("vertical_unit"),
        "vertical_unit_metadata_present": inspection.get("vertical_unit_metadata_present"),
        "slope_baselines": inspection.get("slope_baselines", []),
        "qa_decision": qa.get("decision"),
        "qa_metrics_parsed": qa.get("parsed_any_numeric_metric", False),
        "credentials_used": False,
        "raw_raster_stored": False,
        "raw_pixel_arrays_stored": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(".artifacts/e582/ctx-slope-qa-summary.json"))
    args = parser.parse_args()
    try:
        receipt = audit()
    except Exception as error:
        receipt = {
            "experiment": "E582",
            "pinned_item_id": ITEM_ID,
            "decision": "ACQUISITION_OR_ANALYSIS_ERROR",
            "error_type": type(error).__name__,
            "error_message": str(error)[:300],
            "credentials_used": False,
            "raw_raster_stored": False,
            "raw_pixel_arrays_stored": False,
            "raw_qa_text_stored": False,
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summarize_receipt(receipt), sort_keys=True))


if __name__ == "__main__":
    main()
