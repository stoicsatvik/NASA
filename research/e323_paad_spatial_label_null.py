"""E323: Does geographic proximity inflate PAAD raw-token nearest-site agreement?

This is a within-Earth *lexical* label-dependence falsification, not an
Earth-Mars analogue model. Source code semantics and physical truth unverified.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import random
from pathlib import Path

from research.e319_paad_mars_codebook_overlap import retrieve_paad, split_raw_codes
from research.e320_paad_spatial_holdout import connected_groups, distance_km

THRESHOLDS_KM = (25, 50, 100)
PERMUTATIONS = 999
SEED = 323


def read_labeled_sites(raw: bytes) -> list[dict]:
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    required = {"Field_Site", "Dune_Type", "Center_Latitude", "Center_Longitude"}
    if not reader.fieldnames or not required <= set(reader.fieldnames):
        raise ValueError("missing required source columns")
    sites, seen = [], set()
    for row in reader:
        if not any((v or "").strip() for v in row.values() if isinstance(v, str)):
            continue
        name = (row.get("Field_Site") or "").strip()
        if not name or name in seen:
            raise ValueError("missing or duplicate site identity")
        seen.add(name)
        try:
            lat = float(row["Center_Latitude"])
            lon = float(row["Center_Longitude"])
        except (ValueError, TypeError) as exc:
            raise ValueError("invalid coordinate") from exc
        if not (math.isfinite(lat) and math.isfinite(lon)
                and -90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("invalid coordinate")
        tokens = frozenset(split_raw_codes((row.get("Dune_Type") or "").strip()))
        if not tokens:
            raise ValueError("empty dune-type token set")
        sites.append({"name": name, "lat": lat, "lon": lon, "tokens": tokens})
        if len(sites) > 5000:
            raise ValueError("source row bound exceeded")
    if len(sites) < 3:
        raise ValueError("at least three sites required")
    return sorted(sites, key=lambda x: x["name"])


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    return len(a & b) / len(a | b)


def nearest_indices(sites: list[dict], threshold_km: float | None) -> list[int | None]:
    n = len(sites)
    d = [[0.0] * n for _ in range(n)]
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            x = distance_km((sites[i]["lat"], sites[i]["lon"]),
                            (sites[j]["lat"], sites[j]["lon"]))
            d[i][j] = d[j][i] = x
            if threshold_km is not None and x <= threshold_km:
                edges.append((i, j))
    groups = connected_groups(n, edges)
    group_of = {i: k for k, group in enumerate(groups) for i in group}
    return [
        min((j for j in range(n) if j != i
             and (threshold_km is None or group_of[i] != group_of[j])),
            key=lambda j: (d[i][j], sites[j]["name"]), default=None)
        for i in range(n)
    ]


def mean_agreement(tokens: list[frozenset[str]],
                   neighbors: list[int | None]) -> tuple[float | None, int, float | None]:
    values = [jaccard(tokens[i], tokens[j])
              for i, j in enumerate(neighbors) if j is not None]
    hits = [bool(tokens[i] & tokens[j])
            for i, j in enumerate(neighbors) if j is not None]
    if not values:
        return None, 0, None
    return sum(values) / len(values), len(values), sum(hits) / len(hits)


def audit(sites: list[dict], permutations: int = PERMUTATIONS,
          seed: int = SEED) -> dict:
    if permutations < 1 or permutations > 9999:
        raise ValueError("permutation count outside bounded range")
    names = [x["name"] for x in sites]
    if len(set(names)) != len(names) or len(sites) < 3:
        raise ValueError("invalid site identities")
    sites = sorted(sites, key=lambda x: x["name"])
    tokens = [x["tokens"] for x in sites]
    if any(not isinstance(t, frozenset) or not t for t in tokens):
        raise ValueError("invalid token set")
    near = nearest_indices(sites, None)
    near_mean, n_near, near_hit = mean_agreement(tokens, near)
    blocked = {str(k): nearest_indices(sites, k) for k in THRESHOLDS_KM}
    actual = {}
    for k, indices in blocked.items():
        m, n, hit = mean_agreement(tokens, indices)
        actual[k] = {
            "eligible_holdouts": n,
            "excluded_holdouts": len(sites) - n,
            "nearest_outside_component_jaccard": m,
            "nearest_outside_component_any_token_hit_rate": hit,
            "unblocked_minus_blocked_jaccard": (near_mean - m) if m is not None else None,
        }
    rng = random.Random(seed)
    null_near = []
    null_drop = {k: [] for k in blocked}
    for _ in range(permutations):
        shuffled = tokens[:]
        rng.shuffle(shuffled)
        x, _, _ = mean_agreement(shuffled, near)
        null_near.append(x)
        for k, indices in blocked.items():
            y, _, _ = mean_agreement(shuffled, indices)
            if y is not None:
                null_drop[k].append(x - y)
    def upper_p(observed: float, null: list[float]) -> float:
        return (1 + sum(x >= observed - 1e-12 for x in null)) / (len(null) + 1)
    def null_summary(null: list[float]) -> dict:
        sorted_null = sorted(null)
        return {"mean": sum(null) / len(null),
                "p025": sorted_null[int(0.025 * (len(null) - 1))],
                "p975": sorted_null[int(0.975 * (len(null) - 1))]}
    for k, values in null_drop.items():
        if values and actual[k]["unblocked_minus_blocked_jaccard"] is not None:
            actual[k]["label_permutation_null"] = null_summary(values)
            actual[k]["one_sided_upper_tail_p"] = upper_p(
                actual[k]["unblocked_minus_blocked_jaccard"], values)
    return {
        "sites": len(sites), "permutations": permutations, "seed": seed,
        "raw_token_vocab_size": len(set().union(*tokens)),
        "name_only_nearest_jaccard": near_mean,
        "name_only_nearest_any_token_hit_rate": near_hit,
        "name_only_eligible_holdouts": n_near,
        "name_only_label_permutation_null": null_summary(null_near),
        "name_only_upper_tail_p": upper_p(near_mean, null_near),
        "spatial_block_km": actual,
        "status": "EARTH_ONLY_RAW_TOKEN_SPATIAL_DEPENDENCE_AUDIT",
        "label_semantics": "UNVERIFIED",
        "earth_mars_positive_negative_pairs": "ABSENT",
        "e001_known_site_recovery": "NOT YET MEASURED",
        "cross_body_similarity": "NOT YET PROVEN",
        "limitations": [
            "PAAD dune-type abbreviations are raw source tokens, not harmonized physical labels.",
            "All records are Earth positive sites; this is not Earth-Mars analogue recovery.",
            "Permutation p-values test exchangeability of tokens across fixed coordinates only.",
            "Geodesic proximity and token agreement do not establish shared geology or provenance.",
            "Small sample and connected-component blocking may reduce eligible holdouts.",
            "All results are exploratory; no external holdout or independent negatives.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw, source = retrieve_paad()
    result = audit(read_labeled_sites(raw))
    result["source_receipt"] = source
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "sites", "raw_token_vocab_size", "name_only_nearest_jaccard",
        "name_only_upper_tail_p", "spatial_block_km")}, sort_keys=True))


if __name__ == "__main__":
    main()
