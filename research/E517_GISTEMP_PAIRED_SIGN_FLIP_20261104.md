# E517 | Paired error sign-flip sensitivity for E516 (2026-11-04)

## Falsifiable question
E516 showed smaller rolling-origin one-year MAE for linear trend than persistence in Arctic series, but slightly worse global MAE. Does the **paired error difference** look unusually directional under a simple symmetric-sign null?

## Frozen inputs
The 25 annual observations in `gistemp_zonal_2001_2025_snapshot.csv`, already source-audited by E515. Fifteen rolling-origin predictions (2011–2025), training on 2001 through the preceding year. Ordinary least-squares linear extrapolation versus last-year persistence. No test-year leakage.

## Independently executed diagnostic
A separate JavaScript implementation computed all 2^15 = 32,768 paired sign assignments of yearly absolute-error differences and compared the absolute summed difference to the observed value (two-sided). Values below are recomputed from the pinned CSV, not inferred from E516's reported summary.

| Series | Trend MAE °C | Persistence MAE °C | Trend minus persistence °C | Trend worse / better years | Exact sign-flip fraction |
|---|---:|---:|---:|---:|---:|
| Global | 0.105802 | 0.101333 | +0.004469 | 5 / 10 | 0.790222 |
| Tropics | 0.170921 | 0.187333 | -0.016412 | 7 / 8 | 0.692505 |
| Arctic | 0.335119 | 0.416000 | -0.080881 | 8 / 7 | 0.269653 |
| Arctic minus tropics | 0.356144 | 0.440667 | -0.084523 | 6 / 9 | 0.210876 |

## Interpretation and limits
- The apparent Arctic MAE advantage is concentrated in the magnitudes of particular annual errors rather than consistently beating persistence across years (8 worse, 7 better).
- **None of the four absolute paired differences is extreme under this exploratory sign-flip reference.** This does not prove equal skill or reject the climate trend.
- Expanding-window predictions share most training observations, climate series are autocorrelated, and the sign-flip null's exchangeability assumption is **not validated**. These fractions are descriptive sensitivity diagnostics, **not calibrated p-values** or a significance claim. Four series were inspected without multiplicity adjustment.
- This is a negative evidence-strength result. It does not identify the best 2026 Space Apps challenge, demonstrate future predictive skill, or measure E001 analogue recovery.

## Reproduction
`python -m research.e517_gistemp_paired_null` on this isolated branch. The Python reproduction script was committed, but **Python execution and exact-head CI have not been run in this session**. Independent JavaScript enumeration of the pinned CSV produced the values above.

**Claim state:** E517 exploratory exact enumeration SUPPORTED by the independent JavaScript calculation; prospective forecast advantage NOT YET PROVEN; planetary analogue E001 NOT YET MEASURED; cross-body similarity NOT YET PROVEN.

**Next highest-EV experiment:** independent known-site Earth/planetary analogue labels and E001 held-out recovery. Do not extend the same 25-year climate table into another retrospective significance exercise without a new independent source or prospective validation.
