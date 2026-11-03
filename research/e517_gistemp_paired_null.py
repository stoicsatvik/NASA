"""E517: exploratory exact paired sign-flip diagnostic of E516 rolling forecasts.

Run: python -m research.e517_gistemp_paired_null
Uses only the pinned E516 CSV. No forecasts are refit with test-year data.
IMPORTANT: sign-flip exchangeability is not established for overlapping
expanding-window time-series forecasts. P values are descriptive sensitivity
statistics, NOT calibrated inference or prospective forecasting evidence.
"""
from __future__ import annotations

import csv
from pathlib import Path
from itertools import product

DATA = Path(__file__).with_name("gistemp_zonal_2001_2025_snapshot.csv")


def ols(xs, ys):
    xm = sum(xs) / len(xs)
    ym = sum(ys) / len(ys)
    den = sum((x - xm) ** 2 for x in xs)
    assert den > 0
    slope = sum((x - xm) * (y - ym) for x, y in zip(xs, ys)) / den
    return ym - slope * xm, slope


def evaluate(years, values):
    assert len(years) == len(values) == 25
    assert years == list(range(2001, 2026))
    paired = []
    for t in range(10, len(values)):
        a, b = ols(years[:t], values[:t])
        trend_error = abs(values[t] - (a + b * years[t]))
        persistence_error = abs(values[t] - values[t - 1])
        paired.append((trend_error, persistence_error))
    delta = [a - b for a, b in paired]
    observed = abs(sum(delta))
    count = sum(
        abs(sum(s * v for s, v in zip(signs, delta))) >= observed - 1e-12
        for signs in product((-1, 1), repeat=len(delta))
    )
    return {
        "n": len(delta),
        "trend_mae": sum(a for a, _ in paired) / len(paired),
        "persistence_mae": sum(b for _, b in paired) / len(paired),
        "trend_minus_persistence_mae": sum(delta) / len(delta),
        "trend_worse_years": sum(v > 0 for v in delta),
        "trend_better_years": sum(v < 0 for v in delta),
        "exact_sign_flip_fraction": count / (2 ** len(delta)),
    }


def main():
    with DATA.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    years = [int(r["year"]) for r in rows]
    g = [int(r["global_centi_c"]) / 100 for r in rows]
    t = [int(r["tropics_24S_24N_centi_c"]) / 100 for r in rows]
    a = [int(r["arctic_64N_90N_centi_c"]) / 100 for r in rows]
    for name, series in (
        ("global", g), ("tropics", t), ("arctic", a),
        ("arctic_minus_tropics", [x - y for x, y in zip(a, t)]),
    ):
        print(name, evaluate(years, series))


if __name__ == "__main__":
    main()
