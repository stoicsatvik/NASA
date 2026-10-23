"""E193 pre-event challenge-selection assumption sensitivity, NOT a submission.

All ratings are analyst assumptions based on the 14 official 2026 summaries.
Scenario frequencies are not win probabilities or NASA-endorsed rankings.
Run: python research/e193_challenge_sensitivity.py
"""
import json
from pathlib import Path
import numpy as np

CRITERIA = ["science", "validation", "unique_evidence", "demo", "local_access", "team_fit", "speed"]
WEIGHTS = np.array([.22, .20, .18, .15, .10, .10, .05])
# Seven subjective 0-10 criteria, followed by cloneability/dependency penalties.
CANDIDATES = {
    "Planetary analogues": [9,4,7,9,7,6,4,.8,1.5],
    "MODIS/VIIRS hotspots": [8,8,4,8,5,8,7,.8,.7],
    "Earth trend detective": [8,8,3,7,5,8,8,.8,.6],
    "Field Shift farms": [7,6,8,8,8,6,5,.8,1.5],
    "Dancing with the SARs": [9,6,5,9,6,7,6,1.0,1.4],
    "CLPS lunar browser": [8,6,3,8,3,7,6,1.1,1.1],
    "Planet X / SPHEREx": [9,5,3,9,3,6,5,1.3,1.5],
    "Flame in Freefall": [8,5,4,7,2,7,7,1.3,1.0],
    "Martian survival map": [8,5,3,9,3,7,5,1.2,1.2],
    "Astronaut health software": [7,3,3,8,2,7,6,1.5,1.8],
    "Earth information jukebox": [5,5,4,9,4,8,9,1.4,.5],
    "Space mission design game": [6,5,4,9,4,8,9,1.5,.6],
    "Junior astronaut trainer": [5,5,4,9,5,8,9,1.5,.5],
    "Discarded hardware stories": [4,6,3,8,3,8,9,1.6,.4],
}

def evaluate(seed=20261024, draws=20000, score_sd=1.0, weight_concentration=40.0):
    rng = np.random.default_rng(seed)
    names = list(CANDIDATES)
    a = np.array(list(CANDIDATES.values()), dtype=float)
    base = a[:, :7] @ WEIGHTS - a[:, 7:].sum(axis=1)
    weights = rng.dirichlet(WEIGHTS * weight_concentration, size=draws)
    scores = np.clip(a[None, :, :7] + rng.normal(0, score_sd, (draws, len(names), 7)), 0, 10)
    penalties = np.clip(a[None, :, 7:] + rng.normal(0, .30, (draws, len(names), 2)), 0, 2)
    values = np.einsum("dnc,dc->dn", scores, weights) - penalties.sum(axis=2)
    wins = np.bincount(values.argmax(axis=1), minlength=len(names)) / draws
    ranks = 1 + (values[:, :, None] < values[:, None, :]).sum(axis=2)
    i = names.index("Planetary analogues")
    return {
        "experiment": "E193 analyst-assumption sensitivity, NOT empirical win probability",
        "sources": [
            "https://hackathlone.com/challenges",
            "https://www.spaceappschallenge.org/2026/",
        ],
        "full_statements_release": "2026-10-28",
        "assumptions": {
            "seed": seed, "draws": draws, "criteria": CRITERIA,
            "weights": WEIGHTS.tolist(), "rating_sd": score_sd,
            "penalty_sd": .30, "dirichlet_weight_concentration": weight_concentration,
        },
        "candidates": [
            {
                "challenge": n, "ratings": a[j, :7].tolist(),
                "penalties": a[j, 7:].tolist(),
                "base_score": round(float(base[j]), 4),
                "scenario_top_rank_frequency": round(float(wins[j]), 5),
                "median_rank": int(np.median(ranks[:, j])),
            }
            for j, n in enumerate(names)
        ],
        "planetary": {
            "base_rank": int(1 + (base > base[i]).sum()),
            "top_rank_frequency": float(wins[i]),
            "median_rank": float(np.median(ranks[:, i])),
            "p_below_modis_viirs": float((values[:, i] < values[:, names.index("MODIS/VIIRS hotspots")]).mean()),
            "p_below_earth_trend": float((values[:, i] < values[:, names.index("Earth trend detective")]).mean()),
        },
        "limitations": [
            "All ratings and penalties are subjective analyst assumptions.",
            "Scenario frequencies are NOT empirical competition win probabilities.",
            "No project solution, real planetary raster ingestion, or E001 was performed.",
            "Full challenge statements/resources are scheduled for 2026-10-28.",
        ],
    }

if __name__ == "__main__":
    result = evaluate()
    print(json.dumps(result, indent=2))
