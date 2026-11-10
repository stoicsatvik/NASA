"""Audit an independent public planetary-analogue catalogue as candidate labels only.

The source is pinned to an immutable Git commit. This script does not copy the
catalogue into the repository, geocode sites, or promote Draft entries to
ground truth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

SOURCE_OWNER = "rachellelecussan"
SOURCE_REPO = "planetary-analogue-catalogue"
SOURCE_COMMIT = "62e6339bdf308de3bc987388d0faa7130cf57de9"
SOURCE_PATH = "data/sites.geojson"
SOURCE_URL = (
    f"https://raw.githubusercontent.com/{SOURCE_OWNER}/{SOURCE_REPO}/"
    f"{SOURCE_COMMIT}/{SOURCE_PATH}"
)
USER_AGENT = "NASA-Analog-Research/0.1 (pinned public catalogue audit)"
MAX_SOURCE_BYTES = 2 * 1024 * 1024
DESCRIPTOR_FIELDS = (
    "extent_km2",
    "altitude_min_m",
    "altitude_max_m",
    "ph_min",
    "ph_max",
    "temp_min_c",
    "temp_max_c",
    "salinity",
    "age",
    "rock_types",
    "key_minerals",
    "geological_setting",
    "target_feature",
    "analogue_limitations",
    "references",
)


def safe_source_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    expected_path = (
        f"/{SOURCE_OWNER}/{SOURCE_REPO}/{SOURCE_COMMIT}/{SOURCE_PATH}"
    )
    return (
        parsed.scheme == "https"
        and parsed.netloc == "raw.githubusercontent.com"
        and parsed.path == expected_path
        and not parsed.query
        and not parsed.fragment
    )


def fetch_source(url: str = SOURCE_URL) -> tuple[dict[str, Any], str, int]:
    if not safe_source_url(url):
        raise ValueError("source URL is not the pinned public catalogue file")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/geo+json, application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        if not safe_source_url(response.geturl()):
            raise ValueError("source redirected outside the pinned URL")
        payload = response.read(MAX_SOURCE_BYTES + 1)
    if len(payload) > MAX_SOURCE_BYTES:
        raise ValueError("source exceeds the 2 MiB safety limit")
    digest = hashlib.sha256(payload).hexdigest()
    document = json.loads(payload.decode("utf-8"))
    return document, digest, len(payload)


def _present(value: Any) -> bool:
    if value is None or value == "":
        return False
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def _counts(values: list[Any]) -> dict[str, int]:
    counter = Counter(str(value) for value in values)
    return dict(sorted(counter.items()))


def audit(document: dict[str, Any], source_sha256: str | None = None,
          source_bytes: int | None = None) -> dict[str, Any]:
    if document.get("type") != "FeatureCollection":
        raise ValueError("source is not a GeoJSON FeatureCollection")
    features = document.get("features")
    if not isinstance(features, list) or not features:
        raise ValueError("source contains no GeoJSON features")

    properties = [
        feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
        for feature in features
    ]
    geometries = [
        feature.get("geometry") if isinstance(feature.get("geometry"), dict) else {}
        for feature in features
    ]
    ids = [str(p.get("id")).strip() for p in properties if _present(p.get("id"))]
    references = [
        ref for p in properties
        for ref in (p.get("references") if isinstance(p.get("references"), list) else [])
        if isinstance(ref, dict)
    ]
    photos = [
        photo for p in properties
        for photo in (p.get("photos") if isinstance(p.get("photos"), list) else [])
    ]
    primary_labels = [
        str(p.get("analogue_for_primary")).strip()
        for p in properties if _present(p.get("analogue_for_primary"))
    ]
    primary_counts = _counts(primary_labels)
    review_counts = _counts([
        p.get("review_status", "MISSING") for p in properties
    ])
    precision_counts = _counts([
        p.get("coordinate_precision", "MISSING") for p in properties
    ])
    sensitive_counts = _counts([
        p.get("sensitive_site", "MISSING") for p in properties
    ])
    geometry_counts = _counts([
        geometry.get("type", "MISSING") for geometry in geometries
    ])

    valid_points = 0
    for geometry in geometries:
        coordinates = geometry.get("coordinates")
        if (
            geometry.get("type") == "Point"
            and isinstance(coordinates, (list, tuple))
            and len(coordinates) >= 2
            and all(not isinstance(v, bool) and isinstance(v, (int, float)) and math.isfinite(v) for v in coordinates[:2])
        ):
            valid_points += 1

    doi_values = [str(ref["doi"]).strip() for ref in references if _present(ref.get("doi"))]
    urls = [str(ref["url"]).strip() for ref in references if _present(ref.get("url"))]
    descriptor_coverage = {
        field: sum(_present(p.get(field)) for p in properties)
        for field in DESCRIPTOR_FIELDS
    }
    all_draft = bool(properties) and all(
        p.get("review_status") == "Draft" for p in properties
    )
    # The source is a catalogue of analog candidates, not a sampled control
    # population. It has no explicit non-analogue control field or records.
    explicit_non_analogue_controls = sum(
        1 for p in properties
        if str(p.get("control_role", "")).strip().lower()
        in {"negative", "non-analogue", "control"}
    )
    duplicate_ids = len(ids) - len(set(ids))
    mars_moon_primary = primary_counts.get("Mars", 0) + primary_counts.get("Moon", 0)

    return {
        "experiment": "E532",
        "source": {
            "repository": f"{SOURCE_OWNER}/{SOURCE_REPO}",
            "commit": SOURCE_COMMIT,
            "path": SOURCE_PATH,
            "url": SOURCE_URL,
            "generated": document.get("generated"),
            "sha256": source_sha256,
            "bytes": source_bytes,
        },
        "feature_count": len(features),
        "geometry_type_counts": geometry_counts,
        "valid_point_geometry_count": valid_points,
        "unique_site_id_count": len(set(ids)),
        "missing_site_id_count": len(features) - len(ids),
        "duplicate_site_id_count": duplicate_ids,
        "primary_analogue_label_field": "analogue_for_primary",
        "primary_target_counts": primary_counts,
        "mars_or_moon_primary_candidate_count": mars_moon_primary,
        "review_status_counts": review_counts,
        "all_records_draft": all_draft,
        "coordinate_precision_counts": precision_counts,
        "sensitive_site_counts": sensitive_counts,
        "reference_count": len(references),
        "peer_reviewed_reference_count": sum(ref.get("peer_reviewed") is True for ref in references),
        "non_peer_reviewed_reference_count": sum(ref.get("peer_reviewed") is False for ref in references),
        "unverified_reference_count": sum(ref.get("unverified") is True for ref in references),
        "doi_reference_count": len(doi_values),
        "unique_doi_count": len(set(doi_values)),
        "unique_reference_url_count": len(set(urls)),
        "photo_count": len(photos),
        "descriptor_coverage": descriptor_coverage,
        "explicit_non_analogue_control_count": explicit_non_analogue_controls,
        "e001_supervised_recovery_ready": (
            not all_draft
            and explicit_non_analogue_controls > 0
            and duplicate_ids == 0
            and valid_points == len(features)
        ),
        "interpretation": (
            "candidate-positive catalogue only; Draft records and absence of "
            "explicit non-analogue controls prohibit treating it as E001 ground truth"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(".artifacts/e532/result.json"))
    args = parser.parse_args()
    document, digest, size = fetch_source()
    result = audit(document, digest, size)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "experiment": "E532",
        "feature_count": result["feature_count"],
        "primary_target_counts": result["primary_target_counts"],
        "all_records_draft": result["all_records_draft"],
        "e001_supervised_recovery_ready": result["e001_supervised_recovery_ready"],
        "source_sha256": digest,
        "output": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
