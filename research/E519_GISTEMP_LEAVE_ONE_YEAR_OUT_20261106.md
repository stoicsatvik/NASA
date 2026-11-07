# E519 — Influence of individual retrospective evaluation years (2026-11-06)

## Question and provenance
Does E518's winner for each GISTEMP zone depend on a single 2011–2025 forecast year? Uses the **same** inherited, pinned NASA GISS GISTEMP v4 zonal 2001–2025 snapshot (integer centi-degrees C), the same four frozen forecasting rules, and the same 15 strictly past-only expanding-origin forecasts as E518. No fresh external data or prospective forecasts. Independent JavaScript implementation computed the results below from the exact pinned CSV. Python stdlib reproducer: `python -m research.e519_gistemp_leave_one_year_out`. The Python reproducer was committed but **not executed or CI-verified** in this run.

For each of the 15 evaluation years, remove only that year's absolute forecast error from the 15-year MAE of all four methods; recompute the winner over the remaining 14. Do **not** delete the year from training histories, which would change the forecast experiment and conflate evaluation influence with retraining. Ties would be resolved by method insertion order; none are material here.

## Results
| Zone | E518 full-sample winner | 15 leave-one-evaluation-year-out winner counts | Exception years |
|---|---|---|---|
| Global | Persistence (MAE 0.101333 C) | Persistence 13; trend 2 | Exclude 2016 or 2024 -> trend |
| Tropics | 5-year mean (MAE 0.170400 C) | 5-year mean 9; trend 5; persistence 1 | Exclude 2011, 2014, 2019, 2021, 2022 -> trend; exclude 2025 -> persistence |
| Arctic | Trend (MAE 0.335119 C) | Trend 13; 5-year mean 2 | Exclude 2024 or 2025 -> 5-year mean |

Other methods have zero leave-one-year-out wins. The tropics' original 5-year mean advantage over trend is just 0.000521 C, so its frequent winner flips are unsurprising.

## Interpretation
The categorical winner is **not stable to deleting a single evaluation year in any zone**, especially the tropics (6/15 deletions change the winner). This falsifies a claim of leave-one-year-out ranking invariance for the E518 retrospective window. It does **not** establish a new climate mechanism or prospective forecast superiority. Evaluation years are temporally dependent and the 15 deletions are not independent replications or calibrated confidence intervals. The data snapshot may be revised. Follow-up: contiguous multi-year block influence and genuinely unseen data; prioritize E001 independent planetary analogue recovery over further climate benchmark elaboration unless challenge-ranking evidence justifies it.

Claim: deterministic retrospective sensitivity SUPPORTED by independent JS arithmetic; Python/CI UNVERIFIED; prospective forecasting superiority NOT YET PROVEN; cross-body analogue recovery NOT YET MEASURED.
