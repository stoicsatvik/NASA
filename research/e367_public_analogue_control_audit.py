"""E367: independent read-only audit of a public analogue benchmark's label design.

This is NOT a model reproduction, challenge entry, or assertion about another
team's scientific integrity. It measures what a published control catalog can
and cannot validate from source-pinned public files.
"""
from __future__ import annotations

import hashlib
import json
import math
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

OWNER_REPO = "Yakiyo/terra-nova"
COMMIT = "f6c53ba50a9379d1c06f610b0e598395a0a54b43"
FILES = ("data/known_analogs.json", "src/compute/validation.py", "README.md")
MAX_BYTES = 2_000_000


def download(path: str) -> bytes:
    if path not in FILES:
        raise ValueError("unapproved source path")
    url = f"https://raw.githubusercontent.com/{OWNER_REPO}/{COMMIT}/{path}"
    with urlopen(Request(url, headers={"User-Agent": "NASA-E367-Source-Audit/1.0"}),
                 timeout=35) as response:
        final = urlsplit(response.geturl())
        if final.scheme != "https" or final.hostname != "raw.githubusercontent.com":
            raise ValueError("unexpected source redirect")
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("source exceeds bounded download")
    return raw


def audit(catalog: dict, validation_code: str, readme: str) -> dict:
    if not isinstance(catalog, dict) or not isinstance(catalog.get("sites"), list) \
            or not isinstance(catalog.get("negatives"), list):
        raise ValueError("unexpected catalog structure")
    sites, negatives = catalog["sites"], catalog["negatives"]
    if not sites or not negatives:
        raise ValueError("missing positive or negative reference points")
    names = [x.get("name") for x in sites + negatives]
    if any(not isinstance(n, str) or not n for n in names) or len(set(names)) != len(names):
        raise ValueError("missing or duplicate site identity")
    for site in sites + negatives:
        if not all(type(site.get(k)) in (int, float) and math.isfinite(site[k])
                   for k in ("lat", "lon")):
            raise ValueError("missing or nonfinite coordinate")
        if not (-90 <= site["lat"] <= 90 and -180 <= site["lon"] <= 180):
            raise ValueError("invalid geographic coordinate")
    if "site[\"kind\"] == \"environment\"" not in validation_code \
            or 'catalog["negatives"]' not in validation_code \
            or "def roc_auc(" not in validation_code:
        raise ValueError("source validation policy not independently located")
    environment = [s for s in sites if s.get("kind") == "environment"]
    geology = [s for s in sites if s.get("kind") == "geology"]
    if len(environment) + len(geology) != len(sites):
        raise ValueError("unknown source control role")
    by_body = {
        body: sum(body in s.get("bodies", []) for s in environment)
        for body in ("mars", "moon")
    }
    if not all(by_body.values()):
        raise ValueError("missing body-specific positive controls")
    return {
        "experiment": "E367_PUBLIC_ANALOGUE_CONTROL_DESIGN_AUDIT",
        "source_repository": OWNER_REPO,
        "source_commit": COMMIT,
        "catalog_sites": len(sites),
        "environment_positive_sites": len(environment),
        "geology_only_sites_excluded_from_auc": len(geology),
        "editorial_negative_sites": len(negatives),
        "negative_sites_without_source_url": sum(not s.get("source_url") for s in negatives),
        "environment_sites_with_wikipedia_source": sum(
            (s.get("source_url") or "").startswith("https://en.wikipedia.org/wiki/")
            for s in environment
        ),
        "environment_positive_by_body": by_body,
        "body_specific_positive_negative_pairs": {
            body: count * len(negatives) for body, count in by_body.items()
        },
        "source_self_reports_auc_one": "1.00 on all five built-in targets" in readme,
        "independent_auc_reproduction": "NOT PERFORMED",
        "independently_blinded_earth_mars_site_matches": "NOT DOCUMENTED IN THIS CATALOG",
        "catalogued_negatives_are_editorial": "editorial" in catalog.get("provenance", "").lower(),
        "interpretation": [
            "The catalog tests Earth environmental separation from chosen humid/vegetated controls.",
            "Its own geology-labelled analog sites are excluded from headline AUC.",
            "This catalog does not contain independently blinded Earth-Mars matched site labels.",
            "A reported AUC of 1.00 here is not E001 cross-body analogue recovery evidence.",
            "Existence of a public global map/score baseline weakens UI-only uniqueness, not the value of independent scientific validation.",
        ],
        "claim_state": {
            "public_source_control_structure": "SUPPORTED BY PINNED SOURCE AUDIT",
            "external_roc_auc": "SELF_REPORTED_NOT_INDEPENDENTLY_REPRODUCED",
            "cross_body_similarity": "NOT YET PROVEN",
            "e001_known_site_recovery": "NOT YET MEASURED",
            "challenge_superiority": "NOT YET PROVEN",
        },
    }


def run() -> dict:
    raw = {path: download(path) for path in FILES}
    result = audit(
        json.loads(raw["data/known_analogs.json"]),
        raw["src/compute/validation.py"].decode("utf-8"),
        raw["README.md"].decode("utf-8"),
    )
    result["source_sha256"] = {
        path: hashlib.sha256(blob).hexdigest() for path, blob in raw.items()
    }
    return result


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
