"""E586: compare actual CTX product footprints with the Jezero AOI.

The audit uses one bounded public STAC search, pins the returned item set to
E583, stores geometry hashes and derived metrics only, and never stores raw
item JSON, coordinates, signed URLs, rasters, or credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path
from urllib.parse import urlsplit

from shapely.geometry import box, shape
from shapely.ops import transform

try:
    from experiments.e582_ctx_qa_mola_audit import (
        API_URL,
        COLLECTION,
        MAX_SEARCH_BYTES,
        ProbeError,
        fetch_bounded,
        safe_url_summary,
    )
except ModuleNotFoundError as error:
    if error.name != "experiments":
        raise
    from e582_ctx_qa_mola_audit import (
        API_URL,
        COLLECTION,
        MAX_SEARCH_BYTES,
        ProbeError,
        fetch_bounded,
        safe_url_summary,
    )

MARS_RADIUS_M = 3_396_190.0
JEZERO_BBOX = (76.69, 17.41, 78.69, 19.41)
SEARCH_LIMIT = 9
MAX_ITEMS = 9
GEOMETRY_BBOX_TOLERANCE_DEG = 0.01


def validate_bbox(value: object, label: str = "bbox") -> tuple[float, float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError(f"{label} must contain west, south, east, north")
    numbers = []
    for component in value:
        if isinstance(component, bool) or not isinstance(component, (int, float)):
            raise ValueError(f"{label} coordinates must be finite numbers")
        number = float(component)
        if not math.isfinite(number):
            raise ValueError(f"{label} coordinates must be finite numbers")
        numbers.append(number)
    west, south, east, north = numbers
    if not (-180 <= west < east <= 180):
        raise ValueError(f"{label} longitude bounds are invalid")
    if not (-90 <= south < north <= 90):
        raise ValueError(f"{label} latitude bounds are invalid")
    return west, south, east, north


def _equal_area_xy(longitude: float, latitude: float):
    """Spherical cylindrical equal-area projection for Mars (2015) coordinates."""
    return (
        MARS_RADIUS_M * math.radians(longitude),
        MARS_RADIUS_M * math.sin(math.radians(latitude)),
    )


def project_geometry(geojson: object):
    if not isinstance(geojson, dict):
        raise ValueError("geometry must be a GeoJSON object")
    geometry = shape(geojson)
    if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
        raise ValueError(f"unsupported geometry type: {geometry.geom_type}")
    if geometry.is_empty or not geometry.is_valid or geometry.area <= 0:
        raise ValueError("geometry is empty, invalid, or zero-area")
    projected = transform(_equal_area_xy, geometry)
    if projected.is_empty or not projected.is_valid or projected.area <= 0:
        raise ValueError("projected geometry is empty, invalid, or zero-area")
    return geometry, projected


def geometry_sha256(geojson: dict) -> str:
    encoded = json.dumps(
        geojson, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def safe_asset_summary(asset: object) -> dict:
    if not isinstance(asset, dict):
        return {"present": False}
    href = asset.get("href")
    safe_url = safe_url_summary(href) if isinstance(href, str) else None
    roles = asset.get("roles")
    return {
        "present": True,
        "title": asset.get("title"),
        "type": asset.get("type"),
        "roles": roles if isinstance(roles, list) else None,
        "url": safe_url,
    }


def _finite_metric(metrics: object, key: str, item_id: str) -> float:
    if not isinstance(metrics, dict):
        raise ValueError(f"missing E583 QA metrics for {item_id}")
    value = metrics.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"missing numeric {key} for {item_id}")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"non-finite {key} for {item_id}")
    return number


def pairwise_footprint_overlap(rows: list[dict]) -> dict:
    total = len(rows) * (len(rows) - 1) // 2
    intersecting = 0
    iou_ge_0_1 = 0
    maximum_iou = 0.0
    maximum_pair = None
    for index, left in enumerate(rows):
        for right in rows[index + 1:]:
            intersection_area = left["_geometry"].intersection(
                right["_geometry"]
            ).area
            if intersection_area <= 1e-6:
                continue
            union_area = (
                left["_geometry"].area
                + right["_geometry"].area
                - intersection_area
            )
            iou = intersection_area / union_area
            intersecting += 1
            if iou >= 0.1:
                iou_ge_0_1 += 1
            if iou > maximum_iou:
                maximum_iou = iou
                maximum_pair = [left["id"], right["id"]]
    return {
        "total_pairs": total,
        "footprint_intersecting_pairs": intersecting,
        "footprint_iou_ge_0_1_pairs": iou_ge_0_1,
        "maximum_footprint_iou": round(maximum_iou, 6),
        "maximum_pair": maximum_pair,
    }


def analyze_features(features: object, e583_receipt: dict, e585_bbox_audit: dict | None = None) -> dict:
    if not isinstance(e583_receipt, dict) or e583_receipt.get("experiment") != "E583":
        raise ValueError("input must be the committed E583 receipt")
    if e583_receipt.get("credentials_used") is not False:
        raise ValueError("credentialed E583 receipt is outside the frozen design")
    expected_items = e583_receipt.get("items")
    if not isinstance(expected_items, list) or len(expected_items) != MAX_ITEMS:
        raise ValueError("E583 receipt must contain exactly nine items")
    expected = {item.get("id"): item for item in expected_items if isinstance(item, dict)}
    if len(expected) != MAX_ITEMS or None in expected:
        raise ValueError("E583 item IDs must be non-empty and unique")
    if not isinstance(features, list):
        raise ValueError("STAC search response must contain a feature list")

    selected = {}
    duplicate_ids = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        item_id = feature.get("id")
        if not isinstance(item_id, str) or not item_id:
            continue
        if feature.get("collection") != COLLECTION:
            continue
        if item_id in selected:
            duplicate_ids.append(item_id)
            continue
        selected[item_id] = feature

    actual_ids = set(selected)
    expected_ids = set(expected)
    if duplicate_ids or actual_ids != expected_ids:
        return {
            "experiment": "E586",
            "decision": "ITEM_SET_MISMATCH",
            "expected_item_ids": sorted(expected_ids),
            "actual_item_ids": sorted(actual_ids),
            "missing_item_ids": sorted(expected_ids - actual_ids),
            "unexpected_item_ids": sorted(actual_ids - expected_ids),
            "duplicate_item_ids": sorted(set(duplicate_ids)),
            "credentials_used": False,
            "raw_item_json_stored": False,
            "raw_geometry_stored": False,
        }

    bbox_by_id = {}
    if e585_bbox_audit is not None:
        if not isinstance(e585_bbox_audit, dict) or e585_bbox_audit.get("experiment") != "E585":
            raise ValueError("bbox comparison input must be the committed E585 result")
        bbox_items = e585_bbox_audit.get("items")
        if not isinstance(bbox_items, list):
            raise ValueError("E585 result has no item list")
        for item in bbox_items:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                raise ValueError("E585 bbox rows must have item IDs")
            item_id = item["id"]
            if item_id in bbox_by_id:
                raise ValueError("E585 bbox item IDs must be unique")
            value = item.get("bbox_intersection_fraction_of_item")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise ValueError(f"invalid E585 bbox fraction for {item_id}")
            bbox_by_id[item_id] = float(value)
        if set(bbox_by_id) != expected_ids:
            raise ValueError("E585 and E583 item IDs do not match exactly")

    aoi_geometry = transform(_equal_area_xy, box(*JEZERO_BBOX))
    rows = []
    errors = []
    for item_id in sorted(expected_ids):
        feature = selected[item_id]
        try:
            geometry_json = feature.get("geometry")
            geometry, projected = project_geometry(geometry_json)
            bbox = validate_bbox(feature.get("bbox"), f"{item_id} bbox")
            geometry_bounds = geometry.bounds
            bbox_delta = max(
                abs(geometry_bounds[index] - bbox[index]) for index in range(4)
            )
            if bbox_delta > GEOMETRY_BBOX_TOLERANCE_DEG:
                raise ValueError(
                    f"geometry/bbox disagreement {bbox_delta:.6f} degrees"
                )

            footprint_area = projected.area
            intersection_area = projected.intersection(aoi_geometry).area
            fraction = min(1.0, max(0.0, intersection_area / footprint_area))
            assets = feature.get("assets")
            qa_asset = assets.get("qa_metrics") if isinstance(assets, dict) else None
            source_metrics = expected[item_id].get("metrics")
            rows.append({
                "id": item_id,
                "geometry_sha256": geometry_sha256(geometry_json),
                "geometry_type": geometry.geom_type,
                "footprint_area_km2": round(footprint_area / 1_000_000, 6),
                "aoi_intersection_area_km2": round(intersection_area / 1_000_000, 6),
                "fraction_of_footprint_inside_aoi": round(fraction, 8),
                "bbox_intersection_fraction_of_item": (
                    round(bbox_by_id[item_id], 8) if item_id in bbox_by_id else None
                ),
                "geometry_to_bbox_fraction_ratio": (
                    round(fraction / bbox_by_id[item_id], 8)
                    if item_id in bbox_by_id and bbox_by_id[item_id] > 0
                    else None
                ),
                "geometry_bbox_max_delta_deg": round(bbox_delta, 9),
                "qa_asset": safe_asset_summary(qa_asset),
                "qa_mean_difference_m": _finite_metric(
                    source_metrics, "mean_difference_m", item_id
                ),
                "qa_median_difference_m": _finite_metric(
                    source_metrics, "median_difference_m", item_id
                ),
                "qa_stddev_difference_m": _finite_metric(
                    source_metrics, "stddev_difference_m", item_id
                ),
                "_geometry": projected,
            })
        except Exception as error:
            errors.append({
                "id": item_id,
                "error_type": type(error).__name__,
                "error": str(error)[:240],
            })

    contained = [
        row for row in rows
        if row["fraction_of_footprint_inside_aoi"] >= 0.99
    ]
    partial = [
        row for row in rows
        if row["fraction_of_footprint_inside_aoi"] < 0.99
    ]
    pairwise = pairwise_footprint_overlap(rows)
    contained_pairwise = pairwise_footprint_overlap(contained)
    bbox_deltas = [
        abs(row["fraction_of_footprint_inside_aoi"] - row["bbox_intersection_fraction_of_item"])
        for row in rows
        if row["bbox_intersection_fraction_of_item"] is not None
    ]
    bbox_comparison = {
        "compared_item_count": len(bbox_deltas),
        "median_absolute_fraction_difference": (
            round(statistics.median(bbox_deltas), 8) if bbox_deltas else None
        ),
        "maximum_absolute_fraction_difference": (
            round(max(bbox_deltas), 8) if bbox_deltas else None
        ),
        "interpretation": (
            "Bounding-box area fractions are only a coarse envelope; actual footprint "
            "fractions are computed from GeoJSON polygons."
        ),
    }
    complete = len(rows) == MAX_ITEMS and not errors
    result = {
        "experiment": "E586",
        "decision": "GEOMETRY_AUDIT_COMPLETE" if complete else "PARTIAL_GEOMETRY_AUDIT",
        "collection": COLLECTION,
        "aoi_bbox_mars_lon_lat": list(JEZERO_BBOX),
        "coordinate_interpretation": (
            "Mars 2015 ocentric longitude/latitude as supplied by the USGS STAC "
            "collection; no Earth WGS84 reinterpretation."
        ),
        "area_method": (
            "Spherical cylindrical equal-area projection with Mars 2015 "
            "semi-major radius 3,396,190 m. Area ratios and IoU are the primary "
            "outputs; this is not a DEM or terrain measurement."
        ),
        "selected_item_count": len(rows),
        "invalid_item_count": len(errors),
        "strict_geometry_contained_count": len(contained),
        "partial_geometry_count": len(partial),
        "items": [
            {key: value for key, value in row.items() if key != "_geometry"}
            for row in rows
        ],
        "invalid_items": errors,
        "strict_geometry_contained_qa_summary": {
            "count": len(contained),
            "mean_difference_m_median": (
                round(statistics.median(
                    row["qa_mean_difference_m"] for row in contained
                ), 6) if contained else None
            ),
            "median_difference_m_median": (
                round(statistics.median(
                    row["qa_median_difference_m"] for row in contained
                ), 6) if contained else None
            ),
        },
        "pairwise_footprint_overlap": pairwise,
        "strict_geometry_contained_pairwise_footprint_overlap": contained_pairwise,
        "bbox_vs_geometry_comparison": bbox_comparison,
        "qa_spatial_support": (
            "NOT ESTABLISHED BY ITEM GEOMETRY. The QA asset is attached to the "
            "product; no AOI-clipped support is inferred."
        ),
        "interpretation_boundary": [
            "Overlap is computed from actual STAC GeoJSON footprint geometry, not item bounding boxes.",
            "Footprint/AOI intersection does not establish where product-level QA metrics were computed.",
            "QA metrics remain post-control CTX-MOLA residual summaries, not independent validation or absolute accuracy.",
            "Spatial overlap warns against assuming independent products; it does not identify shared control lineage.",
            "No slope, route safety, E001 recovery, cross-body similarity, novel analogue, or challenge-superiority claim is inferred.",
        ],
        "credentials_used": False,
        "raw_item_json_stored": False,
        "raw_geometry_stored": False,
        "raw_qa_text_stored": False,
        "signed_query_values_stored": False,
    }
    return result


def audit(e583_receipt: dict, e585_bbox_audit: dict | None = None) -> dict:
    payload = {
        "collections": [COLLECTION],
        "bbox": list(JEZERO_BBOX),
        "limit": SEARCH_LIMIT,
    }
    receipt = {
        "experiment": "E586",
        "collection": COLLECTION,
        "search_url": safe_url_summary(API_URL),
        "search_payload": payload,
        "credentials_used": False,
        "raw_item_json_stored": False,
        "raw_geometry_stored": False,
        "signed_query_values_stored": False,
        "decision": "ACQUISITION_NOT_ATTEMPTED",
    }
    response = fetch_bounded(
        API_URL,
        max_bytes=MAX_SEARCH_BYTES,
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    receipt.update({
        "search_http_status": response["status"],
        "search_bytes_read": response["bytes_read"],
        "search_declared_bytes": response["declared_bytes"],
        "search_too_large": response["too_large"],
        "search_url_final": safe_url_summary(response["final_url"]),
    })
    if response["status"] != 200:
        receipt["decision"] = "STAC_SEARCH_FAILURE"
        return receipt
    if response["too_large"]:
        receipt["decision"] = "STAC_SEARCH_EXCEEDS_1MB_CAP"
        return receipt
    receipt["search_response_sha256"] = hashlib.sha256(
        response["payload"]
    ).hexdigest()
    try:
        document = json.loads(response["payload"].decode("utf-8"))
    except Exception as error:
        raise ProbeError("STAC response is not valid UTF-8 JSON") from error
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise ProbeError("STAC response is not a FeatureCollection")
    features = document.get("features")
    if not isinstance(features, list):
        raise ProbeError("STAC FeatureCollection has no feature list")
    receipt["search_result_count"] = len(features)
    result = analyze_features(features, e583_receipt, e585_bbox_audit)
    receipt.update(result)
    receipt["search_result_count"] = len(features)
    receipt["search_response_sha256"] = hashlib.sha256(
        response["payload"]
    ).hexdigest()
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--receipt",
        type=Path,
        default=Path("research/results/E583_CTX_QA_COHORT_SCREEN_20261112.json"),
    )
    parser.add_argument(
        "--bbox-audit",
        type=Path,
        default=Path("research/results/E585_CTX_BBOX_OVERLAP_AUDIT_20261112.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(".artifacts/e586/ctx-footprint-geometry.json"),
    )
    args = parser.parse_args()
    try:
        source = json.loads(args.receipt.read_text(encoding="utf-8"))
        bbox_audit = json.loads(args.bbox_audit.read_text(encoding="utf-8"))
        result = audit(source, bbox_audit)
    except Exception as error:
        result = {
            "experiment": "E586",
            "decision": "ACQUISITION_OR_ANALYSIS_ERROR",
            "error_type": type(error).__name__,
            "error": str(error)[:300],
            "credentials_used": False,
            "raw_item_json_stored": False,
            "raw_geometry_stored": False,
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "experiment": "E586",
        "decision": result.get("decision"),
        "search_http_status": result.get("search_http_status"),
        "selected_item_count": result.get("selected_item_count"),
        "strict_geometry_contained_count": result.get("strict_geometry_contained_count"),
        "partial_geometry_count": result.get("partial_geometry_count"),
        "invalid_item_count": result.get("invalid_item_count"),
        "footprint_intersecting_pairs": (
            result.get("pairwise_footprint_overlap", {}).get(
                "footprint_intersecting_pairs"
            )
        ),
        "output": str(args.out),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
