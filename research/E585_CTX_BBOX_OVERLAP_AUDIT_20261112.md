# E585 — Jezero CTX cohort bounding-box overlap audit

Date: 12 November 2026  
Branch: \`research/e585-ctx-bbox-overlap-audit-20261112\`  
Parent: E584 / PR #146. Draft research only; \`main\` untouched.

## Question

Does the E583 STAC bbox search identify nine products whose QA summaries are spatially local to the Jezero area of interest (AOI), and are those products spatially independent?

## Frozen inputs and method

- Input: committed E583 aggregate receipt, SHA-256 recorded in Git history.
- AOI: [76.69, 17.41, 78.69, 19.41] WGS84 longitude/latitude.
- No new network requests, raster reads, raw item JSON, QA text, or MOLA rows.
- Compute the intersection of each STAC item bounding box with the AOI.
- Compute rectangle areas on a sphere (Earth radius 6,371,008.8 m) and report intersection-area fractions.
- Use 99% item-bbox containment as a conservative descriptive screen, not a scientific accuracy threshold.
- Compute pairwise bounding-box intersection and IoU. These are bounding-box diagnostics, not actual polygon/raster-footprint overlap.

## Measured result

Six of nine item bounding boxes are at least 99% contained within the AOI. Three are materially partial:

| Item prefix | Item bbox area inside AOI | AOI bbox covered |
|---|---:|---:|
| N02_063 | 100.00% | 11.56% |
| N03_063 | 100.00% | 11.07% |
| N04_063 | 100.00% | 10.42% |
| N04_064 | 99.38% | 11.40% |
| N09_065 | 3.56% | 0.40% |
| N15_068 | 48.03% | 5.51% |
| P02_001 | 100.00% | 11.21% |
| P05_002 | 12.28% | 17.90% |
| P18_007 | 100.00% | 27.44% |

The E584 nine-item descriptive result is therefore not a uniformly AOI-local cohort. A STAC bbox search admits intersecting items; it does not guarantee that an item's full bbox, or the spatial support of its product-level QA summary, is restricted to the AOI.

### Strictly bbox-contained six-item subset

The positive mean/median pattern persists among the six items whose bounding boxes are at least 99% contained:

| Metric | Median across six items | Range |
|---|---:|---:|
| Item mean difference | +26.17935 m | +21.2787 to +38.1975 m |
| Item median difference | +25.26180 m | +21.0239 to +37.2683 m |
| Item SD | 13.18815 m | 10.9340 to 15.0610 m |

This is still a descriptive summary of post-control QA values, not a local accuracy estimate or independent validation.

### Bounding-box dependence diagnostic

- All nine items: 28/36 pairs have intersecting bounding boxes; 14/36 have bbox IoU at least 0.1; maximum bbox IoU is 0.782143 (N03_063 and N04_063).
- Six-item contained subset: 15/15 pairs have intersecting bounding boxes; 12/15 have bbox IoU at least 0.1.

This makes independence especially implausible as a default assumption. Bounding-box overlap does not prove actual raster overlap, but it is enough to reject treating the six or nine products as independent spatial replicates without further geometry-level analysis.

## Interpretation and claim boundary

1. E583's acquisition is valid as a bounded STAC search and nine successful QA-asset fetches.
2. E584's all-nine positive pattern must be described as applying to the first nine returned bbox-intersecting products, not as a spatially homogeneous Jezero residual field.
3. The six-item ≥99%-contained subset retains positive mean and median QA differences, but product footprints overlap strongly at the bbox level and may share control lineage.
4. Actual item geometry, raster footprint overlap, QA metric spatial support, and item-specific \`geodiff\` input order remain unresolved.
5. No absolute accuracy, independent validation, route safety, E001 recovery, cross-body similarity, or challenge-superiority claim is made.

## Validation

- Exact-head Actions run [#43222673590](https://github.com/stoicsatvik/NASA/actions/runs/43222673590) passed all 7 deterministic offline tests and recomputed the committed E585 result with a structural match to the E583 receipt.
- The initial recomputation mismatch exposed a P05 item-ID transcription error in the expected receipt; the ID was corrected against the source E583 receipt. Earlier failed runs remain preserved.
- No live source request or external-data workflow is used.

## Next decisive gate

1. Retrieve the nine STAC item geometries and compute polygon intersections with the AOI; do not substitute bbox IoU for actual footprint overlap.
2. Establish whether the QA metrics asset is whole-product or AOI-clipped. If whole-product, use the intersection-error raster and appropriately located controls for a local analysis.
3. Keep initial pc-align MOLA points separate from held-out validation; use an independent reference before promoting any accuracy claim.
4. Group overlapping products or shared control lineage before any uncertainty calculation.

No merge, production deployment, raster processing, field-data claim, or competition-readiness claim is made.
