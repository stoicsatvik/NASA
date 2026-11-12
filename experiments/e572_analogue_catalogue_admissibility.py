"""E572: admissibility audit for a pinned independent planetary-analogue catalogue.

The source is a candidate inventory, not ground truth. No source rows or coordinates
are retained in the result; only aggregate counts and provenance are emitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

SOURCE_REPOSITORY = "rachellelecussan/planetary-analogue-catalogue"
SOURCE_COMMIT = "62e6339bdf308de3bc987388d0faa7130cf57de9"
SOURCE_PATH = "data/sites.geojson"
SOURCE_BLOB_SHA1 = "156edd871599cf9ac9c083658d14d034f660e35d"
SOURCE_BYTES = 143202
SOURCE_URL = (
    "https://raw.githubusercontent.com/"
    f"{SOURCE_REPOSITORY}/{SOURCE_COMMIT}/{SOURCE_PATH}"
)
SOURCE_LICENSE = "CC BY 4.0"
SOURCE_CITATION = "Le Cussan, R. (2026). Planetary Analogue Catalogue, v0.1."
MAX_BYTES = 200_000
IN_SCOPE_BODIES = {"Mars", "Moon"}
NON_PHYSICAL_SHARED_FIELDS = {"access_level", "hazard_rating"}
LABEL_SUPPORT_FIELDS = {"analogue_for_primary", "target_feature", "science_relevance"}
NEGATIVE_CONTROL_ROLES = {"negative", "non-analogue", "non_analogue"}


def is_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def sorted_counts(values: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def is_negative_control(properties: dict) -> bool:
    role = str(properties.get("control_role", "")).strip().lower()
    return properties.get("is_analog") is False or role in NEGATIVE_CONTROL_ROLES


def audit_document(document: dict) -> dict:
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise ValueError("Expected a GeoJSON FeatureCollection")
    features = document.get("features")
    if not isinstance(features, list) or not features:
        raise ValueError("FeatureCollection must contain features")

    seen_ids: set[str] = set()
    for index, feature in enumerate(features):
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise ValueError(f"Invalid feature at index {index}")
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            raise ValueError(f"Missing properties at index {index}")
        site_id = properties.get("id")
        if not isinstance(site_id, str) or not site_id:
            raise ValueError(f"Missing stable site id at index {index}")
        if site_id in seen_ids:
            raise ValueError(f"Duplicate site id: {site_id}")
        seen_ids.add(site_id)

        geometry = feature.get("geometry")
        coordinates = geometry.get("coordinates") if isinstance(geometry, dict) else None
        if (
            not isinstance(geometry, dict)
            or geometry.get("type") != "Point"
            or not isinstance(coordinates, list)
            or len(coordinates) < 2
            or not is_number(coordinates[0])
            or not is_number(coordinates[1])
        ):
            raise ValueError(f"Invalid point coordinates for {site_id}")
        lon, lat = coordinates[:2]
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError(f"Out-of-range coordinates for {site_id}")

        references = properties.get("references", [])
        if not isinstance(references, list) or any(not isinstance(r, dict) for r in references):
            raise ValueError(f"Invalid references for {site_id}")

    in_scope = [
        feature for feature in features
        if feature["properties"].get("analogue_for_primary") in IN_SCOPE_BODIES
    ]
    if not in_scope:
        raise ValueError("No primary Mars/Moon analogue records found")

    controls = [
        feature for feature in in_scope
        if is_negative_control(feature["properties"])
    ]
    positives = [
        feature for feature in in_scope
        if not is_negative_control(feature["properties"])
    ]

    numeric_keys = sorted({
        key
        for feature in in_scope
        for key, value in feature["properties"].items()
        if is_number(value)
    })
    numeric_coverage = [
        {
            "field": key,
            "count": sum(
                1 for feature in in_scope
                if is_number(feature["properties"].get(key))
            ),
        }
        for key in numeric_keys
    ]
    common_numeric = [
        row["field"] for row in numeric_coverage
        if row["count"] == len(in_scope)
    ]
    common_physical = [
        key for key in common_numeric
        if key not in NON_PHYSICAL_SHARED_FIELDS
    ]

    family_counts = Counter(
        str(feature["properties"].get("analogue_type_primary"))
        for feature in positives
        if feature["properties"].get("analogue_type_primary")
    )
    verified_family_counts = Counter(
        str(feature["properties"].get("analogue_type_primary"))
        for feature in positives
        if (
            str(feature["properties"].get("review_status", "")).lower() == "verified"
            and feature["properties"].get("analogue_type_primary")
        )
    )
    families_with_two = [
        {"family": family, "count": count}
        for family, count in sorted(family_counts.items())
        if count >= 2
    ]
    verified_families_with_two = [
        {"family": family, "count": count}
        for family, count in sorted(verified_family_counts.items())
        if count >= 2
    ]

    references = [
        reference
        for feature in positives
        for reference in feature["properties"].get("references", [])
    ]
    peer_reviewed = [reference for reference in references if reference.get("peer_reviewed") is True]
    peer_reviewed_label_support = [
        reference for reference in peer_reviewed
        if LABEL_SUPPORT_FIELDS.intersection(reference.get("supports", []))
    ]

    precision_counts = sorted_counts([
        str(feature["properties"].get("coordinate_precision", "MISSING"))
        for feature in in_scope
    ])
    body_counts = sorted_counts([
        str(feature["properties"]["analogue_for_primary"])
        for feature in positives
    ])
    type_counts = sorted_counts([
        str(feature["properties"].get("analogue_type_primary"))
        for feature in positives
        if feature["properties"].get("analogue_type_primary")
    ])
    review_counts = sorted_counts([
        str(feature["properties"].get("review_status", "MISSING"))
        for feature in positives
    ])

    target_measurement_keys = sorted({
        key
        for feature in in_scope
        for key, value in (feature["properties"].get("compare") or {}).items()
        if is_number(value) and key not in {"lat", "lon", "view_km"}
    })
    target_measurement_field_coverage = [
        {
            "field": key,
            "count": sum(
                1 for feature in in_scope
                if is_number((feature["properties"].get("compare") or {}).get(key))
            ),
        }
        for key in target_measurement_keys
    ]
    target_measurement_fields = [
        row["field"] for row in target_measurement_field_coverage
    ]
    common_target_measurement_fields = [
        row["field"] for row in target_measurement_field_coverage
        if row["count"] == len(in_scope)
    ]

    verified_positive_records = sum(
        1 for feature in positives
        if str(feature["properties"].get("review_status", "")).lower() == "verified"
    )
    reasons = []
    if not verified_families_with_two:
        reasons.append("No analogue family has at least two Verified positive sites.")
    if not controls:
        reasons.append("No explicit non-analogue control sites are supplied.")
    if not common_physical:
        reasons.append(
            "No physical numeric descriptor is populated across every in-scope "
            "positive/control record; the only common numeric fields are "
            "access_level and hazard_rating."
        )
    if not common_target_measurement_fields:
        reasons.append(
            "No target-body numeric measurement field is populated across every "
            "in-scope positive/control record; map context alone is not a matched "
            "physical measurement."
        )

    return {
        "generated": document.get("generated"),
        "total_features": len(features),
        "in_scope_features": len(in_scope),
        "in_scope_positive_records": len(positives),
        "in_scope_by_body": body_counts,
        "primary_type_counts": type_counts,
        "review_status_counts": review_counts,
        "coordinate_precision_counts": precision_counts,
        "references": {
            "total": len(references),
            "peer_reviewed": len(peer_reviewed),
            "peer_reviewed_label_support": len(peer_reviewed_label_support),
            "unverified": sum(1 for reference in references if reference.get("unverified") is True),
        },
        "missing_coordinates": 0,
        "numeric_field_coverage": numeric_coverage,
        "common_numeric_fields": common_numeric,
        "common_physical_numeric_fields": common_physical,
        "target_measurement_field_coverage": target_measurement_field_coverage,
        "target_measurement_fields": target_measurement_fields,
        "common_target_measurement_fields": common_target_measurement_fields,
        "family_counts": dict(sorted(family_counts.items())),
        "families_with_two_or_more": families_with_two,
        "verified_positive_records": verified_positive_records,
        "verified_positive_family_counts": dict(sorted(verified_family_counts.items())),
        "verified_families_with_two_or_more": verified_families_with_two,
        "explicit_non_analogue_controls": len(controls),
        "minimum_e001_input_gate_passed": not reasons,
        "e001_reasons": reasons,
    }


def git_blob_sha1(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def fetch_pinned_source() -> bytes:
    request = Request(
        SOURCE_URL,
        headers={
            "User-Agent": "Unified-Parallel-Foundry-E572/1.0",
            "Accept": "application/geo+json,application/json",
        },
    )
    with urlopen(request, timeout=20) as response:
        final = urlparse(response.geturl())
        if final.scheme != "https" or final.hostname != "raw.githubusercontent.com":
            raise ValueError("Source redirected outside pinned raw.githubusercontent.com host")
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError(f"Source exceeded {MAX_BYTES} byte cap")
    if len(raw) != SOURCE_BYTES:
        raise ValueError(f"Source size changed: expected {SOURCE_BYTES}, got {len(raw)}")
    actual_blob = git_blob_sha1(raw)
    if actual_blob != SOURCE_BLOB_SHA1:
        raise ValueError(
            f"Git blob mismatch: expected {SOURCE_BLOB_SHA1}, got {actual_blob}"
        )
    return raw


def build_result(raw: bytes) -> dict:
    document = json.loads(raw.decode("utf-8"))
    return {
        "source": {
            "repository": SOURCE_REPOSITORY,
            "commit": SOURCE_COMMIT,
            "path": SOURCE_PATH,
            "git_blob_sha1": SOURCE_BLOB_SHA1,
            "bytes": SOURCE_BYTES,
            "license": SOURCE_LICENSE,
            "citation": SOURCE_CITATION,
        },
        **audit_document(document),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.download == (args.input is not None):
        parser.error("Provide exactly one of --download or --input")
    raw = fetch_pinned_source() if args.download else args.input.read_bytes()
    if len(raw) != SOURCE_BYTES or git_blob_sha1(raw) != SOURCE_BLOB_SHA1:
        raise SystemExit("Input does not match the pinned source blob")
    result = build_result(raw)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    print(
        "E572: "
        f"{result['in_scope_features']} Mars/Moon records; "
        f"{result['verified_positive_records']} verified positives; "
        f"{result['explicit_non_analogue_controls']} controls; "
        f"{len(result['common_physical_numeric_fields'])} common physical fields; "
        f"{len(result['common_target_measurement_fields'])} common target measurement fields; "
        f"minimum E001 gate={result['minimum_e001_input_gate_passed']}"
    )


if __name__ == "__main__":
    main()
