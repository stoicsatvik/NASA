"""E375: source-role selection stress on E369's pinned Earth-only analogue controls.

The four geology-labelled sites are POSITIVE analogue examples for a different
geological use case, not independently adjudicated planetary hard negatives.
This is a descriptive catalog-subset sensitivity audit, not E001 recovery.
"""
from __future__ import annotations

import json
import math

from research.e369_single_feature_control_baselines import auc, fetch_pinned, run


def _scores(samples: dict, sites: list[dict]) -> list[float]:
    out = []
    for site in sites:
        item = samples[site["name"]]
        score = item["score"]
        if score is None or not math.isfinite(score):
            raise ValueError("all source-pinned controls must have finite scores")
        out.append(float(score))
    return out


def audit_roles(catalog: dict, e369: dict) -> dict:
    sites, negatives = catalog["sites"], catalog["negatives"]
    if len(sites) != 12 or len(negatives) != 8:
        raise ValueError("unexpected pinned source role counts")
    if sorted(s["kind"] for s in sites) != ["environment"] * 8 + ["geology"] * 4:
        raise ValueError("unexpected site roles")
    names = [s["name"] for s in sites + negatives]
    if len(set(names)) != 20:
        raise ValueError("duplicate names")
    output = {}
    for feature in ("vegetation", "precipitation"):
        output[feature] = {}
        for mask in ("finite_only", "land_fraction_ge_0_5"):
            samples = e369["results"][feature][mask]["control_scores"]
            if set(samples) != set(names):
                raise ValueError("source scores do not match source catalog")
            controls = _scores(samples, negatives)
            body_results = {}
            for body in ("mars", "moon", "all"):
                subset = [s for s in sites if body == "all" or body in s["bodies"]]
                environment = [s for s in subset if s["kind"] == "environment"]
                geology = [s for s in subset if s["kind"] == "geology"]
                env = _scores(samples, environment)
                geo = _scores(samples, geology)
                pooled = _scores(samples, subset)
                body_results[body] = {
                    "environment_n": len(env),
                    "geology_n": len(geo),
                    "editorial_n": len(controls),
                    "environment_vs_editorial_auc": auc(env, controls),
                    "geology_vs_editorial_auc": auc(geo, controls),
                    "pooled_analogue_vs_editorial_auc": auc(pooled, controls),
                    "geology_vs_environment_auc": auc(geo, env),
                }
            output[feature][mask] = body_results
    return {
        "experiment": "E375_PINNED_CATALOG_GEOLOGY_SUBSET_STRESS",
        "source_repo": e369["source_repo"],
        "source_commit": e369["source_commit"],
        "source_sha256": e369["sha256"],
        "method": "No model fitting: exact pairwise AUC of frozen E369 Earth-only scores, retaining all 4 source-labelled geology analogues as an alternative positive stratum.",
        "results": output,
        "claim_state": {
            "earth_only_catalog_subset_sensitivity": "MEASURED_ONLY_FOR_PINNED_SOURCE",
            "geology_sites_are_negative_controls": "FALSE: THEY ARE SOURCE-LABELLED ANALOGUE EXAMPLES",
            "e001_known_site_recovery": "NOT YET MEASURED",
            "cross_body_similarity": "NOT YET PROVEN",
            "novel_analogue_discovery": "NOT YET PROVEN",
            "challenge_superiority": "NOT YET PROVEN",
        },
        "limitations": [
            "All labels and features come from the same public comparator; this is not independent evaluation.",
            "Geology-labelled sites are alternative analogue positives, not validated non-analogues.",
            "Earth-only vegetation and precipitation are not physical cross-body descriptors.",
            "Small, nonrandom site subsets and coarse rasters prevent population-level inference.",
        ],
    }


def main() -> dict:
    e369 = run()
    catalog = json.loads(fetch_pinned("data/known_analogs.json"))
    return audit_roles(catalog, e369)


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True, allow_nan=False))
