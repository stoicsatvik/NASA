"""E585: quantify bounding-box intersection and overlap in the E583 CTX cohort.

This is a spherical-rectangle bounding-box diagnostic only. It does not compute
actual raster-footprint overlap, pixel support, independent accuracy, or route
safety. E583 QA metrics remain product-level summaries unless source semantics
establish otherwise.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

CONTAINMENT_THRESHOLD = 0.99


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


def spherical_rectangle_solid_angle_sr(bbox: tuple[float, float, float, float]) -> float:
    """Return a lon/lat rectangle's solid angle on the unit sphere (steradians).

    The common planetary-radius-squared factor is intentionally omitted:
    E585 reports only dimensionless fractions and IoU, not absolute area.
    """
    west, south, east, north = bbox
    return math.radians(east - west) * (
        math.sin(math.radians(north))
        - math.sin(math.radians(south))
    )


def intersection_bbox(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
) -> tuple[float, float, float, float] | None:
    west = max(left[0], right[0])
    south = max(left[1], right[1])
    east = min(left[2], right[2])
    north = min(left[3], right[3])
    if east <= west or north <= south:
        return None
    return west, south, east, north


def _metric_summary(values: list[float]) -> dict:
    return {
        "median": round(statistics.median(values), 6),
        "minimum": round(min(values), 6),
        "maximum": round(max(values), 6),
        "positive_count": sum(value > 0 for value in values),
    }


def _pairwise_summary(items: list[dict]) -> dict:
    total = len(items) * (len(items) - 1) // 2
    intersecting = 0
    iou_ge_0_1 = 0
    maximum = 0.0
    maximum_pair = None

    for index, left in enumerate(items):
        for right in items[index + 1:]:
            intersection = intersection_bbox(left["bbox"], right["bbox"])
            if intersection is None:
                continue
            intersection_solid_angle = spherical_rectangle_solid_angle_sr(intersection)
            union_solid_angle = (
                spherical_rectangle_solid_angle_sr(left["bbox"])
                + spherical_rectangle_solid_angle_sr(right["bbox"])
                - intersection_solid_angle
            )
            iou = intersection_solid_angle / union_solid_angle
            intersecting += 1
            if iou >= 0.1:
                iou_ge_0_1 += 1
            if iou > maximum:
                maximum = iou
                maximum_pair = [left["id"], right["id"]]

    return {
        "total_pairs": total,
        "bbox_intersecting_pairs": intersecting,
        "bbox_iou_ge_0_1_pairs": iou_ge_0_1,
        "maximum_bbox_iou": round(maximum, 6),
        "maximum_pair": maximum_pair,
    }


def analyze(receipt: dict) -> dict:
    if not isinstance(receipt, dict) or receipt.get("experiment") != "E583":
        raise ValueError("input must be the committed E583 receipt")
    if receipt.get("credentials_used") is not False:
        raise ValueError("credentialed acquisition is outside the frozen E583 design")

    aoi = validate_bbox(receipt.get("bbox_wgs84_lon_lat"), "AOI bbox")
    items = receipt.get("items")
    if not isinstance(items, list) or len(items) != 9:
        raise ValueError("E583 receipt must contain exactly nine selected items")
    if receipt.get("qa_success_count") != 9:
        raise ValueError("all nine E583 QA assets must have succeeded")

    seen = set()
    normalized = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("each E583 item must be an object")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id or item_id in seen:
            raise ValueError("E583 item IDs must be non-empty and unique")
        seen.add(item_id)
        if item.get("http_status") != 200:
            raise ValueError(f"QA asset did not succeed for {item_id}")

        bbox = validate_bbox(item.get("bbox"), f"{item_id} bbox")
        intersection = intersection_bbox(aoi, bbox)
        if intersection is None:
            raise ValueError(f"STAC-selected item bbox does not intersect AOI: {item_id}")

        metrics = item.get("metrics")
        if not isinstance(metrics, dict) or metrics.get("metric_count") != 6:
            raise ValueError(f"expected six parsed QA metrics for {item_id}")
        values = {}
        for key in ("mean_difference_m", "median_difference_m", "stddev_difference_m"):
            value = metrics.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"missing numeric {key} for {item_id}")
            value = float(value)
            if not math.isfinite(value):
                raise ValueError(f"non-finite {key} for {item_id}")
            values[key] = value

        item_solid_angle = spherical_rectangle_solid_angle_sr(bbox)
        intersection_solid_angle = spherical_rectangle_solid_angle_sr(intersection)
        aoi_solid_angle = spherical_rectangle_solid_angle_sr(aoi)
        normalized.append({
            "id": item_id,
            "bbox": bbox,
            "intersection_bbox": intersection,
            "bbox_intersection_fraction_of_item": intersection_solid_angle / item_solid_angle,
            "bbox_intersection_fraction_of_aoi": intersection_solid_angle / aoi_solid_angle,
            **values,
        })

    normalized.sort(key=lambda item: item["id"])
    contained = [
        item for item in normalized
        if item["bbox_intersection_fraction_of_item"] >= CONTAINMENT_THRESHOLD
    ]
    partial = [item for item in normalized if item not in contained]
    if not contained:
        raise ValueError("no item bounding boxes meet the frozen containment screen")

    public_items = [
        {
            "id": item["id"],
            "intersection_bbox_wgs84_lon_lat": [
                round(value, 8) for value in item["intersection_bbox"]
            ],
            "bbox_intersection_fraction_of_item": round(
                item["bbox_intersection_fraction_of_item"], 6
            ),
            "bbox_intersection_fraction_of_aoi": round(
                item["bbox_intersection_fraction_of_aoi"], 6
            ),
            "mean_difference_m": item["mean_difference_m"],
            "median_difference_m": item["median_difference_m"],
            "stddev_difference_m": item["stddev_difference_m"],
        }
        for item in normalized
    ]

    all_pairs = _pairwise_summary(normalized)
    contained_pairs = _pairwise_summary(contained)

    return {
        "experiment": "E585",
        "source_experiment": "E583",
        "aoi_bbox_wgs84_lon_lat": list(aoi),
        "spatial_measure_method": (
            "Unit-sphere spherical-rectangle solid angle in steradians; "
            "scale-free fractions and IoU, no body-specific radius or absolute-area claim; "
            "bounding boxes only, not item polygons or raster footprints."
        ),
        "containment_threshold": CONTAINMENT_THRESHOLD,
        "selected_item_count": len(normalized),
        "strict_bbox_contained_count": len(contained),
        "partial_bbox_intersection_count": len(partial),
        "items": public_items,
        "strict_bbox_contained_subset": {
            "item_ids": [item["id"] for item in contained],
            "mean_difference_m": _metric_summary(
                [item["mean_difference_m"] for item in contained]
            ),
            "median_difference_m": _metric_summary(
                [item["median_difference_m"] for item in contained]
            ),
            "stddev_difference_m": {
                "median": round(statistics.median(
                    item["stddev_difference_m"] for item in contained
                ), 6),
                "minimum": round(min(
                    item["stddev_difference_m"] for item in contained
                ), 6),
                "maximum": round(max(
                    item["stddev_difference_m"] for item in contained
                ), 6),
            },
            "pairwise_bbox_overlap": contained_pairs,
        },
        "all_selected_items_pairwise_bbox_overlap": all_pairs,
        "interpretation_boundary": [
            "A STAC bbox search admits any item whose bounding box intersects the AOI; it does not guarantee the whole item lies inside the AOI.",
            "Three selected item bounding boxes are materially partial under the 99% containment screen; their product-level QA summaries are not demonstrated to be AOI-clipped.",
            "Six item bounding boxes are at least 99% contained, and their descriptive positive-mean/median pattern persists, but their bounding boxes overlap substantially.",
            "Bounding-box intersection and IoU are not actual polygon/raster-footprint overlap and do not establish independent samples.",
            "QA residuals remain post-control product QA, not held-out accuracy, independent validation, or route-safety evidence.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--receipt",
        type=Path,
        default=Path("research/results/E583_CTX_QA_COHORT_SCREEN_20261112.json"),
    )
    parser.add_argument("--out", type=Path, default=Path(".artifacts/e585/result.json"))
    parser.add_argument("--expected", type=Path)
    args = parser.parse_args()

    result = analyze(json.loads(args.receipt.read_text(encoding="utf-8")))
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(encoded, encoding="utf-8")
    if args.expected:
        expected = json.loads(args.expected.read_text(encoding="utf-8"))
        if expected != result:
            raise SystemExit("E585 recomputation differs from committed result")
    print(json.dumps({
        "experiment": "E585",
        "strict_bbox_contained_count": result["strict_bbox_contained_count"],
        "partial_bbox_intersection_count": result["partial_bbox_intersection_count"],
        "bbox_intersecting_pairs": result["all_selected_items_pairwise_bbox_overlap"]["bbox_intersecting_pairs"],
        "bbox_iou_ge_0_1_pairs": result["all_selected_items_pairwise_bbox_overlap"]["bbox_iou_ge_0_1_pairs"],
        "output": str(args.out),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
