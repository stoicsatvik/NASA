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

Deterministic tests check the fixed grid, window margins, and shift set. The first live attempt completed the nine-patch calculations but failed while assembling the receipt because the label URL was not imported. No artifact was emitted; the failure is preserved in Actions run 43024731121. The import is corrected and the exact-head campaign is rerun.


## Exact-head result (11 November 2026)

- Draft PR #110, branch research/e550-ctx-hirise-spatial-residual-grid-20261111.
- Actions run [#43025080316](https://github.com/stoicsatvik/NASA/actions/runs/43025080316) passed **3/3 deterministic spatial-design tests** and completed the live nine-patch campaign.
- CTX source SHA-256 remained identical to E544. HiRISE acquisition used **223 exact Range requests / 353,859 bytes**, below the 1 MB cap. The CTX GeoTIFF was 9,662,387 bytes.
- The fixed 3×3 grid produced **9 patches**, but only **6/9 patches had any common valid HiRISE support**. The three no-support patches were x15_y15, x50_y85, and x85_y85. The six supported patches had 25/25 cells each, giving **150/225 common valid cells (66.7%)**. This directly falsifies the assumption that the metadata bounding-box intersection is equivalent to common valid-pixel support.
- Supported patch zero-shift medians (CTX minus area-weighted HiRISE, metres): x50_y15 **−1.515**, x85_y15 **−3.152**, x15_y50 **−5.014**, x50_y50 **−2.727**, x85_y50 **+2.425**, x15_y85 **−2.427**. Pooled 150-cell median **−2.3149 m**, mean **−2.2881 m**, SD **3.0036 m**, MAE **3.0621 m**, RMSE **3.7764 m**, p95 absolute residual **6.9772 m**, range **−13.9472 to +3.1226 m**.
- The residual is spatially heterogeneous: one supported patch has the opposite sign (+2.425 m), while five are negative. The fixed cardinal ±6 m shift sensitivity does not produce a single correction that resolves all patches; median-of-patch-medians remains negative from roughly −1.79 m to −3.04 m across the five tested translations.
- This is a spatial diagnostic over six valid 100 m patches, not a global mosaic statistic. It is discordant with the published USGS ~+0.4 m median-offset description, but it does not establish a global contradiction, product defect, or which DTM is closer to truth.
- Claim state: CRS parameter equivalence SUPPORTED; metadata-envelope ≠ common-support distinction MEASURED; common support for this sampled grid PARTIAL; spatial residual distribution MEASURED; global vertical offset reproduction NOT ESTABLISHED; local horizontal registration residual NOT YET MEASURED; cross-body similarity NOT YET PROVEN; E001 known-site recovery NOT YET MEASURED.

Next: inspect CTX component-DTM seam/quality provenance and seek an independent HRSC or MOLA reference for the six supported patches. Do not apply a fitted vertical or horizontal correction. Once within-Mars comparability is bounded, move to E001 known-analogue recovery with explicit random/Euclidean/physically weighted baselines.
