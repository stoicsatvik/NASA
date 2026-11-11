# E550 — nine-patch spatial CTX / HiRISE residual campaign (11 November 2026)

## Question

Is the E549 negative CTX-minus-HiRISE residual a local Jezero patch effect or spatially systematic across the full 2020 TRN product overlap?

## Frozen design

- Nine patch centers at the Cartesian product of 15%, 50%, and 85% of the CTX/HiRISE metadata-overlap envelope.
- Each patch is 5×5 CTX cells (nominally 100 m × 100 m).
- Each 20 m CTX cell is compared with an area-weighted mean of overlapping 1 m HiRISE pixels.
- A cell counts only with at least 99% valid HiRISE area.
- Fixed translation sensitivity: (0,0), (±6,0), (0,±6) metres. No shift is fitted.
- Retain only source hashes, per-cell derived residuals, patch summaries, and coverage; no raw raster/pixel arrays.

## Interpretation boundary

The nine-patch campaign is a spatial diagnostic, not global product validation. The published USGS ~0.4 m median offset is external context, not a target to calibrate against. Any mismatch is preserved rather than corrected away.

## Validation

Deterministic tests check the fixed grid, window margins, and shift set. Exact-head live results are appended after the workflow completes.
