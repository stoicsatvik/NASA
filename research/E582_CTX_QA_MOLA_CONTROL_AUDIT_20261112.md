# E582 — pinned CTX QA metrics and MOLA-control asset audit

Date: 12 November 2026  
Branch: \`research/e582-ctx-qa-mola-control-audit-20261112\`  
Base: E581 / PR #141. Draft research only; \`main\` untouched.

## Question

Do the pinned E580/E581 CTX item's QA metrics and MOLA-control CSV expose usable residual statistics and a bounded control-point schema?

## Frozen source and limits

- Collection: \`mro_ctx_controlled_usgs_dtms\`
- Item: \`P18_007925_1987_XN_18N282W__P19_008650_1987_XI_18N282W\`
- One anonymous STAC POST for the exact collection and item.
- QA metrics asset cap: 1 MB.
- MOLA-control CSV cap: 5 MB.
- 30-second timeout; HTTPS host allowlist for the pinned USGS STAC/S3 endpoints.
- No credentials, raw item JSON, raw QA text, CSV rows, individual coordinates or signed query values are persisted.
- Receipt contains asset hashes, safe URL summaries, content metadata, numeric QA key/value summaries, CSV schema, row counts and aggregate numeric summaries.

## Exact-head result

Workflow [#43215530283](https://github.com/stoicsatvik/NASA/actions/runs/43215530283) passed **9/9 deterministic tests**, acquired both public assets with HTTP 200, and uploaded aggregate receipt [#13943192285](https://github.com/stoicsatvik/NASA/actions/runs/43215530283/artifacts/13943192285).

- STAC search: HTTP 200, 10,691 bytes.
- QA metrics: HTTP 200, 398 bytes; SHA-256 \`c577c0a83ccc58375b4a7790b6edd9eeee0d84de41f602c56ba00c424a8bcd5e\`.
- MOLA-control CSV: HTTP 200, 344,365 bytes; SHA-256 \`87c1d7f7c32d2ea6aa6257826c30c9576a6d130faff493ae3751635d0b8f998b\`.
- Neither asset exceeded its byte cap; neither raw asset was stored.

## QA metrics

The bounded parser extracted six numeric metrics:

| Metric | Value |
|---|---:|
| Input NoData | -32767 |
| Maximum CTX–MOLA difference | +117.316 m |
| Minimum CTX–MOLA difference | -79.9007 m |
| Mean CTX–MOLA difference | +27.3687 m |
| Median CTX–MOLA difference | +26.7783 m |
| Standard deviation | 10.934 m |

The QA file explicitly labels the differences in metres. The USGS collection documentation says these are statistics for the final CTX–MOLA differences after ground control. It says mean, median and standard deviation should generally be close to zero; values of many tens to hundreds of metres can indicate disagreement and possible large-scale quality issues. It also warns that maximum and minimum differences are less important because they can be driven by edge outliers or steep local terrain unresolved by MOLA.

**Interpretation:** this item does not show a few-metre CTX–MOLA agreement. Its mean and median differences are both about +27 m, with a 10.934 m standard deviation. This is a meaningful item-level QA warning and warrants further review. It is not, by itself, a proof that the DTM is unusable or an independent estimate of absolute error.

The sign convention is not independently resolved: the item's STAC asset list does not expose a provenance/command asset, so the exact input order used for the difference calculation was not recovered. Preserve the signed values as reported; do not translate the positive sign into “CTX above MOLA” until the item-specific processing command or sign convention is verified.

## MOLA-control CSV

The bounded CSV contains **8,750 rows** and exactly three columns:

- \`latitude\`: min 17.7613068339, mean 18.5450165381, max 19.3372370116.
- \`longitude\`: min 77.2196079357, mean 77.5412554439, max 77.8524971254.
- \`radius\`: min 3,391,555.10 m, mean 3,392,247.0405 m, max 3,393,171.49 m.

The coordinate envelope spans most of the DTM footprint but does not establish uniform spatial coverage. The CSV rows are the MOLA points used to control the DTM, not held-out validation points. The USGS documentation notes approximately 300 m along-track spacing, large shot footprints, and kilometre-scale gaps between tracks near the equator.

The \`radius\` column is not a direct areoid-height column. ASP documentation distinguishes MOLA Radius from MOLA Topography (radius minus areoid). No conversion was applied, and these radius values must not be treated as elevations above the areoid.

## Evidence boundary

- QA metrics provide a post-control CTX–MOLA comparison, not independent horizontal validation.
- The MOLA CSV documents the control-point schema and aggregate coverage envelope, not an independent validation sample.
- The reported mean/median residual and standard deviation warrant item-specific inspection, but do not establish absolute accuracy or route safety.
- The COG/STAC band unit remains unreported. The collection-level ASP/USGS documentation supports a metre-valued areoid interpretation, but the item's exact processing command remains unverified.
- No raw item JSON, QA text, CSV rows, individual coordinates, credentials or signed query values were stored.

## Next discriminating gate

1. Determine the QA difference sign convention from an item-specific processing command. No provenance asset was exposed in this item's STAC asset list.
2. Inspect the DTM, intersection-error raster and co-registered orthoimage for spatially coherent artifacts; keep this distinct from independent validation.
3. Do not use the MOLA control points as held-out validation. A separate independent reference is required for that claim.
4. If slope summaries are computed, label the unit basis as a collection-level processing-documentation inference, report valid-pair counts and preserve the USGS 3–5 m typical vertical-precision and coarser-effective-resolution caveats.

## Claim states

- Public CTX item and COG acquisition: SUPPORTED.
- Raster/STAC shape and transform agreement: SUPPORTED FOR THIS ITEM.
- Five valid pixel windows acquired: SUPPORTED.
- QA metrics and MOLA-control CSV acquisition: SUPPORTED.
- Item QA residuals: MEASURED AS REPORTED; sign convention not independently resolved.
- MOLA control-point schema and aggregate envelope: SUPPORTED; not held-out validation.
- TIFF/STAC vertical-unit field: NOT REPORTED.
- Metre-valued areoid elevation from documented collection processing chain: SUPPORTED AS A COLLECTION-LEVEL INFERENCE; item-specific command not independently verified.
- Slope descriptors and independent horizontal/vertical accuracy: NOT YET MEASURED.
- E001 known-site recovery, cross-body similarity, novel analogue discovery, local validation advantage and challenge-selection superiority: unchanged / NOT YET PROVEN.

No raw raster, raw pixel arrays, raw QA text, raw CSV rows, individual control-point coordinates, field measurements, route-safety conclusions or competition outcomes are asserted.
