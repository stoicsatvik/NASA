# E571 — LOLA 45-degree latitude-band seam control

**Date:** 12 November 2026  
**Branch:** `research/e571-lola-seam-control-20261112`  
**Parent:** E570 bounded real LOLA GDR sample, PR #129  
**Status:** exact-head deterministic controls and bounded live acquisition succeeded

## Question

Does the unusually large relief in E570's analyst-selected window centred at 45°S coincide with a measurable local discontinuity at the PDS-documented 45-degree latitude-band boundary?

## Frozen design

Reuse the exact E570 PDS3 product contract, metadata parser, HTTP Range validator, 11×11 window geometry and 1 MB transfer cap. Acquire three windows at the same 90°E longitude:

- seam baseline: 45.0°S, crossing the documented 45-degree boundary;
- north control: 44.5°S, not crossing the boundary;
- south control: 45.5°S, not crossing the boundary.

The adjacent windows overlap the seam window by three of eleven rows. This is explicit in the receipt; the windows are not independent replicates. Reacquire the seam window to check repeatability against E570's reported 1,662.64 m p95–p05 relief (rounded to 0.01 m).

Compare p95–p05 radial-height relief, median absolute deviation, median local slope and p90 local slope. Retain only source hashes, PDS metadata, transfer counts and aggregate descriptors. No raw pixel values or full raster download.

## Discriminating predictions

- A seam-related discontinuity is more plausible if the seam window is an outlier relative to both adjacent controls across multiple descriptors, while the two controls are more similar to each other.
- Ordinary local terrain variation remains plausible if the controls differ substantially or the seam window lies within their range.
- No observed difference at this one longitude does not falsify all seam effects; it only weakens this local explanation.
- Even a strong seam/control contrast does not prove causation because windows overlap and local topography may change over the same distance.

## Exact-head validation and live result

- Code head: `59f8fe849e93a9b5b3948bbf90e3963bc5d60ee2`.
- GitHub Actions run [#43135464449](https://github.com/stoicsatvik/NASA/actions/runs/43135464449) succeeded: **6/6 deterministic tests passed**, bounded live acquisition completed, receipt artifact [#13907615759](https://github.com/stoicsatvik/NASA/actions/runs/43135464449/artifacts/13907615759).
- PDS label HTTP 200, 5,139 bytes. Three exact HTTP 206 ranges transferred 691,332 bytes; total 696,471 / 1,000,000-byte cap. All windows contained 121/121 finite samples, zero missing/non-finite samples. No full raster or raw pixel values were retained.
- Reacquired seam relief was 1,662.636876 m, only 0.003124 m from E570's rounded 1,662.64 m report.
- Seam window: relief 1,662.636876 m; MAD 437.139962 m; median slope 5.137607°; p90 slope 12.917739°.
- North control (44.5°S): 164.632440 m; 31.714439 m; 0.560620°; 0.986113°.
- South control (45.5°S): 757.747948 m; 43.487906 m; 1.864560°; 7.642094°.
- The seam window exceeds both controls on all four descriptors. Relative to the two-control mean, its relief is 3.605×, MAD 11.626×, median slope 4.237× and p90 slope 2.994×.
- However, the north/south controls themselves differ by 593.116 m in relief and 6.656° in p90 slope. Each control overlaps the seam window by 3/11 rows. This is strong local spatial heterogeneity and non-independent sampling, so the result is a **candidate seam confound, not causal attribution**.

## Interpretation and next gate

The single-location result is consistent with a seam-associated anomaly, but ordinary local terrain variation remains a viable explanation. Do not use this window's extreme relief as a clean planetary morphology descriptor without a seam/quality mask or independent corroboration. Do not repeat another single-longitude variant. The next NASA decision gate should prioritize the still-leading alternatives in the 14-challenge screen (Martian Map and MODIS/VIIRS) and only spend more on LOLA seams if a predeclared multi-longitude design can change feature admissibility.

No geoid correction, geological classification, cross-body similarity, known-site recovery or analogue discovery is claimed.

## Claim boundary

- Bounded LOLA metadata and sample ingestion: SUPPORTED by E570.
- Same-location seam/control comparison: NOT YET MEASURED.
- Seam artifact attribution: NOT YET PROVEN.
- Cross-body similarity: NOT YET PROVEN.
- Known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
