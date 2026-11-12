# E574 — Decompose the E573 HiRISE valid-point support gain

Date: 2026-11-12  
Parent: E573 / PR #132  
Source workflow: [E573 exact-head run #43155697664](https://github.com/stoicsatvik/NASA/actions/runs/43155697664)  
Source artifact: #13916101713; receipt SHA-256 `939e3c3b81917f50065f4a1296e909bcfd95144e20257fc8939035ae0f5450a0`; source head `7f6541e10a823402c2c50bcf6647e425d037ca3a`

## Question

Does the 2025 HiRISE DTM's 95-point valid-support advantage over the 2020 DTM arise from more valid samples inside the same footprint, or mostly from its larger footprint?

## Frozen aggregate result

At zero offset, both products were sampled at the same 346 observed MOLA point centers:

- 2020 valid: 164
- 2025 valid: 259
- Net difference: +95
- Shared footprint: 239 points
- 2025-only valid within shared footprint: 83
- 2020-only valid within shared footprint: 61
- Net shared-footprint validity difference: +22
- 2025 valid where 2020 is outside its footprint: 90
- 2020 valid where 2025 is outside its footprint: 17
- Net footprint-only contribution: +73

The 95-point net gain decomposes exactly into **+22 within the shared footprint** and **+73 from footprint extent**. Therefore 76.84% of the net count advantage comes from the additional 2025 footprint; 23.16% comes from differing valid/nodata masks within the common footprint.

## Translation sensitivity

| Mode | Offsets | Total net difference | Shared-footprint component | Footprint component |
|---|---:|---:|---:|---:|
| Common-mode, up to 10.2 m | 13 | +94 to +95 | +21 to +22 | +73 |
| 2025-only differential, up to 10.2 m | 13 | +95 | +22 | +73 |

The support advantage remains positive across every tested offset. This is a deterministic translation grid, not a probability distribution or confidence region.

## Interpretation

The 2025 DTM offers more valid MOLA-point support in this frozen window, but the headline +95 count should not be read as a +95-point improvement in data quality. Most of the difference is footprint extent. The smaller +22 component is a within-common-footprint validity-mask difference.

This is still only point-support availability. E573 does not provide an independent horizontal control network, registration residuals, terrain-accuracy validation, route safety, or cross-body analogue similarity.

## Claim states

- 2025 vs 2020 point-support difference: **MEASURED FOR THIS FROZEN 346-POINT WINDOW**.
- Support-gain decomposition: **SUPPORTED FOR THIS FROZEN WINDOW AND 13-POINT TRANSLATION GRID**.
- Independent horizontal registration: **NOT MEASURED**.
- Terrain accuracy / route safety: **NOT MEASURED / NOT CLAIMED**.
- Cross-body similarity: **NOT YET PROVEN**.
- Known-site recovery: **NOT YET MEASURED**.
- Novel analogue discovery: **NOT YET PROVEN**.

## Next decisive gate

Find an independent horizontal control or registration source for the pinned Mars area. Do not turn point-support availability into an accuracy or safety claim. Keep the planetary-analog challenge conditional; the current challenge-ranking evidence still places Martian Map and MODIS/VIIRS in a provisional tie, with planetary analog outside the top five under the E541 factor ablations.


## Validation history and provenance hardening — 12 November 2026

The first E574 workflow run [#43156436125](https://github.com/stoicsatvik/NASA/actions/runs/43156436125) failed before executing any tests because the workflow invoked `python -m pytest` in a clean Python 3.11 environment without installing pytest. The tests themselves use the standard-library `unittest` framework. No decomposition script ran and no E574 receipt was produced. This is an environment/runner-command failure, not a failed scientific hypothesis or arithmetic result.

The source summary is now pinned to the latest exact-head E573 run #43155697664 / artifact #13916101713. The receipt JSON SHA-256 is unchanged at `939e3c3b81917f50065f4a1296e909bcfd95144e20257fc8939035ae0f5450a0`; the source head is `7f6541e10a823402c2c50bcf6647e425d037ca3a`. Recalculation from that artifact independently reproduces common-mode components (+21–22 shared, +73 footprint) and differential components (+22 shared, +73 footprint) across all 13 offsets.

The implementation now fails closed on source run/artifact/commit/hash mismatch; validates the 239-point shared-footprint partition, both product valid totals, baseline +22/+73/+95 arithmetic, and every min/max offset decomposition. The workflow now invokes standard-library unittest rather than requiring pytest. Exact-head E574 validation is pending; the result remains a deterministic decomposition of the E573 aggregate, not a new raster acquisition.
