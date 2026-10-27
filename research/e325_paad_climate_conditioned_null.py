"""E325: Is PAAD spatial raw-token dependence explained by climate labels?

Earth-only exploratory conditional permutation. Climate labels and dune codes
are source metadata, not physically harmonized Earth-Mars descriptors.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import random
import re
from collections import defaultdict
from pathlib import Path

from research.e319_paad_mars_codebook_overlap import retrieve_paad
from research.e323_paad_spatial_label_null import (
    read_labeled_sites, nearest_indices, mean_agreement,
)

CLIMATE_FIELD = "Köppen_Geiger_Climate_Classification"
THRESHOLDS_KM = (25, 50, 100)
PERMUTATIONS = 999
SEED = 325


def climate_family(raw: str) -> str:
    """Only recognize an unambiguous single Köppen-like code; do not guess."""
    if re.fullmatch(r"[ABCDE][A-Z0-9]*", raw.upper()):
        return raw[0].upper()
    return "UNCLASSIFIED"


def read_climate_sites(raw: bytes) -> list[dict]:
    sites = read_labeled_sites(raw)
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    if not reader.fieldnames or CLIMATE_FIELD not in reader.fieldnames:
        raise ValueError("official climate field missing")
    climates = {}
    for row in reader:
        name = (row.get("Field_Site") or "").strip()
        if not name:
            continue
        value = (row.get(CLIMATE_FIELD) or "").strip()
        if not value or name in climates:
            raise ValueError("missing climate label or duplicate site")
        climates[name] = value
    if set(climates) != {s["name"] for s in sites}:
        raise ValueError("climate and dune site identities disagree")
    for site in sites:
        full = climates[site["name"]]
        site["climate_full"] = full
        site["climate_family"] = climate_family(full)
    return sites


def groups_for(sites: list[dict], scheme: str) -> list[list[int]]:
    groups = defaultdict(list)
    for i, site in enumerate(sites):
        if scheme == "global":
            key = "ALL"
        elif scheme in ("climate_full", "climate_family"):
            key = site[scheme]
        else:
            raise ValueError("unknown permutation scheme")
        groups[key].append(i)
    return [groups[k] for k in sorted(groups)]


def shuffle_within_groups(tokens: list[frozenset[str]],
                          groups: list[list[int]],
                          rng: random.Random) -> list[frozenset[str]]:
    result = tokens[:]
    for indices in groups:
        values = [tokens[i] for i in indices]
        rng.shuffle(values)
        for i, value in zip(indices, values):
            result[i] = value
    return result


def _summary(values: list[float], observed: float | None) -> dict:
    if observed is None:
        return {"observed": None, "upper_tail_p": None, "null": None}
    if not values or not all(math.isfinite(v) for v in values):
        raise ValueError("invalid null sample")
    ordered = sorted(values)
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return {
        "observed": observed,
        "upper_tail_p": (1 + sum(v >= observed - 1e-12 for v in values))
                        / (len(values) + 1),
        "null": {
            "mean": mean,
            "standard_deviation": math.sqrt(variance),
            "p025": ordered[int(0.025 * (len(values) - 1))],
            "p975": ordered[int(0.975 * (len(values) - 1))],
            "degenerate": max(values) - min(values) < 1e-12,
        },
    }


def audit(sites: list[dict], permutations: int = PERMUTATIONS,
          seed: int = SEED) -> dict:
    if not 1 <= permutations <= 9999:
        raise ValueError("invalid permutation count")
    if len(sites) < 3 or len({s["name"] for s in sites}) != len(sites):
        raise ValueError("invalid site identities")
    sites = sorted(sites, key=lambda s: s["name"])
    if any(not s.get("climate_full") or not s.get("climate_family")
           or not isinstance(s["tokens"], frozenset) or not s["tokens"]
           for s in sites):
        raise ValueError("incomplete source labels")
    tokens = [s["tokens"] for s in sites]
    neighbor_sets = {"name_only": nearest_indices(sites, None)}
    neighbor_sets.update({
        f"blocked_{radius}_km": nearest_indices(sites, radius)
        for radius in THRESHOLDS_KM
    })
    observed_means = {
        key: mean_agreement(tokens, indices)[0]
        for key, indices in neighbor_sets.items()
    }
    observed = {"name_only_jaccard": observed_means["name_only"]}
    for radius in THRESHOLDS_KM:
        key = f"blocked_{radius}_km"
        blocked = observed_means[key]
        observed[f"drop_{radius}_km"] = (
            observed_means["name_only"] - blocked if blocked is not None else None
        )
    schemes = {}
    for offset, scheme in enumerate(("global", "climate_full", "climate_family")):
        groups = groups_for(sites, scheme)
        rng = random.Random(seed + offset)
        nulls = {key: [] for key in observed}
        for _ in range(permutations):
            shuffled = shuffle_within_groups(tokens, groups, rng)
            means = {
                key: mean_agreement(shuffled, indices)[0]
                for key, indices in neighbor_sets.items()
            }
            nulls["name_only_jaccard"].append(means["name_only"])
            for radius in THRESHOLDS_KM:
                key = f"blocked_{radius}_km"
                if means[key] is not None:
                    nulls[f"drop_{radius}_km"].append(
                        means["name_only"] - means[key]
                    )
        schemes[scheme] = {
            "strata_count": len(groups),
            "singleton_strata": sum(len(g) == 1 for g in groups),
            "permutable_sites": sum(len(g) for g in groups if len(g) > 1),
            "largest_stratum": max(map(len, groups)),
            "metrics": {
                key: _summary(nulls[key], value)
                for key, value in observed.items()
            },
        }
    return {
        "experiment": "E325_PAAD_CLIMATE_CONDITIONED_LEXICAL_NULL",
        "sites": len(sites),
        "permutations_per_scheme": permutations,
        "seed": seed,
        "climate_raw_distinct": len({s["climate_full"] for s in sites}),
        "climate_family_counts": {
            k: sum(s["climate_family"] == k for s in sites)
            for k in sorted({s["climate_family"] for s in sites})
        },
        "unclassified_family_count": sum(
            s["climate_family"] == "UNCLASSIFIED" for s in sites
        ),
        "observed": observed,
        "conditional_permutations": schemes,
        "e001_known_site_recovery": "NOT YET MEASURED",
        "cross_body_similarity": "NOT YET PROVEN",
        "limitations": [
            "Earth-only raw dune-type tokens; PAAD morphology codebook not harmonized.",
            "Köppen class is an Earth climatic proxy, not a Martian climate feature.",
            "Within-stratum exchangeability is an assumption, not a physical law.",
            "Singleton climate strata cannot be permuted; degenerate nulls are not evidence.",
            "Multiple tested thresholds and stratifications are exploratory.",
            "No independently matched positive/negative Earth-Mars site pairs.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw, source = retrieve_paad()
    result = audit(read_climate_sites(raw))
    result["source_receipt"] = source
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({
        "sites": result["sites"],
        "climate_family_counts": result["climate_family_counts"],
        "observed": result["observed"],
        "conditional_permutations": result["conditional_permutations"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
