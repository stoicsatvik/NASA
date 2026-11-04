# E492 | NASA GISTEMP five-year-block trend null (2 Nov 2026)

## Question
Does the *competing* 2026 Space Apps Earth System Trend Detective direction offer a statistically defensible, reproducible baseline on already accessible NASA annual zonal observations? This is pre-event **data-method feasibility research**, not a competition project, planetary E001, climate attribution or a challenge win-probability estimate.

## Frozen source
- NASA GISS GISTEMP v4 zonal annual anomaly source: https://data.giss.nasa.gov/gistemp/tabledata_v4/ZonAnn.Ts%2BdSST.txt
- Repository 2001–2025 **manually transcribed** CSV, Git blob `0f8109a63a1e3b683a67d83bbb6ef8840ccfad45`, SHA-256 `dc5d81e433b4687143e06b7f35471105aa9f12e9c9e1c6ea5304436ff48b44a2`.
- Values are 0.01 °C anomalies relative to 1951–1980, **not absolute surface temperatures**. No new NASA source download or observational uncertainty ensemble was obtained this run.

## Method
1. Freeze 25 annual values (2001–2025) for global, 24°S–24°N tropics, 64°N–90°N Arctic, and Arctic-minus-tropics.
2. OLS slopes in °C/decade; Newey-West HAC intervals for lags 1, 3, 5; Theil–Sen slopes and intervals.
3. Exhaustively permute **five contiguous 5-year blocks** in all 5! = 120 orders, preserving within-block order. Exact inclusive two-sided conditional p = number of permuted slopes with absolute magnitude >= observed, divided by 120.
4. Delete each consecutive five-year window (21 exclusions), preserving original calendar years when refitting.

## Measured retrospective results

| Series | OLS °C/decade | HAC lag-3 95% interval | Theil–Sen °C/decade | Exact block-order two-sided p | Leave-5-out slope range |
|---|---:|---:|---:|---:|---:|
| Global | +0.25877 | [+0.19457,+0.32297] | +0.25000 | 1/120 = 0.00833 | [+0.22917,+0.31639] |
| Tropics | +0.19392 | [+0.12050,+0.26735] | +0.17958 | 2/120 = 0.01667 | [+0.17361,+0.25940] |
| Arctic | +0.67869 | [+0.52668,+0.83070] | +0.62426 | 2/120 = 0.01667 | [+0.55947,+0.83880] |
| Arctic minus tropics | +0.48477 | [+0.30377,+0.66577] | +0.45586 | **6/120 = 0.05000** | [+0.30008,+0.64098] |

**Finding:** A visually strong and HAC-positive Arctic/tropics contrast becomes *borderline* under this particular block-order null. Thus an unqualified “robust under every temporal null” claim is REJECTED for the frozen series. The conditional null is **not** a physically valid counterfactual climate simulation, so the 0.05 value is not a climate attribution p-value or proof against Arctic amplification. Block exchangeability is unproven and the coarse 120-order space limits resolution.

## Validation
- Local Python 3, NumPy 2.3.5, SciPy 1.17.0, statsmodels 0.14.6: **6/6 focused tests PASS**.
- Independent Python standard-library `fractions.Fraction` calculation, without importing experiment code: exact global slope +0.2587692308, 1/120 extreme; Arctic-minus-tropics +0.4847692308, 6/120 extreme.
- Local CSV Git blob verified identical to repository source blob. Remote experiment/test exact-head execution and native CI are **NOT YET VERIFIED**.
- Deterministic numerical receipt: `research/results/e492_gistemp_block_null_20261102.json`.

## Claims and next decision
- **SUPPORTED locally:** Reproducible real-source-transcription time-series baseline and exact conditional sensitivity calculations.
- **NOT YET PROVEN:** This block-order null is physically exchangeable; Earth Trend challenge superiority; climate causal attribution; source freshness; cross-body similarity.
- **NOT YET MEASURED:** Planetary E001 known-site recovery.
- **Next high-EV move:** Obtain source-native, independently downloaded NASA monthly/site-level data and measurement uncertainties for a genuinely held-out trend test; in parallel prioritize physically registered LOLA/MOLA/Earth terrain elevation pairs for planetary E001. No more trend-methodology scaffolding unless the new data changes the decision.
