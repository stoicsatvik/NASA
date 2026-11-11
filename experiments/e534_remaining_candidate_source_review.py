"""E534: audit the six remaining Mars/Moon catalogue candidates.

E533's six-record purposeful subset is preserved unchanged. E534 audits the
complement against the same immutable E532 GeoJSON. Source support remains
candidate-positive only; this is not independent site verification or E001.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from experiments.e533_candidate_label_source_review import (
    SOURCE_COMMIT,
    SOURCE_URL,
    fetch_source,
    safe_source_url,
)

REVIEW_CSV = Path(__file__).resolve().parents[1] / "research" / "E534_REMAINING_CANDIDATE_SOURCE_REVIEW_20261111.csv"
PREVIOUS_CSV = Path(__file__).resolve().parents[1] / "research" / "E533_CANDIDATE_LABEL_SOURCE_REVIEW_20261111.csv"

PREVIOUS_IDS = {
    "atacama-yungay-cl",
    "rio-tinto-es",
    "iceland-volcanic-fields-is",
    "lava-beds-us",
    "mauna-kea-us",
    "haughton-crater-ca",
}
NEW_IDS = {
    "dallol-et",
    "mcmurdo-dry-valleys-aq",
    "arkaroola-au",
    "lanzarote-es",
    "bockfjord-svalbard-sj",
    "boulby-mine-gb",
}
EXPECTED_COUNTS = {"Mars": 10, "Moon": 2}


def load_review(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _features_by_id(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if document.get("type") != "FeatureCollection" or not isinstance(document.get("features"), list):
        raise ValueError("invalid GeoJSON FeatureCollection")
    features: dict[str, dict[str, Any]] = {}
    for feature in document["features"]:
        props = feature.get("properties") or {}
        site_id = props.get("id")
        if not isinstance(site_id, str) or not site_id or site_id in features:
            raise ValueError("missing or duplicate catalogue site ID")
        features[site_id] = props
    return features


def _validate_rows(
    features: dict[str, dict[str, Any]],
    rows: list[dict[str, str]],
    expected_ids: set[str],
    label: str,
) -> list[dict[str, Any]]:
    ids = [row.get("site_id", "") for row in rows]
    if len(rows) != 6 or set(ids) != expected_ids or len(ids) != len(set(ids)):
        raise ValueError(f"{label} must contain exactly its six frozen unique site IDs")

    reviewed = []
    for row in rows:
        site_id = row["site_id"]
        if site_id not in features:
            raise ValueError(f"reviewed site absent from pinned catalogue: {site_id}")
        props = features[site_id]
        target = row.get("target_body", "")
        if target not in EXPECTED_COUNTS or props.get("analogue_for_primary") != target:
            raise ValueError(f"target-body mismatch for {site_id}")
        if props.get("review_status") != "Draft" or row.get("catalogue_status") != "Draft":
            raise ValueError(f"catalogue review status changed or was promoted for {site_id}")

        catalogue_dois = {
            str(ref.get("doi", "")).strip().lower()
            for ref in props.get("references", [])
            if isinstance(ref, dict) and ref.get("doi")
        }
        doi = row.get("catalogue_doi", "").strip().lower()
        if not doi or doi not in catalogue_dois:
            raise ValueError(f"review DOI is not attached to pinned catalogue record: {site_id}")
        additional = row.get("additional_doi", "").strip().lower()
        if additional and additional not in catalogue_dois:
            raise ValueError(f"additional DOI is not attached to pinned catalogue record: {site_id}")
        if row.get("review_decision") != "SOURCE_SUPPORTS_CANDIDATE_LABEL":
            raise ValueError(f"unexpected decision token for {site_id}")
        if not row.get("limitations", "").strip() or not row.get("evidence_relation", "").strip():
            raise ValueError(f"missing limitations/evidence relation for {site_id}")

        reviewed.append({
            "site_id": site_id,
            "target_body": target,
            "catalogue_status": "Draft",
            "catalogue_doi": row["catalogue_doi"],
            "additional_doi": additional,
            "source_title": row["source_title"],
            "source_year": int(row["source_year"]),
            "source_type": row["source_type"],
            "evidence_relation": row["evidence_relation"],
            "limitations": row["limitations"],
            "decision": "SOURCE_SUPPORTS_CANDIDATE_LABEL",
        })
    return reviewed


def audit(
    document: dict[str, Any],
    previous_rows: list[dict[str, str]],
    new_rows: list[dict[str, str]],
    source_sha256: str,
) -> dict[str, Any]:
    features = _features_by_id(document)
    previous = _validate_rows(features, previous_rows, PREVIOUS_IDS, "E533 prior review")
    new = _validate_rows(features, new_rows, NEW_IDS, "E534 remaining review")
    if set(x["site_id"] for x in previous).intersection(x["site_id"] for x in new):
        raise ValueError("E534 new review overlaps the preserved E533 subset")

    in_scope = [
        props for props in features.values()
        if props.get("analogue_for_primary") in ("Mars", "Moon")
    ]
    if len(in_scope) != 12:
        raise ValueError("pinned catalogue Mars/Moon primary-candidate count changed")
    combined = previous + new
    target_counts = {
        target: sum(1 for item in combined if item["target_body"] == target)
        for target in EXPECTED_COUNTS
    }
    if target_counts != EXPECTED_COUNTS:
        raise ValueError(f"cumulative target counts changed: {target_counts}")
    verified = sum(1 for props in features.values() if props.get("review_status") == "Verified")

    return {
        "experiment": "E534",
        "source_url": SOURCE_URL,
        "source_commit": SOURCE_COMMIT,
        "source_sha256": source_sha256,
        "catalogue_feature_count": len(features),
        "mars_moon_primary_candidate_count": len(in_scope),
        "previous_e533_reviewed_count": len(previous),
        "new_e534_reviewed_count": len(new),
        "cumulative_source_audited_count": len(combined),
        "unreviewed_mars_moon_candidate_count": len(in_scope) - len(combined),
        "cumulative_target_counts": target_counts,
        "catalogue_verified_count": verified,
        "catalogue_statuses_preserved": all(x["catalogue_status"] == "Draft" for x in combined),
        "candidate_positive_only": True,
        "negative_controls": 0,
        "e001_ready": False,
        "known_site_recovery": "NOT YET MEASURED",
        "cross_body_similarity": "NOT YET PROVEN",
        "previous_reviewed_sites": previous,
        "newly_reviewed_sites": new,
        "interpretation": (
            "Primary sources support the narrow candidate-label claims for all twelve "
            "Mars/Moon records in this pinned catalogue. All catalogue records remain Draft. "
            "This does not independently verify site quality, create negative controls, "
            "establish matched physical descriptors, or measure E001 recovery."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(".artifacts/e534/result.json"))
    args = parser.parse_args()
    if not safe_source_url(SOURCE_URL):
        raise ValueError("source URL is not the pinned E532 GeoJSON")
    document, digest = fetch_source(SOURCE_URL)
    result = audit(document, load_review(PREVIOUS_CSV), load_review(REVIEW_CSV), digest)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "catalogue_feature_count",
        "mars_moon_primary_candidate_count",
        "previous_e533_reviewed_count",
        "new_e534_reviewed_count",
        "cumulative_source_audited_count",
        "unreviewed_mars_moon_candidate_count",
        "cumulative_target_counts",
        "catalogue_verified_count",
        "e001_ready",
        "known_site_recovery",
        "cross_body_similarity",
    )}, sort_keys=True))


if __name__ == "__main__":
    main()
