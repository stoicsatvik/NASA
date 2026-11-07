"""E516: frozen expanding-window one-year GISTEMP prediction stress test.

Auxiliary falsification of simple trend extrapolation, not climate attribution,
a calibrated significance test, or a complete challenge solution.
No target-year value is used to construct its prediction.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from pathlib import Path

SOURCE_SHA256 = "dc5d81e433b4687143e06b7f35471105aa9f12e9c9e1c6ea5304436ff48b44a2"
COLUMNS = ("global_centi_c", "tropics_24S_24N_centi_c", "arctic_64N_90N_centi_c")
FIRST_FORECAST_YEAR = 2011


def read_source(path: Path) -> tuple[tuple[int, ...], dict[str, tuple[int, ...]]]:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError("source bytes differ from pinned E515 GISTEMP snapshot")
    rows = list(csv.DictReader(raw.decode("utf-8").splitlines()))
    if not rows or set(rows[0]) != {"year", *COLUMNS}:
        raise ValueError("unexpected source schema")
    years = tuple(int(row["year"]) for row in rows)
    if years != tuple(range(2001, 2026)):
        raise ValueError("expected annual observations 2001 through 2025")
    series = {name: tuple(int(row[name]) for row in rows) for name in COLUMNS}
    series["arctic_minus_tropics_centi_c"] = tuple(
        a - t for a, t in zip(series[COLUMNS[2]], series[COLUMNS[1]])
    )
    return years, series


def ols_forecast(years: tuple[int, ...], values: tuple[int, ...], target_year: int) -> float:
    if len(years) != len(values) or len(years) < 2 or target_year <= max(years):
        raise ValueError("OLS requires at least two training years strictly before target")
    xbar, ybar = statistics.fmean(years), statistics.fmean(values)
    denom = sum((x - xbar) ** 2 for x in years)
    if denom == 0:
        raise ValueError("training years are not distinct")
    slope = sum((x - xbar) * (y - ybar) for x, y in zip(years, values)) / denom
    return ybar + slope * (target_year - xbar)


def diagnostics(years: tuple[int, ...], values: tuple[int, ...]) -> dict[str, object]:
    if years != tuple(range(2001, 2026)) or len(values) != 25:
        raise ValueError("E516 freezes 25 annual observations")
    predictions: dict[str, list[float]] = {"linear_trend": [], "last_year": [], "training_mean": []}
    actual: list[int] = []
    for i in range(10, len(years)):
        train_years, train_values = years[:i], values[:i]
        predictions["linear_trend"].append(ols_forecast(train_years, train_values, years[i]))
        predictions["last_year"].append(float(train_values[-1]))
        predictions["training_mean"].append(statistics.fmean(train_values))
        actual.append(values[i])
    metrics = {}
    for name, pred in predictions.items():
        errors = [(p - y) / 100 for p, y in zip(pred, actual)]
        metrics[name] = {
            "mae_c": round(statistics.fmean(abs(e) for e in errors), 6),
            "rmse_c": round(math.sqrt(statistics.fmean(e * e for e in errors)), 6),
        }
    loo_slopes = []
    for i in range(25):
        xs = years[:i] + years[i + 1:]
        ys = values[:i] + values[i + 1:]
        xbar, ybar = statistics.fmean(xs), statistics.fmean(ys)
        b = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / sum((x - xbar) ** 2 for x in xs)
        loo_slopes.append(b / 10)
    sen = statistics.median((values[j] - values[i]) / (years[j] - years[i]) / 10
                            for i in range(25) for j in range(i + 1, 25))
    return {
        "forecast_years": [FIRST_FORECAST_YEAR, 2025],
        "forecast_count": len(actual),
        "metrics": metrics,
        "trend_vs_persistence_mae_delta_c": round(metrics["linear_trend"]["mae_c"] - metrics["last_year"]["mae_c"], 6),
        "leave_one_year_out_ols_slope_range_c_per_decade": [round(min(loo_slopes), 6), round(max(loo_slopes), 6)],
        "theil_sen_slope_c_per_decade": round(sen, 6),
    }


def run(path: Path) -> dict[str, object]:
    years, series = read_source(path)
    return {
        "experiment": "E516",
        "source_sha256": SOURCE_SHA256,
        "method": "Expanding 2001-2010 initial training window; predict 2011-2025 one year ahead without target leakage",
        "claim_boundary": "Retrospective source-pinned predictive stress test only; not climate attribution, calibrated inference, or future forecast",
        "series": {name: diagnostics(years, values) for name, values in series.items()},
    }


if __name__ == "__main__":
    print(json.dumps(run(Path(__file__).with_name("gistemp_zonal_2001_2025_snapshot.csv")), indent=2, sort_keys=True))
