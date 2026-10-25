# E242 | Real Earth 30-km terrain sampling-density falsification

**Executed:** 2026-10-25. **Status:** real-source exploratory measurement, not a planetary analogue model or hackathon submission.

## Question and falsifiable prediction

At approximately 30 km equatorial physical support, E212 found a lunar LOLA 4×4 tile has 16 elevation samples while a Martian MOLA 2×2 tile has four. Can a conventional detrended-relief descriptor be assumed stable when a high-resolution *Earth* DEM is degraded to those sample counts?

**Null expectation to challenge:** the descriptor's ratio to high-resolution Earth terrain is approximately one and insensitive to the coarse sampling phase. The experiment does not assert that actual LOLA/MOLA point-spread functions behave like Earth downsampling.

## Independent real-data sources

Read-only Mapzen Skadi SRTM-derived tiles:
- Western Ghats research lead, N18E073, SHA-256 `73523b876c229607f421c529b8c91a5ed7dd9b504ba413064b5ab0fcb193361b`.
- Ladakh research lead, N34E077, SHA-256 `9179642ad2f9ccd90266229b9e9d7c49044bda661ec731d0068879dd607f2c7c`.

Both sites are **unvalidated research leads**, not positive or negative planetary analogue labels. Delivered patches are fully finite (971×1025 and 971×1174 pixels). Both use the same nominal 30-km square support, with local spherical latitude geometry; Skadi is a derived DEM with no pixel-level source completeness claim.

Reproducible script: `research/e242_earth_sampling_aliasing.py`. Deterministic tests: `tests/test_e242_earth_sampling_aliasing.py`. Complete numerical receipt: `research/results/e242_real_earth_sampling_aliasing_20261025.json`.

## Measured result

Relief standard deviation in metres **after separately fitting a plane to each sample grid**:

| Site | Full-resolution relief SD | Idealized 2×2 cell means | 2×2 point-phase min–max (16 phases) | Idealized 4×4 cell means | 4×4 point-phase min–max |
|---|---:|---:|---:|---:|---:|
| Western Ghats | 144.09 | **7.59 (5.3%)** | 0.50–143.00 | **52.16 (36.2%)** | 82.19–187.72 |
| Ladakh | 436.64 | **113.38 (26.0%)** | 14.25–673.75 | **303.31 (69.5%)** | 242.12–535.36 |

Numbers in parentheses are ratios to the same site's full-resolution detrended relief SD. Point-phase samples can *overestimate* as well as underestimate relief, depending on registration. All 2×2 and 4×4 values use exactly the same 30-km nominal physical footprint as their high-resolution reference.

**Decisive limitation:** a 2×2 grid has four values and fitting an intercept plus two planar coefficients leaves only **one residual degree of freedom**. Some of the loss is a mathematical consequence of the estimator, not solely an instrument-resolution effect. It is therefore indefensible to use raw 2×2 detrended relief as if it were a robust counterpart to a dense Earth DEM descriptor.

## Validation and failure preservation

The first workflow attempt [40151021226](https://github.com/stoicsatvik/NASA/actions/runs/40151021226) failed because E214's shared `square_bounds` helper intentionally rejects widths over 20 km. E242 now uses an independently validated 30-km bounds helper; it does not loosen E214's safety/geometry gate. Corrected [real-data workflow 40151130273](https://github.com/stoicsatvik/NASA/actions/runs/40151130273) **SUCCESS**, with synthetic plane, vertical-offset, checkerboard aliasing, sampling-phase and invalid-data controls. Numerical receipt was captured from the successful workflow output; raw DEMs were not committed.

## Inference boundaries and next experiment

**SUPPORTED:** For these two delivered real Earth patches, the selected planar-detrended relief statistic is strongly sensitive to coarse sample count, bin averaging and sample registration. The specific 2×2 estimator is poorly identified.

**NOT YET PROVEN:** That actual lunar/Martian sensors have these biases; that Earth, Moon and Mars roughness can be compared from these products; or that either research lead is a valid analogue.

**E001 known-site recovery: NOT YET MEASURED. Cross-body similarity: NOT YET PROVEN. Novel discovery: NOT YET PROVEN. Local validation advantage: NOT YET PROVEN. Challenge superiority: NOT YET PROVEN.**

**Next highest-value decision:** before using 2×2 MOLA versus 4×4 LOLA versus dense Earth roughness as a matching feature, choose an instrument-aware common spatial-frequency band or a physically comparable robust descriptor, and test it against an independent known analogue with positive and negative geological labels. Re-rank all 14 official challenges when full statements are available on October 28. No UI work is justified by this result.
