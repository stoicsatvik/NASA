# E571 — LOLA 45-degree latitude-band seam control

**Date:** 12 November 2026  
**Branch:** `research/e571-lola-seam-control-20261112`  
**Parent:** E570 bounded real LOLA GDR sample, PR #129  
**Status:** deterministic controls and bounded live acquisition pending

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

## Validation

Pending exact-head deterministic tests and the bounded live PDS acquisition. Failed acquisition is preserved as a negative result. No geoid correction, geological classification, cross-body similarity or analogue recovery is claimed.

## Claim boundary

- Bounded LOLA metadata and sample ingestion: SUPPORTED by E570.
- Same-location seam/control comparison: NOT YET MEASURED.
- Seam artifact attribution: NOT YET PROVEN.
- Cross-body similarity: NOT YET PROVEN.
- Known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
