"""E418: delete each editorial negative in turn from the pinned E397 catalogue.

This is a source-selection sensitivity test, not Earth/Moon/Mars recovery.
"""
from __future__ import annotations

import itertools
import json
import math

from research.e397_geographic_control_null import (
    FEATURES,
    fetch_pinned_catalog,
    midranks,
)


def pairwise_auc(positives: list[dict], negatives: list[dict], feature) -> float:
    wins = 0.0
    for positive in positives:
        for negative in negatives:
            a, b = feature(positive), feature(negative)
            wins += 1.0 if a > b else 0.5 if a == b else 0.0
    return wins / (len(positives) * len(negatives))


def audit(catalog: dict, *, allow_toy: bool = False) -> dict:
    positives = catalog["sites"]
    negatives = catalog["negatives"]
    k = len(positives)
    if k < 2 or len(negatives) < 3 or (not allow_toy and (k, len(negatives)) != (12, 8)):
        raise ValueError("unexpected source population")
    sites = positives + negatives
    if len({site["name"] for site in sites}) != len(sites):
        raise ValueError("duplicate site identity")
    for site in sites:
        lat, lon = float(site["lat"]), float(site["lon"])
        if not (math.isfinite(lat) and math.isfinite(lon)
                and -90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("invalid coordinate")

    rows = []
    for omitted in range(len(negatives)):
        controls = [site for i, site in enumerate(negatives) if i != omitted]
        combined = positives + controls
        m = len(controls)
        denominator = k * m
        offset = k * (k + 1) / 2
        ranked = [(name, midranks([feature(site) for site in combined]))
                  for name, feature in FEATURES]
        observed = {}
        for name, feature in FEATURES:
            rank_vector = dict(ranked)[name]
            rank_auc = (sum(rank_vector[:k]) - offset) / denominator
            direct_auc = pairwise_auc(positives, controls, feature)
            if abs(rank_auc - direct_auc) > 1e-12:
                raise AssertionError("rank/pairwise AUC mismatch")
            observed[name] = rank_auc

        observed_max = max(observed.values())
        exceedances = 0
        permutations = 0
        for selected in itertools.combinations(range(k + m), k):
            permutations += 1
            maximum = max(
                (sum(ranks[index] for index in selected) - offset) / denominator
                for _, ranks in ranked
            )
            if maximum >= observed_max - 1e-12:
                exceedances += 1

        rows.append({
            "omitted_negative": negatives[omitted]["name"],
            "feature_auc": observed,
            "max_feature_auc": observed_max,
            "familywise_exceedances": exceedances,
            "permutations": permutations,
            "familywise_conditional_p": exceedances / permutations,
        })
    return {
        "experiment": "E418_GEOGRAPHIC_NEGATIVE_DELETION",
        "source_commit": "f6c53ba50a9379d1c06f610b0e598395a0a54b43",
        "source_blob_sha1": "d75240ce203ddb00b2d9186e7981ab90720ff9a3",
        "positives": k,
        "editorial_negatives": len(negatives),
        "features": [name for name, _ in FEATURES],
        "rows": rows,
        "limitations": [
            "Editorial negative deletion is a source-selection sensitivity, not an independent validation.",
            "Conditional label exchangeability is hypothetical, not a randomized source design.",
            "No planetary descriptors, independent controls or E001 known-site recovery measured.",
        ],
        "claim_states": {
            "geographic_catalog_sensitivity": "SUPPORTED FOR PINNED PUBLIC CATALOG",
            "e001_known_site_recovery": "NOT YET MEASURED",
            "cross_body_similarity": "NOT YET PROVEN",
            "challenge_superiority": "NOT YET PROVEN",
        },
    }


if __name__ == "__main__":
    print(json.dumps(audit(fetch_pinned_catalog()), sort_keys=True, indent=2,
                     allow_nan=False))
