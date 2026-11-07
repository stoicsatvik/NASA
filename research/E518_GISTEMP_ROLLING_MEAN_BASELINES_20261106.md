# E518 — NASA GISTEMP rolling-mean baseline comparison (2026-11-06)

## Question
Do simple trailing-window climatology forecasts change the apparent ranking of the E516/E517 expanding-window linear-trend forecast versus last-year persistence?

## Provenance and frozen protocol
Input: inherited `research/gistemp_zonal_2001_2025_snapshot.csv`, a 25-row 2001–2025 NASA GISS GISTEMP v4 zonal snapshot, whose source-cell reconciliation was recorded in E515. No new download or live-source verification occurred in E518. Units: temperature anomaly in degrees Celsius (CSV integer centi-degrees divided by 100). Three zonal series: global, tropics 24°S–24°N, Arctic 64°N–90°N.

Test years: 2011–2025 inclusive (15 rolling one-step forecasts per zone). Every predictor uses only earlier years: expanding OLS trend, previous-year persistence, trailing 3-year mean, trailing 5-year mean. Fixed rules; no tuning against held-out years. Absolute error is averaged over 15 test years. Deterministic stdlib reproduction: `python -m research.e518_gistemp_rolling_mean_baselines`.

## Results (MAE in °C)
| Zone | Expanding OLS | Persistence | Trailing 3-year mean | Trailing 5-year mean |
|---|---:|---:|---:|---:|
| Global | 0.105802 | **0.101333** | 0.110000 | 0.120000 |
| Tropics | 0.170921 | 0.187333 | 0.190222 | **0.170400** |
| Arctic | **0.335119** | 0.416000 | 0.384000 | 0.353600 |

Values independently calculated in a separate JavaScript implementation from the exact pinned CSV before committing the Python reproducer. The Python file was committed, but a Python execution or exact-head CI success is **not claimed** for this run.

## Interpretation and falsification
The claim that one universal forecasting rule dominates across all three zones is **REJECTED on this retrospective fixture**: persistence wins global, trailing 5-year mean narrowly wins tropics, and expanding OLS wins Arctic. In the tropics the 5-year mean's 0.000521 °C advantage over OLS is extremely small and not evidence of meaningful superiority.

This is not a calibrated significance test, not an independent prospective prediction campaign, and not a complete solution to the Earth System Trend Detective challenge. Temporal dependence, shared observation revisions, and the small test window limit inference. Do not turn this into a claim of a new climate trend or a NASA challenge-selection victory.

**Claim states:** retrospective baseline comparison SUPPORTED at the deterministic arithmetic level, pending exact-head CI; prospective generalization NOT YET PROVEN; planetary cross-body similarity NOT YET PROVEN; independently labeled E001 analogue recovery NOT YET MEASURED.

## Next discriminating test
Freeze a later genuinely unseen GISTEMP update or an independently sourced official time-series snapshot, assess year-block sensitivity and the stability of zone-specific baseline rankings, and compare the full official challenge acceptance requirements. Do not spend effort on geospatial UI until the planetary analogue evidence gate is met.
