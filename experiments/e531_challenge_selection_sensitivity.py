"""Deterministic sensitivity screen for the 2026 Space Apps challenge shortlist.

This perturbs the existing subjective scorecard; it is not a probability model
for judging outcomes or challenge success.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

CHALLENGES = [
    "Abandoned but Not Forgotten",
    "Be An Earth System Trend Detective",
    "Junior Astronaut Mission Trainer",
    "CLPS Lunar Mission Browser",
    "Astronaut Health Monitoring Software",
    "Dancing with the SARs",
    "Field Shift: Adapting Farms with NASA Data",
    "Flame in Freefall",
    "Harmonization of MODIS and VIIRS Hot Spots",
    "Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars",
    "Interplanetary Survival Guide: Martian Map",
    "Planet X and SPHEREx",
    "Space Mission Design Game",
    "The Earth Information Jukebox",
]

# Columns: public-data readiness, measurable validation, portfolio reuse,
# technical differentiation, 48-hour feasibility. Transcribed from the
# source-pinned 2026-11-11 challenge-selection screen.
SCORES = [
    [4.5, 3.0, 2.0, 1.5, 4.5],
    [4.5, 4.0, 3.5, 2.5, 4.0],
    [3.0, 2.5, 2.0, 2.0, 3.0],
    [4.0, 4.0, 4.0, 3.0, 4.0],
    [2.5, 2.0, 1.5, 2.5, 2.0],
    [3.0, 3.5, 3.0, 4.0, 2.5],
    [3.5, 3.5, 4.0, 3.5, 3.0],
    [4.0, 3.0, 2.0, 2.0, 4.0],
    [4.5, 4.5, 3.5, 3.0, 4.0],
    [2.0, 1.5, 5.0, 5.0, 2.0],
    [4.0, 4.0, 4.5, 3.5, 4.5],
    [3.0, 2.5, 2.0, 4.0, 2.0],
    [3.5, 2.5, 3.0, 2.0, 3.0],
    [4.0, 2.5, 2.0, 2.0, 4.0],
]
BASE_WEIGHTS = [0.25, 0.25, 0.20, 0.15, 0.15]
MARTIAN_INDEX = 10
MODIS_INDEX = 8


def run_sensitivity(amplitude: float, draws: int = 200_000, seed: int = 526) -> dict:
    if not 0 <= amplitude <= 2:
        raise ValueError("score perturbation amplitude must be in [0, 2]")
    if draws < 1:
        raise ValueError("draws must be positive")

    rng = random.Random(seed)
    wins = [0] * len(CHALLENGES)
    differences = []
    for _ in range(draws):
        weights = [base * rng.uniform(0.8, 1.2) for base in BASE_WEIGHTS]
        total_weight = sum(weights)
        weights = [weight / total_weight for weight in weights]

        totals = []
        for row in SCORES:
            perturbed = [
                min(5.0, max(1.0, score + rng.uniform(-amplitude, amplitude)))
                for score in row
            ]
            totals.append(sum(score * weight for score, weight in zip(perturbed, weights)))

        winner = max(range(len(CHALLENGES)), key=totals.__getitem__)
        wins[winner] += 1
        differences.append(totals[MARTIAN_INDEX] - totals[MODIS_INDEX])

    differences.sort()

    def quantile(p: float) -> float:
        return differences[int(p * (draws - 1))]

    return {
        "score_perturbation_amplitude": amplitude,
        "draws": draws,
        "seed": seed,
        "weight_perturbation": "independent multiplicative uniform [0.8, 1.2], then renormalized",
        "score_perturbation": f"independent uniform [-{amplitude}, +{amplitude}], clipped to [1, 5]",
        "winner_pct": {
            CHALLENGES[index]: round(100.0 * count / draws, 2)
            for index, count in enumerate(wins) if count
        },
        "martian_minus_modis_score_difference_quantiles": {
            "p05": round(quantile(0.05), 4),
            "p50": round(quantile(0.50), 4),
            "p95": round(quantile(0.95), 4),
        },
    }


def run_all(draws: int = 200_000) -> dict:
    return {
        "experiment": "E531",
        "source": "research/CHALLENGE_SELECTION_SCREEN_20261111.md",
        "challenge_count": len(CHALLENGES),
        "base_weights": dict(zip(
            ["data_readiness", "validation", "portfolio_reuse", "differentiation", "feasibility"],
            BASE_WEIGHTS,
        )),
        "method_warning": (
            "Heuristic robustness diagnostic only. Winner frequencies are not probabilities "
            "of judging success, challenge quality, or actual project outcomes."
        ),
        "scenarios": [run_sensitivity(amplitude, draws=draws) for amplitude in (0.25, 0.50, 0.75)],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draws", type=int, default=200_000)
    parser.add_argument("--output", type=Path, default=Path("research/results/E531_CHALLENGE_SELECTION_SENSITIVITY_20261111.json"))
    args = parser.parse_args()
    result = run_all(draws=args.draws)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
