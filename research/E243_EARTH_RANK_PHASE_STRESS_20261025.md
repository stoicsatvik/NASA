# E243 | Earth terrain rank reversal under independent sampling registration

**Executed:** 2026-10-25. **Claim:** SUPPORTED only for two real, unvalidated Earth terrain leads under a finite deterministic sampling stress test. **Not** an Earth/Moon/Mars analogue-recovery result.

## Question

E242 showed that separately plane-detrended 2×2 relief measurements are strongly sensitive to sample registration. Does this affect the *ordering* of two real sites over a common 30-km physical footprint?

## Data and frozen protocol

Reuse the exact E242 source-fingerprinted public Mapzen Skadi SRTM-derived HGT tiles:

- Western Ghats N18E073 SHA-256 `73523b876c229607f421c529b8c91a5ed7dd9b504ba413064b5ab0fcb193361b`.
- Ladakh N34E077 SHA-256 `9179642ad2f9ccd90266229b9e9d7c49044bda661ec731d0068879dd607f2c7c`.

For each of 2×2, 4×4, 8×8, 16×16, evaluate the same 16 point-sampling registrations (four offsets per axis). Count both 16 synchronized phase comparisons and the exact 16×16=256 independent cross-site combinations. Compare to each metric's full-resolution ordering. Include separately plane-detrended relief SD and raw elevation range as a contrasting, slope-sensitive descriptor. No tuning against these measurements.

## Exact-head numerical result

[Read-only workflow 40155160144](https://github.com/stoicsatvik/NASA/actions/runs/40155160144), head `ff89191814a0a6aef1f508dbb11bb767da5861ef`: **69/69 deterministic tests passed**; both source SHA-256 gates passed. Machine-readable receipt artifact `12584127859` (`e243-real-earth-rank-phase-receipt`).

The dense-resolution higher-ranked site is **Ladakh** for both descriptors.

| Coarse grid | Independent phase reversals, plane-detrended relief SD | Independent phase reversals, raw elevation range |
|---|---:|---:|
| 2×2 | **27 / 256** | 0 / 256 |
| 4×4 | 0 / 256 | 0 / 256 |
| 8×8 | 0 / 256 | 0 / 256 |
| 16×16 | 0 / 256 | 0 / 256 |

The 2×2 rank reversal fraction is **10.546875% of the enumerated artificial phase combinations**, NOT a statistical probability of planetary sensor failure. In this finite two-site comparison, the alternative raw elevation range preserved the order under all 256 combinations, but it also includes broad-scale slope and must not be relabeled as a roughness measure. Four-by-four stability for this pair does not imply stability for other sites or actual sensors.

## Mathematical identifiability gate

For a 2×2 grid with heights `[[a,b],[c,d]]`, least-squares removal of an intercept and x/y plane leaves one residual dimension. Its population residual standard deviation is exactly

`|a - b - c + d| / 4`.

Thus the 2×2 detrended-relief descriptor measures **only one checkerboard interaction mode**. Arbitrarily steep planar terrain can yield zero residual; an apparent roughness rank reversal need not indicate a meaningful geological difference. The identity was checked on 200 seeded random grids and planar controls.

## Boundaries and next decision

This is an **Earth-only finite-scenario falsification**, not an observed frequency, calibrated sensor model, independent site sample, analogue ground truth, or field validation. The 16 phase offsets are analyst-defined and the two derived DEMs do not reproduce LOLA/MOLA sampling footprints or PSFs.

**E001 known-site recovery: NOT YET MEASURED. Cross-body similarity: NOT YET PROVEN. Novel analogue discovery: NOT YET PROVEN. Local validation advantage: NOT YET PROVEN. Planetary challenge superiority: NOT YET PROVEN.**

**Next:** do not use a 2×2 plane-detrended relief SD as a standalone cross-body ranking feature. Test instrument-aware common spatial-frequency descriptors against independent geological positive and negative labels. Re-rank the official challenge statements on/after 2026-10-28; no competition solution or UI work is justified yet.
