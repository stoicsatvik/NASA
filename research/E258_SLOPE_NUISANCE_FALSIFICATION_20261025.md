# E258 | Real Earth terrain contrast under synthetic planar-slope nuisance

**Executed:** 2026-10-25. **Exact-head evidence:** [GitHub Actions 40185139599](https://github.com/stoicsatvik/NASA/actions/runs/40185139599), SUCCESS, 78/78 deterministic tests. [Numerical artifact 12595447715](https://github.com/stoicsatvik/NASA/actions/runs/40185139599/artifacts/12595447715) contains the full machine-readable result. No raw DEM rasters committed.

## Question and preregistered test

E247's combined 15-km-lag RMS height contrast had **0/256** two-site ranking reversals at 2×2 under independent registration phases. But the descriptor is sensitive to broad-scale slope. Does adding a *synthetic* planar gradient to either one of the two real Earth elevation windows expose rank fragility without changing plane-detrended relief?

Use exactly the same source-fingerprinted 30-km Western Ghats and Ladakh research windows as E247. Add slopes of 2, 5, 10, 20, 40 or 80 metres/km, each in the four cardinal directions, separately to each site. That is **48 predetermined transformations**. At each 2×2, 4×4, 8×8 and 16×16 resolution, enumerate all **256** independent phase pairs. Compare each perturbed rank to the *original* dense two-site ordering, not a post-hoc new target. The synthetic plane is a controlled nuisance, **not** an estimate of instrument error or actual terrain change.

## Measured result

- **48** real-data-plus-synthetic-nuisance scenarios; dense-resolution ranking reversed in **0/48**.
- At **2×2**, **6/48** slope scenarios yielded at least one phase-pair rank reversal. Total reversed 2×2 phase comparisons: **140/12,288** across all scenarios.
- At **4×4, 8×8 and 16×16**, **0/48** scenarios yielded any phase-pair reversal.
- Maximum change in plane-detrended relief standard deviation after adding the plane: **0.0 m** in the emitted floating-point result.
- All original, unperturbed phase counts remained consistent with E247.

| Site receiving synthetic plane | Direction | Slope (m/km) | 2×2 reversed / 256 |
|---|---|---:|---:|
| Western Ghats lead | North | 40 | 1 |
| Western Ghats lead | East | 80 | 51 |
| Western Ghats lead | West | 80 | 22 |
| Western Ghats lead | North | 80 | 34 |
| Western Ghats lead | South | 80 | 29 |
| Ladakh lead | North | 80 | 3 |

The other 42 predeclared transformations had zero 2×2 reversals. These are deterministic artificial scenarios, not probabilities, confidence intervals or empirical instrument-error frequencies.

## Interpretation and scientific boundary

**SUPPORTED:** E247's common-lag descriptor is not invariant to additive planar slope. On two actual Earth terrain windows, sufficiently strong controlled tilts can create registration-dependent sparse-rank reversals even though plane-detrended relief is unchanged. E247's zero reversals therefore do **not** establish that its descriptor isolates geological roughness.

**LIMITATION:** All observed flips required high synthetic slopes (40–80 m/km), and the original dense ordering survived every tested tilt. This is a bounded counterexample, **not** evidence of widespread instability under ordinary Earth/Moon/Mars acquisition. Neither the slope distribution nor the registration phases were sampled from instrument-error models.

The two Earth locations remain research leads, not independently verified analogue positives/negatives. No actual LOLA/MOLA PSF, spectral/thermal process equivalence, cross-body similarity, known-site recovery, novel analogue discovery or local field validation was measured.

**Claim states:** Earth descriptor slope sensitivity SUPPORTED IN TESTED REAL-DATA/SYNTHETIC-NUISANCE CONDITIONS; E001 known-site recovery NOT YET MEASURED; cross-body similarity NOT YET PROVEN; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; challenge superiority NOT YET PROVEN.

## Next decisive gate

Stop optimizing terrain descriptors against the same two unvalidated Earth leads. Seek independent geological process labels and matched instrument observables, then run blinded leave-one-site-out E001 with random/Euclidean/physically weighted baselines, ablations, false-positive inspection and uncertainty. Re-rank all official 2026 challenge statements when released. No geospatial UI work or competition submission.
