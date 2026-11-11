"""E533: source-audit a predeclared subset of Mars/Moon catalogue candidates.

This validates DOI-to-record provenance against the pinned E532 GeoJSON. It
does not promote Draft catalogue records to independently verified labels,
does not create negative controls, and does not run E001.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import urllib.parse
import urllib.request
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
MAX_BYTES = 2 * 1024 * 1024
USER_AGENT = "NASA-E533-Candidate-Label-Source-Audit/1.0"
REVIEW_CSV = Path(__file__).resolve().parents[1] / "research" / "E533_CANDIDATE_LABEL_SOURCE_REVIEW_20261111.csv"


def safe_source_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return (
        parsed.scheme == "https"
        and parsed.netloc == "raw.githubusercontent.com"
        and parsed.path == f"/{SOURCE_OWNER}/{SOURCE_REPO}/{SOURCE_COMMIT}/{SOURCE_PATH}"
        and not parsed.query
        and not parsed.fragment
    )


def fetch_source(url: str = SOURCE_URL) -> tuple[dict[str, Any], str]:
    if not safe_source_url(url):
        raise ValueError("source URL is not the pinned E532 GeoJSON")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/geo+json, application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.geturl() != url:
            raise ValueError("unexpected source redirect")
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("source byte limit exceeded")
    document = json.loads(raw)
    if document.get("type") != "FeatureCollection" or not isinstance(document.get("features"), list):
        raise ValueError("invalid GeoJSON FeatureCollection")
    return document, hashlib.sha256(raw).hexdigest()


def load_review(path: Path = REVIEW_CSV) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def audit(document: dict[str, Any], rows: list[dict[str, str]], source_sha256: str) -> dict[str, Any]:
    features = {}
    for feature in document.get("features", []):
        props = feature.get("properties") or {}
        site_id = props.get("id")
        if not isinstance(site_id, str) or not site_id or site_id in features:
            raise ValueError("missing or duplicate catalogue site ID")
        features[site_id] = props

    if len(rows) != 6:
        raise ValueError("E533 predeclared review subset must contain exactly six records")
    ids = [row.get("site_id", "") for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate reviewed site ID")

    reviewed = []
    target_counts = {"Mars": 0, "Moon": 0}
    for row in rows:
        site_id = row["site_id"]
        if site_id not in features:
            raise ValueError(f"reviewed site absent from pinned catalogue: {site_id}")
        props = features[site_id]
        target = row["target_body"]
        if target not in target_counts or props.get("analogue_for_primary") != target:
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
        if row.get("review_decision") != "SOURCE_SUPPORTS_CANDIDATE_LABEL":
            raise ValueError(f"unexpected decision token for {site_id}")
        if not row.get("limitations", "").strip() or not row.get("evidence_relation", "").strip():
            raise ValueError(f"missing limitations/evidence relation for {site_id}")
        target_counts[target] += 1
        reviewed.append({
            "site_id": site_id,
            "target_body": target,
            "catalogue_status": "Draft",
            "catalogue_doi": row["catalogue_doi"],
            "additional_doi": row.get("additional_doi", ""),
            "source_title": row["source_title"],
            "source_year": int(row["source_year"]),
            "source_type": row["source_type"],
            "evidence_relation": row["evidence_relation"],
            "limitations": row["limitations"],
            "decision": "SOURCE_SUPPORTS_CANDIDATE_LABEL",
        })

    in_scope = [
        props for props in features.values()
        if props.get("analogue_for_primary") in ("Mars", "Moon")
    ]
    verified = sum(1 for props in features.values() if props.get("review_status") == "Verified")
    return {
        "experiment": "E533",
        "source_url": SOURCE_URL,
        "source_commit": SOURCE_COMMIT,
        "source_sha256": source_sha256,
        "catalogue_feature_count": len(features),
        "mars_moon_primary_candidate_count": len(in_scope),
        "predeclared_reviewed_count": len(reviewed),
        "unreviewed_mars_moon_candidate_count": len(in_scope) - len(reviewed),
        "reviewed_target_counts": target_counts,
        "catalogue_verified_count": verified,
        "catalogue_statuses_preserved": all(x["catalogue_status"] == "Draft" for x in reviewed),
        "candidate_positive_only": True,
        "negative_controls": 0,
        "e001_ready": False,
        "known_site_recovery": "NOT YET MEASURED",
        "cross_body_similarity": "NOT YET PROVEN",
        "reviewed_sites": reviewed,
        "interpretation": (
            "Primary sources support these six narrow candidate-label claims. "
            "This is not independent site verification, a negative-control set, "
            "a cross-body similarity result, or an E001 recovery experiment."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(".artifacts/e533/result.json"))
    args = parser.parse_args()
    document, digest = fetch_source()
    result = audit(document, load_review(), digest)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "catalogue_feature_count", "mars_moon_primary_candidate_count",
        "predeclared_reviewed_count", "unreviewed_mars_moon_candidate_count",
        "reviewed_target_counts", "catalogue_verified_count", "e001_ready",
        "known_site_recovery", "cross_body_similarity"
    )}, sort_keys=True))


if __name__ == "__main__":
    main()
