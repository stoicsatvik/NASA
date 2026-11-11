"""Retrospective NASA GISTEMP v4 zonal trend check, NOT planetary analogue E001.
Run: python research/gistemp_zonal_feasibility.py
Requires numpy, scipy, statsmodels; no network, credentials or field data.
Source: https://data.giss.nasa.gov/gistemp/tabledata_v4/ZonAnn.Ts%2BdSST.txt
Snapshot manually transcribed 2026-10-10; NASA may revise historic values.
"""
import csv
import json
from pathlib import Path
import numpy as np
from scipy.stats import theilslopes
import statsmodels.api as sm

DATA = Path(__file__).with_name("gistemp_zonal_2001_2025_snapshot.csv")

def slope(y, year):
    x = year - year.mean()
    fit = sm.OLS(y, sm.add_constant(x)).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    beta, se = 10 * fit.params[1], 10 * fit.bse[1]
    ts = theilslopes(y, year, alpha=0.95)
    return {
        "n_years": len(y),
        "ols_c_per_decade": round(float(beta), 6),
        "hac95_c_per_decade": [round(float(beta - 1.96 * se), 6), round(float(beta + 1.96 * se), 6)],
        "theil_sen_c_per_decade": round(float(10 * ts.slope), 6),
    }

def run():
    with DATA.open(newline="") as file:
        rows = list(csv.DictReader(file))
    years = np.array([int(row["year"]) for row in rows], dtype=float)
    assert len(years) == 25 and np.array_equal(years, np.arange(2001, 2026))
    fields = {
        "global": "global_centi_c",
        "tropics": "tropics_24S_24N_centi_c",
        "arctic": "arctic_64N_90N_centi_c",
    }
    series = {key: np.array([int(row[field]) for row in rows], dtype=float) / 100 for key, field in fields.items()}
    result = {key: slope(values, years) for key, values in series.items()}
    difference = series["arctic"] - series["tropics"]
    result["arctic_minus_tropics"] = slope(difference, years)
    result["arctic_minus_tropics_2011_2025"] = slope(difference[10:], years[10:])
    excluded = []
    for start in range(21):
        keep = np.ones(25, dtype=bool)
        keep[start:start + 5] = False
        excluded.append(slope(difference[keep], years[keep])["ols_c_per_decade"])
    result["leave_5_consecutive_years_out_range"] = [min(excluded), max(excluded)]
    assert 0.25 < result["global"]["ols_c_per_decade"] < 0.27
    assert result["arctic_minus_tropics"]["hac95_c_per_decade"][0] > 0
    assert result["arctic_minus_tropics_2011_2025"]["hac95_c_per_decade"][0] < 0
    assert min(excluded) > 0
    return result

if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
