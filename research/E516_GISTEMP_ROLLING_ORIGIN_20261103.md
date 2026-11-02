# E516 | GISTEMP expanding-window prediction falsification (2026-11-03)

**Question:** Does the E515 retrospective positive trend automatically make a linear-trend model the best simple one-year-ahead predictor? **No.** This is a different predictive test, not a challenge-wide ranking, calibrated climate significance test, or E001 known-analogue recovery.

## Frozen source and protocol

- Reuses E515 NASA GISS GISTEMP annual zonal 2001–2025 CSV with SHA-256 dc5d81e433b4687143e06b7f35471105aa9f12e9c9e1c6ea5304436ff48b44a2. The E515 audit reconciled 75/75 selected source values with the official NASA GISS table on 2026-11-03. Source: https://data.giss.nasa.gov/gistemp/tabledata_v4/ZonAnn.Ts%2BdSST.txt
- Initial training years 2001–2010. For each target year 2011–2025, fit only earlier years and predict that year; 15 expanding-window, one-year-ahead retrospective predictions per series.
- Frozen predictors: ordinary least-squares linear extrapolation; prior-year persistence; training-mean baseline. All scores in degrees Celsius anomaly MAE/RMSE.
- Also compute full-window Theil–Sen trend and 25 leave-one-year-out OLS slopes as descriptive sensitivity diagnostics. These use full data and are not forecasts.
- No hyperparameter selection or test-year value enters a prediction. Predictions across years are dependent; this sample is too small for claims of robust generalizable forecast superiority.

## Executed local numerical result

| Annual series | Trend MAE °C | Persistence MAE °C | Training mean MAE °C | Trend minus persistence MAE |
|---|---:|---:|---:|---:|
| Global | 0.105802 | **0.101333** | 0.228963 | **+0.004469** |
| Tropics | **0.170921** | 0.187333 | 0.211142 | -0.016412 |
| Arctic | **0.335119** | 0.416000 | 0.626415 | -0.080881 |
| Arctic minus tropics | **0.356144** | 0.440667 | 0.472290 | -0.084523 |

Global linear trend extrapolation loses narrowly to naive last-year persistence on the 15 frozen one-year predictions, despite the E515 full-window positive global trend. For Arctic and the Arctic-minus-tropics contrast, linear extrapolation improves MAE against both simple baselines in this specific window. Neither outcome is a climate-science contradiction or a validated forecasting advantage.

| Series | Theil–Sen slope °C/decade | Leave-one-year-out OLS slope range °C/decade |
|---|---:|---:|
| Global | +0.250000 | +0.239350 to +0.270311 |
| Tropics | +0.179583 | +0.165512 to +0.217069 |
| Arctic | +0.624265 | +0.603362 to +0.716568 |
| Arctic minus tropics | +0.455861 | +0.406437 to +0.517589 |

All 100 leave-one-year-out slopes are positive, so no single year reverses the descriptive trend direction. This does not establish attribution, independence, or calibrated statistical significance.

## Validation and limitations

Six focused deterministic Python controls passed locally, including pinned-source tamper rejection, no target-year leakage, exact-linear and constant controls, and invalid-window rejection. Code and tests are on this isolated stacked research branch; exact-head GitHub Actions is tracked separately.

Reproduce:

    python -m unittest discover -s research -p 'test_e516_gistemp_forward_validation.py' -v
    python -m research.e516_gistemp_forward_validation

**Claim state:** E516 frozen retrospective baseline comparison SUPPORTED LOCALLY; Earth Trend challenge superiority and future predictive skill NOT YET PROVEN. E001 known-analogue recovery NOT YET MEASURED; cross-body similarity, novel analogue discovery and local field-validation advantage NOT YET PROVEN.

**Highest-EV next:** Stop expanding retrospective trend tests without new independent validation. Acquire independent known analogue labels and run E001, or compare a real regional Earth Trend/operational Martian Map data acceptance gate against the planetary-analogue track. No competition submission or UI polish.
