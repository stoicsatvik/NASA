"""E596: audit a pinned public planetary-analogue catalogue without retaining coordinates."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

SOURCE_REPO = "rachellelecussan/planetary-analogue-catalogue"
SOURCE_COMMIT = "62e6339bdf308de3bc987388d0faa7130cf57de9"
SOURCE_BLOB_SHA = "156edd871599cf9ac9c083658d14d034f660e35d"
SOURCE_URL = (
    "https://raw.githubusercontent.com/rachellelecussan/"
    "planetary-analogue-catalogue/"
    + SOURCE_COMMIT
    + "/data/sites.geojson"
)


def audit(path: Path | str) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("type") != "FeatureCollection":
        raise ValueError("source is not a GeoJSON FeatureCollection")
    features = payload.get("features")
    if not isinstance(features, list) or not features:
        raise ValueError("source has no feature list")
    ids = []
    sites = []
    statuses = Counter()
    precision = Counter()
    targets = Counter()
    types = Counter()
    sensitive_count = 0
    reference_count = photo_count = 0
    for feature in features:
        if feature.get("type") != "Feature":
            raise ValueError("non-Feature object in FeatureCollection")
        properties = feature.get("properties") or {}
        site_id = properties.get("id")
        name = properties.get("name")
        if not isinstance(site_id, str) or not site_id or not isinstance(name, str) or not name:
            raise ValueError("site id/name missing")
        ids.append(site_id)
        review_status = str(properties.get("review_status", "Unknown"))
        coordinate_precision = str(properties.get("coordinate_precision", "Unknown"))
        target = str(properties.get("analogue_for_primary", "Unknown"))
        analogue_type = str(properties.get("analogue_type_primary", "Unknown"))
        sensitive = str(properties.get("sensitive_site", "Unknown"))
        refs = properties.get("references") or []
        photos = properties.get("photos") or []
        if not isinstance(refs, list) or not isinstance(photos, list):
            raise ValueError(f"references/photos must be lists for {site_id}")
        if not refs:
            raise ValueError(f"site has no source references: {site_id}")
        statuses[review_status] += 1
        precision[coordinate_precision] += 1
        targets[target] += 1
        types[analogue_type] += 1
        reference_count += len(refs)
        photo_count += len(photos)
        sensitive_count += sensitive.lower() == "yes"
        sites.append({
            "id": site_id,
            "name": name,
            "country": properties.get("country"),
            "primary_target": target,
            "primary_analogue_type": analogue_type,
            "coordinate_precision": coordinate_precision,
            "review_status": review_status,
            "sensitive_site": sensitive.lower() == "yes",
            "reference_count": len(refs),
            "photo_count": len(photos),
        })
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate site IDs")
    verified_ids = sorted(
        site["id"] for site in sites if site["review_status"].strip().lower() == "verified"
    )
    draft_ids = sorted(
        site["id"] for site in sites if site["review_status"].strip().lower() == "draft"
    )
    return {
        "experiment": "E596",
        "source": {
            "repository": SOURCE_REPO,
            "commit": SOURCE_COMMIT,
            "geojson_git_blob_sha": SOURCE_BLOB_SHA,
            "url": SOURCE_URL,
            "data_license": "CC-BY-4.0",
            "code_license": "MIT",
            "citation": "Le Cussan, R. (2026). Planetary Analogue Catalogue, v0.1.",
        },
        "feature_count": len(features),
        "review_status_counts": dict(sorted(statuses.items())),
        "draft_count": len(draft_ids),
        "verified_count": len(verified_ids),
        "coordinate_precision_counts": dict(sorted(precision.items())),
        "primary_target_counts": dict(sorted(targets.items())),
        "primary_analogue_type_counts": dict(sorted(types.items())),
        "reference_count": reference_count,
        "photo_count": photo_count,
        "sensitive_site_count": sensitive_count,
        "verified_source_candidate_ids": verified_ids,
        "draft_site_ids": draft_ids,
        "e001_label_admission": "NONE; source review status is not an independently validated ground-truth label",
        "e001_known_site_recovery": "NOT_YET_MEASURED",
        "cross_body_similarity": "NOT_YET_PROVEN",
        "novel_analogue_discovery": "NOT_YET_PROVEN",
        "sites": sorted(sites, key=lambda site: site["id"]),
        "raw_coordinates_retained": False,
        "raw_geometry_retained": False,
        "decision": (
            "CANDIDATE_CATALOGUE_ONLY_ALL_CURRENT_RECORDS_DRAFT"
            if not verified_ids else
            "CANDIDATE_CATALOGUE_REQUIRES_REPO_LEVEL_PRIMARY_SOURCE_REVIEW"
        ),
        "next_gate": (
            "Independently review primary references and resolve site extents/coordinates "
            "from primary geospatial sources before constructing an E001 labelled feature matrix."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.input)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
