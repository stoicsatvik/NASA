"""E437: challenge-choice sensitivity to FIRMS archive access assumptions.

Arithmetic on frozen E193 *subjective* ratings. Not a measurement of
NASA judging, dataset access, win probabilities, or a competition solution.
"""
from __future__ import annotations

import json
from decimal import Decimal


def score(row, weights):
    """Seven 0-10 analyst axes followed by two nonnegative penalties."""
    if len(row) != 9 or len(weights) != 7 or sum(weights) != 1:
        raise ValueError("invalid frozen scorecard shape or weights")
    if any(not v.is_finite() for v in (*row, *weights)):
        raise ValueError("nonfinite rating or weight")
    if any(not 0 <= v <= 10 for v in row[:7]):
        raise ValueError("criterion rating outside 0-10")
    if any(not 0 <= v <= 2 for v in row[7:]):
        raise ValueError("penalty outside 0-2")
    return sum((a * b for a, b in zip(row[:7], weights)), Decimal(0)) - sum(row[7:])


def audit(candidates, weights):
    """Hold every old rating fixed except a declared MODIS validation stress.

    The stale CLPS label is NOT silently renamed Lunar Landing Site Navigator.
    This analysis remains conditional on the historical E193 14-label table.
    """
    required = ("Planetary analogues", "MODIS/VIIRS hotspots", "Earth trend detective", "CLPS lunar browser")
    if any(name not in candidates for name in required):
        raise ValueError("historical E193 candidate identity changed")
    base = {name: score(row, weights) for name, row in candidates.items()}
    analog = base["Planetary analogues"]
    scenarios = []
    for validation in (Decimal(8), Decimal(6), Decimal(4), Decimal(0)):
        variant = dict(base)
        row = list(candidates["MODIS/VIIRS hotspots"])
        row[1] = validation
        variant["MODIS/VIIRS hotspots"] = score(row, weights)
        scenarios.append({
            "modis_validation_assumption": str(validation),
            "modis_score": str(variant["MODIS/VIIRS hotspots"]),
            "planetary_rank_in_stale_14": 1 + sum(v > analog for v in variant.values()),
            "highest_scoring_old_label": max(sorted(variant), key=variant.get),
        })
    thresholds = {}
    for name in ("MODIS/VIIRS hotspots", "Earth trend detective"):
        if weights[1] <= 0:
            raise ValueError("validation weight must be positive")
        thresholds[name] = str(candidates["Planetary analogues"][1] + (base[name] - analog) / weights[1])
    return {
        "experiment": "E437 FIRMS archive access decision sensitivity",
        "historical_candidate_count": len(candidates),
        "historical_analogue_score": str(analog),
        "modis_validation_stress": scenarios,
        "planetary_validation_for_tie": thresholds,
        "current_challenge_coverage": "13/14 unambiguous; CLPS lunar browser is NOT Lunar Landing Site Navigator",
        "sources": {
            "official_lunar_navigator": "https://www.spaceappschallenge.org/2026/challenges/lunar-landing-site-navigator/",
            "official_firms_archive": "https://firms.modaps.eosdis.nasa.gov/download/",
            "official_firms_active_fire": "https://firms.modaps.eosdis.nasa.gov/content/active_fire/",
            "official_gistemp": "https://data.giss.nasa.gov/gistemp/",
        },
        "limitations": [
            "E193 ratings and penalties are analyst assumptions, not measurements.",
            "Changing MODIS validation score is a sensitivity experiment, not a new justified rating.",
            "Official FIRMS archive advertises Earthdata/email authentication and science-quality lag; no data downloaded in E437.",
            "No full fourteen-statement independent source audit or new Lunar Navigator rating was performed.",
            "No E001 known-site recovery, cross-body similarity, or competition outcome measured.",
        ],
    }


if __name__ == "__main__":
    from .e411_challenge_validation_ablation import frozen_e193_inputs
    candidates, weights = frozen_e193_inputs()
    print(json.dumps(audit(candidates, weights), indent=2, sort_keys=True))
