"""E227 USGS source-quality audit: geometry-vs-attribute coordinate consistency.

Reads a REAL unauthenticated USGS ArcGIS sample receipt; does not infer
planetary-body labels, site suitability or analogue recovery.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path


def distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    for lat, lon in ((lat1, lon1), (lat2, lon2)):
        if not math.isfinite(lat) or not math.isfinite(lon) or abs(lat) > 90 or abs(lon) > 180:
            raise ValueError("Invalid geodetic coordinate")
    radius = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(min(1.0, math.sqrt(a)))


def audit(receipt: dict, threshold_m: float = 100.0) -> dict:
    sample = receipt["usgs"]["arcgis_public_sample"]
    if sample.get("status") != "PUBLIC_SAMPLE_INGESTED":
        raise ValueError("No verified real public feature sample")
    points = sample.get("first_five_points", [])
    if sample.get("point_features_ingested") != len(points):
        raise ValueError("Truncated feature sample; cannot audit all returned points")
    if not points or not math.isfinite(threshold_m) or threshold_m <= 0:
        raise ValueError("Invalid sample or threshold")
    records = []
    missing_body = 0
    types = Counter()
    for point in points:
        props = point["attributes"]
        body = props.get("AnalogBody")
        if body is None or not str(body).strip():
            missing_body += 1
        kind = str(props.get("AnalogType") or "UNKNOWN").strip()
        types[kind] += 1
        attr_lat, attr_lon = props.get("Lat"), props.get("Lon")
        if not isinstance(attr_lat, (float, int)) or not isinstance(attr_lon, (float, int)):
            discrepancy = None
        else:
            discrepancy = distance_m(
                float(point["latitude"]), float(point["longitude"]),
                float(attr_lat), float(attr_lon),
            )
        records.append({
            "name": props.get("Name"), "fid": props.get("FID"),
            "analogue_body_present": bool(body and str(body).strip()),
            "analogue_type": kind,
            "geometry_vs_attribute_distance_m": discrepancy,
            "exceeds_100m": discrepancy is not None and discrepancy > threshold_m,
        })
    discrepancies = [r["geometry_vs_attribute_distance_m"] for r in records
                     if r["geometry_vs_attribute_distance_m"] is not None]
    return {
        "experiment": "E227 independent USGS analogue point-label quality control",
        "source_raw_sha256": sample.get("raw_sha256"),
        "sample_count": len(records),
        "body_missing_count": missing_body,
        "body_missing_fraction": missing_body / len(records),
        "type_counts": dict(sorted(types.items())),
        "coordinate_discrepancies_over_100m": sum(r["exceeds_100m"] for r in records),
        "max_coordinate_discrepancy_m": max(discrepancies) if discrepancies else None,
        "records": records,
        "interpretation": "Published USGS point attributes, not validated planetary analogue recovery.",
        "claim": "SOURCE DATA QC SUPPORTED; cross-body similarity NOT YET PROVEN; E001 NOT YET MEASURED",
        "limitations": [
            "Four currently returned public points are all volcanic; not a representative negative-control sample.",
            "Missing AnalogBody does not establish a Moon/Mars analogue class.",
            "Lat/Lon attribute and GeoJSON geometry mismatch does not determine which position is correct.",
            "Rounded source attribute coordinates can differ by tens of metres.",
            "No real planetary-body terrain descriptors were compared.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.receipt.read_text(encoding="utf-8")))
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
