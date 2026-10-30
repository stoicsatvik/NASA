"""E411: frozen E193 challenge-ranking criterion ablation and source-index audit.

This is an analysis of analyst ratings, NOT empirical challenge win probabilities.
The 14-title index is transcribed from the 2026 HackAthlone local-event
summary listing (https://hackathlone.com/challenges), checked 2026-10-30.
Official full statements/resources were not independently retrieved for all 14.
No competition solution is implemented.
"""
from __future__ import annotations

import ast
import json
from decimal import Decimal
from pathlib import Path

OFFICIAL_INDEX_TITLES = (
    "Abandoned but not Forgotten: Storytelling about NASA's Discarded Equipment on the Moon and Mars",
    "Be An Earth System Trend Detective!",
    "Build a Junior Astronaut Mission Trainer",
    "Create Health Monitoring Software for Astronauts on Space Missions",
    "Dancing with the SARs",
    "Field Shift: Adapting Farms with NASA Data",
    "Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity Combustion Data",
    "Harmonization of MODIS and VIIRS Hot Spots",
    "Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars",
    "Interplanetary Survival Guide: Martian Map",
    "Lunar Landing Site Navigator",
    "Planet X and SPHEREx",
    "Space Mission Design Game",
    "The Earth Information Jukebox",
)

PRIOR_ALIASES = {
    "Planetary analogues": OFFICIAL_INDEX_TITLES[8],
    "MODIS/VIIRS hotspots": OFFICIAL_INDEX_TITLES[7],
    "Earth trend detective": OFFICIAL_INDEX_TITLES[1],
    "Field Shift farms": OFFICIAL_INDEX_TITLES[5],
    "Dancing with the SARs": OFFICIAL_INDEX_TITLES[4],
    "Planet X / SPHEREx": OFFICIAL_INDEX_TITLES[11],
    "Flame in Freefall": OFFICIAL_INDEX_TITLES[6],
    "Martian survival map": OFFICIAL_INDEX_TITLES[9],
    "Astronaut health software": OFFICIAL_INDEX_TITLES[3],
    "Earth information jukebox": OFFICIAL_INDEX_TITLES[13],
    "Space mission design game": OFFICIAL_INDEX_TITLES[12],
    "Junior astronaut trainer": OFFICIAL_INDEX_TITLES[2],
    "Discarded hardware stories": OFFICIAL_INDEX_TITLES[0],
}

CRITERIA = (
    "science", "validation", "unique_evidence", "demo",
    "local_access", "team_fit", "speed",
)


def frozen_e193_inputs():
    """Parse historical literal values without importing NumPy or changing E193."""
    path = Path(__file__).with_name("e193_challenge_sensitivity.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    candidates = weights = None
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if target.id == "CANDIDATES":
            candidates = ast.literal_eval(node.value)
        elif target.id == "WEIGHTS":
            if not isinstance(node.value, ast.Call) or len(node.value.args) != 1:
                raise ValueError("historical weights no longer literal")
            weights = ast.literal_eval(node.value.args[0])
    if candidates is None or weights is None:
        raise ValueError("missing frozen E193 inputs")
    if len(candidates) != 14 or len(weights) != 7:
        raise ValueError("unexpected E193 cohort")
    w = tuple(Decimal(str(x)) for x in weights)
    if sum(w) != 1:
        raise ValueError("weights do not sum to one")
    return {name: tuple(Decimal(str(x)) for x in values) for name, values in candidates.items()}, w


def score(values, weights):
    return sum((v * w for v, w in zip(values[:7], weights)), Decimal(0)) - sum(values[7:])


def audit():
    candidates, weights = frozen_e193_inputs()
    covered = set(PRIOR_ALIASES.values())
    missing = sorted(set(OFFICIAL_INDEX_TITLES) - covered)
    stale = sorted(set(candidates) - set(PRIOR_ALIASES))
    if len(set(OFFICIAL_INDEX_TITLES)) != 14:
        raise ValueError("duplicate index title")
    base = {name: score(values, weights) for name, values in candidates.items()}
    analog = "Planetary analogues"
    competitor = max((n for n in base if n != analog), key=lambda n: (base[n], n))
    gap = base[competitor] - base[analog]
    validation_required = candidates[analog][1] + gap / weights[1]
    ablations = {}
    for i, axis in enumerate(CRITERIA):
        reduced = list(weights)
        reduced[i] = Decimal(0)
        normalizer = sum(reduced)
        reduced = [v / normalizer for v in reduced]
        values = {name: score(row, reduced) for name, row in candidates.items()}
        ablations[axis] = {
            "winner": max(values, key=lambda n: (values[n], n)),
            "analogue_rank": 1 + sum(v > values[analog] for v in values.values()),
            "analogue_score": str(values[analog].quantize(Decimal("0.000001"))),
        }
    return {
        "schema": "nasa/e411/frozen-challenge-criterion-ablation/v1",
        "source": "https://hackathlone.com/challenges",
        "source_scope": "local-event mirror of official 2026 summaries, NOT all independently fetched full statements",
        "index_title_count": len(OFFICIAL_INDEX_TITLES),
        "e193_candidate_count": len(candidates),
        "matched_prior_aliases": len(covered),
        "missing_from_prior": missing,
        "stale_prior_names": stale,
        "base_analogue_rank": 1 + sum(v > base[analog] for v in base.values()),
        "base_analogue_score": str(base[analog]),
        "base_best_competitor": competitor,
        "base_best_competitor_score": str(base[competitor]),
        "gap_to_best_competitor": str(gap),
        "analogue_validation_score_current": str(candidates[analog][1]),
        "analogue_validation_score_for_tie_if_all_else_fixed": str(validation_required),
        "leave_one_criterion_out": ablations,
        "limitations": [
            "Every numerical rating and penalty is an E193 analyst assumption.",
            "Renormalized criterion ablations are sensitivity scenarios, not evidence of win probability.",
            "Replacing the stale CLPS name requires a NEW lunar navigator rating, not a silent relabel.",
            "Full official statements and resource links for all 14 were not independently retrieved.",
            "No E001 known-site recovery or cross-body similarity was measured.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
