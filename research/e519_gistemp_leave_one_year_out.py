"""E519: leave-one-evaluation-year-out sensitivity of E518 frozen forecasts.

Only delete each target year's ERROR from evaluation, never from model training.
Reproduce: python -m research.e519_gistemp_leave_one_year_out
Data provenance and retrospective-only limits: E518.
"""
import csv
from pathlib import Path
from research.e518_gistemp_rolling_mean_baselines import ols_predict

DATA = Path(__file__).with_name("gistemp_zonal_2001_2025_snapshot.csv")
METHODS = ("trend", "persistence", "mean3", "mean5")
COLUMNS = (("global", "global_centi_c"),
           ("tropics", "tropics_24S_24N_centi_c"),
           ("arctic", "arctic_64N_90N_centi_c"))

def errors(years, values):
    assert years == list(range(2001, 2026))
    e = {k: [] for k in METHODS}
    for t in range(10, len(years)):
        train = values[:t]
        predictions = {
            "trend": ols_predict(years[:t], train, years[t]),
            "persistence": train[-1],
            "mean3": sum(train[-3:]) / 3,
            "mean5": sum(train[-5:]) / 5,
        }
        for key in METHODS:
            e[key].append(abs(values[t] - predictions[key]))
    return e

def leave_one_out(e):
    n = len(e["trend"])
    assert n == 15 and all(len(e[k]) == n for k in METHODS)
    winners = {k: 0 for k in METHODS}
    exceptions = []
    for i in range(n):
        ranking = sorted(METHODS, key=lambda k: (sum(e[k]) - e[k][i]) / (n - 1))
        winners[ranking[0]] += 1
        exceptions.append((2011 + i, ranking[0]))
    return winners, exceptions

def main():
    with DATA.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    years = [int(r["year"]) for r in rows]
    for label, col in COLUMNS:
        values = [int(r[col]) / 100 for r in rows]
        e = errors(years, values)
        full = {k: sum(e[k]) / 15 for k in METHODS}
        winners, years_winners = leave_one_out(e)
        print(label, "full_mae", {k: round(v, 6) for k, v in full.items()},
              "leave_one_year_out_winners", winners, "per_year", years_winners)
        assert sum(winners.values()) == 15

if __name__ == "__main__":
    main()
