"""E518: fixed-window rolling mean controls for the pinned NASA GISTEMP snapshot.

Run: python -m research.e518_gistemp_rolling_mean_baselines
Only years strictly before the target year enter any prediction.
Source: research/gistemp_zonal_2001_2025_snapshot.csv (inherited E515 snapshot).
This is a retrospective 15-year exercise, NOT independent prospective validation.
"""
import csv
from pathlib import Path

DATA = Path(__file__).with_name("gistemp_zonal_2001_2025_snapshot.csv")

def ols_predict(years, values, target_year):
    n = len(years)
    xm, ym = sum(years) / n, sum(values) / n
    denominator = sum((x - xm) ** 2 for x in years)
    assert denominator > 0
    slope = sum((x - xm) * (y - ym) for x, y in zip(years, values)) / denominator
    return ym + slope * (target_year - xm)

def evaluate(years, values):
    assert years == list(range(2001, 2026))
    errors = {k: [] for k in ("trend", "persistence", "mean3", "mean5")}
    for t in range(10, len(years)):
        train = values[:t]
        predictions = {
            "trend": ols_predict(years[:t], train, years[t]),
            "persistence": train[-1],
            "mean3": sum(train[-3:]) / 3,
            "mean5": sum(train[-5:]) / 5,
        }
        for key, pred in predictions.items():
            errors[key].append(abs(values[t] - pred))
    assert all(len(v) == 15 for v in errors.values())
    return {k: sum(v) / len(v) for k, v in errors.items()}

def main():
    with DATA.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    years = [int(r["year"]) for r in rows]
    for label, col in (("global", "global_centi_c"), ("tropics", "tropics_24S_24N_centi_c"), ("arctic", "arctic_64N_90N_centi_c")):
        values = [int(r[col]) / 100 for r in rows]
        print(label, {k: round(v, 6) for k, v in evaluate(years, values).items()})

if __name__ == "__main__":
    main()
