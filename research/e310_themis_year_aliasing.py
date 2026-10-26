"""E310: structural identifiability audit of E305 published THEMIS observations.

This tests whether local-time group can be separated from Mars-year effects in
the *existing published sample*. It does not estimate causal temperature effects,
retrieve raw PDS pixels, or measure planetary analogue recovery.
"""
from __future__ import annotations

import hashlib
import json
import statistics
from fractions import Fraction
from pathlib import Path

from research.e305_published_themis_time_audit import DATA, SOURCE, load, matched


def exact_rank(matrix: list[list[int]]) -> int:
    """Exact rational row rank, avoiding numerical tolerance decisions."""
    if not matrix:
        return 0
    width = len(matrix[0])
    if any(len(row) != width for row in matrix):
        raise ValueError("ragged design")
    a = [[Fraction(value) for value in row] for row in matrix]
    pivot_row = 0
    for col in range(width):
        pivot = next((i for i in range(pivot_row, len(a)) if a[i][col]), None)
        if pivot is None:
            continue
        a[pivot_row], a[pivot] = a[pivot], a[pivot_row]
        divisor = a[pivot_row][col]
        a[pivot_row] = [x / divisor for x in a[pivot_row]]
        for i in range(len(a)):
            if i != pivot_row and a[i][col]:
                factor = a[i][col]
                a[i] = [x - factor * y for x, y in zip(a[i], a[pivot_row])]
        pivot_row += 1
        if pivot_row == len(a):
            break
    return pivot_row


def analyze(rows: list[dict]) -> dict:
    if not rows:
        raise ValueError("empty observations")
    years = sorted({int(row["mars_year"]) for row in rows})
    groups = {"early_morning": [], "evening": []}
    for row in rows:
        group = "early_morning" if row["local_time_h"] < 12 else "evening"
        groups[group].append(row)
    if not all(groups.values()):
        raise ValueError("both local-time groups required")
    morning_years = {int(r["mars_year"]) for r in groups["early_morning"]}
    evening_years = {int(r["mars_year"]) for r in groups["evening"]}
    common_years = sorted(morning_years & evening_years)
    base = [[int(int(row["mars_year"]) == year) for year in years] for row in rows]
    extended = [vector + [int(row["local_time_h"] >= 12)]
                for vector, row in zip(base, rows)]
    rank_base, rank_extended = exact_rank(base), exact_rank(extended)
    identifiable = rank_extended > rank_base
    if identifiable != bool(common_years):
        raise AssertionError("unexpected time/year design identifiability")
    pairs = matched(rows, 10)
    by_id = {r["image_id"]: r for r in rows}
    cross_year = [
        abs(int(by_id[p["evening_id"]]["mars_year"]) -
            int(by_id[p["morning_id"]]["mars_year"]))
        for p in pairs
    ]
    equivalent_sse = None
    if not identifiable:
        # For ANY candidate time coefficient d, redefine each year intercept
        # a_y := mean(T | year=y) - d * evening(y).
        # Predictions and residuals are unchanged: this is an aliasing proof,
        # NOT evidence that the true year effects take these values.
        year_means = {
            year: statistics.mean(r["temperature_k"] for r in rows
                                  if int(r["mars_year"]) == year)
            for year in years
        }
        equivalent_sse = {}
        for delta in (-30, 0, 30):
            intercepts = {
                year: year_means[year] - delta * int(year in evening_years)
                for year in years
            }
            sse = sum(
                (r["temperature_k"] -
                 (intercepts[int(r["mars_year"])] +
                  delta * int(r["local_time_h"] >= 12))) ** 2
                for r in rows
            )
            equivalent_sse[str(delta)] = round(sse, 6)
        if len(set(equivalent_sse.values())) != 1:
            raise AssertionError("year/time aliasing prediction check failed")
    return {
        "n_observations": len(rows),
        "mars_years": years,
        "morning_years": sorted(morning_years),
        "evening_years": sorted(evening_years),
        "years_with_both_time_groups": common_years,
        "year_only_design_rank": rank_base,
        "year_plus_time_design_rank": rank_extended,
        "time_group_identifiable_conditional_on_year": identifiable,
        "ten_degree_season_matched_pairs": len(pairs),
        "pairs_from_different_mars_years": sum(gap > 0 for gap in cross_year),
        "paired_mars_year_gaps": cross_year,
        "observationally_equivalent_sse_by_assumed_time_coefficient_k":
            equivalent_sse,
        "interpretation": (
            "Local-time group is exactly aliased with Mars-year indicators in "
            "this sample; matched solar longitude does not identify a local-time "
            "temperature effect."
            if not identifiable else
            "Some within-year time-group contrast exists, but other confounding remains."
        ),
    }


def run(path: Path = DATA) -> dict:
    rows = load(path)
    return {
        "schema": "nasa/e310/themis-year-aliasing/v1",
        "source": SOURCE,
        "data_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "measurement_status": "SECONDARY_PUBLISHED_REAL_OBSERVATIONS",
        "result": analyze(rows),
        "claim": "Structural time/year nonidentifiability in the cited 24-row sample",
        "limitations": [
            "Published derived temperatures, manually transcribed; no raw PDS pixels.",
            "Exact rank/aliasing is a design property, not a physical year-effect model.",
            "Solar-longitude matching does not control Mars year or dust conditions.",
            "No causal local-time coefficient or cross-body analogue claim is identified.",
        ],
        "e001_known_analogue_recovery": "NOT YET MEASURED",
        "cross_body_similarity": "NOT YET PROVEN",
        "novel_analogue_discovery": "NOT YET PROVEN",
    }


if __name__ == "__main__":
    output = Path(__file__).parent / "results/e310_themis_year_aliasing.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    result = run()
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result["result"], sort_keys=True))
