"""E397: exact geography-only null on a pinned public Earth analogue catalog.

Exploratory source-selection diagnostic, not planetary recovery.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
from urllib.request import Request, urlopen

SOURCE_COMMIT = "f6c53ba50a9379d1c06f610b0e598395a0a54b43"
SOURCE_BLOB = "d75240ce203ddb00b2d9186e7981ab90720ff9a3"
SOURCE_LENGTH = 6500
SOURCE_URL = ("https://raw.githubusercontent.com/Yakiyo/terra-nova/"
              + SOURCE_COMMIT + "/data/known_analogs.json")
FEATURES = (
    ("abs_lat", lambda s: abs(float(s["lat"]))),
    ("north_lat", lambda s: float(s["lat"])),
    ("negative_abs_lat", lambda s: -abs(float(s["lat"]))),
    ("west_lon", lambda s: -float(s["lon"])),
    ("abs_lon", lambda s: abs(float(s["lon"]))),
)


def midranks(values: list[float]) -> list[float]:
    """Return 1-based midranks, retaining exact tied-score half credit."""
    if not values or not all(math.isfinite(v) for v in values):
        raise ValueError("nonfinite or empty score vector")
    ordered = sorted(enumerate(values), key=lambda pair: pair[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(values):
        j = i + 1
        while j < len(values) and ordered[j][1] == ordered[i][1]:
            j += 1
        for _, item in enumerate(ordered[i:j]):
            ranks[item[0]] = (i + j + 1) / 2
        i = j
    return ranks


def audit(catalog: dict, *, allow_toy: bool = False) -> dict:
    positives = catalog["sites"]
    negatives = catalog["negatives"]
    k, m = len(positives), len(negatives)
    if k == 0 or m == 0 or (not allow_toy and (k, m) != (12, 8)):
        raise ValueError("unexpected source role counts")
    sites = positives + negatives
    names = [s["name"] for s in sites]
    if len(set(names)) != len(names):
        raise ValueError("duplicate site identity")
    for s in sites:
        lat, lon = float(s["lat"]), float(s["lon"])
        if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("invalid coordinate")
    if not allow_toy and (sum(s["kind"] == "environment" for s in positives) != 8
                          or sum(s["kind"] == "geology" for s in positives) != 4):
        raise ValueError("unexpected source-positive strata")
    ranked = [(name, midranks([fn(s) for s in sites])) for name, fn in FEATURES]
    offset = k * (k + 1) / 2
    denominator = k * m
    observed = [(sum(r[:k]) - offset) / denominator for _, r in ranked]
    counts = [0] * len(ranked)
    maximum_count = 0
    observed_max = max(observed)
    total = 0
    for indices in itertools.combinations(range(k + m), k):
        total += 1
        permutation_max = -1.0
        for j, (_, ranks) in enumerate(ranked):
            score = (sum(ranks[i] for i in indices) - offset) / denominator
            if score >= observed[j] - 1e-12:
                counts[j] += 1
            permutation_max = max(permutation_max, score)
        if permutation_max >= observed_max - 1e-12:
            maximum_count += 1
    return {
        "experiment": "E397_EXACT_GEOGRAPHIC_CONTROL_NULL",
        "source_commit": SOURCE_COMMIT,
        "source_blob_sha1": SOURCE_BLOB,
        "positive_sites": k,
        "editorial_negatives": m,
        "permutations": total,
        "features": {name: {"auc": observed[j], "exceedances": counts[j],
                            "exact_one_sided_p": counts[j] / total}
                     for j, (name, _) in enumerate(ranked)},
        "max_feature_auc": observed_max,
        "max_feature_exceedances": maximum_count,
        "five_feature_familywise_p": maximum_count / total,
        "interpretation": "Exploratory fixed-catalog label-exchangeability sensitivity only; no independent labels or planetary recovery.",
        "claim_states": {"geographic_source_selection": "CANDIDATE CONFOUND, NOT PROVEN",
                         "e001_known_site_recovery": "NOT YET MEASURED",
                         "cross_body_similarity": "NOT YET PROVEN",
                         "challenge_superiority": "NOT YET PROVEN"},
    }


def fetch_pinned_catalog() -> dict:
    with urlopen(Request(SOURCE_URL, headers={"User-Agent": "NASA-E397-Research/1.0"}), timeout=30) as response:
        if response.geturl() != SOURCE_URL:
            raise ValueError("unexpected source redirect")
        raw = response.read(SOURCE_LENGTH + 1)
    digest = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if len(raw) != SOURCE_LENGTH or digest != SOURCE_BLOB:
        raise ValueError("source identity mismatch")
    return json.loads(raw)


if __name__ == "__main__":
    print(json.dumps(audit(fetch_pinned_catalog()), indent=2, sort_keys=True, allow_nan=False))
