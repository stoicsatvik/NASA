# E584 — interpret the bounded Jezero CTX QA cohort

Date: 12 November 2026  
Branch: `research/e584-ctx-qa-residual-cohort-interpretation-20261112`  
Parent: E583 / PR #145, exact head `556ada42b7ab049eadee8ca2786e2bd3f9b1f23c`. Draft research only; `main` untouched.

## Question

Is the approximately +27 m mean / +27 m median CTX–MOLA QA residual in the pinned E580 product isolated, or does it recur across the bounded Jezero cohort?

## Source and execution receipt

- Official USGS STAC collection: `mro_ctx_controlled_usgs_dtms`.
- Frozen Jezero bbox: [76.69, 17.41, 78.69, 19.41] longitude/latitude.
- E583 workflow: [run #43217785725](https://github.com/stoicsatvik/NASA/actions/runs/43217785725).
- Exact commit: `556ada42b7ab049eadee8ca2786e2bd3f9b1f23c`.
- Search: HTTP 200, 90,433 bytes, nine returned/selected items.
- QA assets: **9/9 HTTP 200**, each 397–399 bytes, six numeric metrics parsed per item.
- No credentials, raw item JSON, raw QA text, rasters, MOLA CSV rows, individual control coordinates or signed URL values were retained.
- Aggregate-only source receipt is preserved in `research/results/E583_CTX_QA_COHORT_SCREEN_20261112.json`; each QA asset SHA-256 is recorded.

## Measured descriptive result

All nine products have positive reported mean and median CTX–MOLA differences.

| Summary | Mean difference (m) | Median difference (m) | SD of difference (m) |
|---|---:|---:|---:|
| Cohort median | 27.3687 | 26.9863 | 13.4709 |
| Minimum | 21.2787 | 21.0239 | 10.9340 |
| Maximum | 40.5091 | 40.0418 | 15.6490 |

The pinned E580 item `P18_007925_1987_XN_18N282W__P19_008650_1987_XI_18N282W` has mean **+27.3687 m**, median **+26.7783 m**, and SD **10.934 m**. Its mean ranks 5th of 9 (ascending); its SD is the lowest of the nine.

### Interpretation

The pinned item's approximately +27 m mean/median is **not an isolated value within this bounded cohort**. Every selected product reports a positive mean/median, with cohort medians near +27 m. The pinned item has comparatively low dispersion but not a uniquely low offset.

This is a product-level QA pattern worth investigating, not evidence of absolute CTX elevation bias. The USGS QA values are post-control CTX–MOLA residuals. They are not independent validation errors. The sign convention remains unresolved without item-specific processing input order. The first nine returned items are a bounded screening cohort, not a random or exhaustive sample; product footprints overlap and may share control lineage. No p-value, confidence interval, independent-sample inference or accuracy estimate is claimed.

## Validation

- E583 exact-head Actions run #43217785725: **success**; deterministic selection tests and bounded live QA acquisition completed.
- E584 deterministic analysis tests are designed to fail closed on partial cohorts, failed assets or credential use. They can be run locally with:
  `python -m pytest experiments/test_e584_ctx_qa_cohort_analysis.py -q`.
- No new Actions workflow was added; no extra runner spend is required for this analysis.

## Claim state

- Bounded public CTX QA acquisition for nine Jezero products: **SUPPORTED**.
- Positive mean/median residual pattern within this selected cohort: **SUPPORTED as a descriptive observation**.
- Absolute CTX vertical accuracy, sign interpretation, independent validation, route safety, and E001 known-site recovery: **NOT YET PROVEN / NOT MEASURED**.
- Cross-body similarity, novel analogue discovery, local validation advantage, and challenge-selection superiority: unchanged **NOT YET PROVEN**.

## Next decisive gate

1. Resolve the item-specific `geodiff` input order and exact control provenance from the processing metadata or source documentation.
2. Inspect the selected item's intersection-error raster and orthoimage only after the QA semantics are resolved; keep MOLA control points out of any held-out validation claim.
3. Require an independent horizontal/vertical control source before using terrain slope or route safety.
4. Keep the official 14-challenge comparison open. E584 does not change the current readiness ranking or justify locking a challenge.

No field data, new pixel measurements, route-safety result, competition submission, merge, deployment or external contact is claimed.
