# E582 — pinned CTX QA metrics and MOLA-control audit

Date: 12 November 2026  
Branch: `research/e582-ctx-qa-mola-control-audit-20261112`  
Base: E581 / PR #141. Draft research only; `main` untouched.

## Question

Do the pinned Jezero CTX DTM's official QA metrics and MOLA-control asset support using this item as an absolute-elevation or terrain-slope source?

## Acquisition and reproducibility

- Collection: `mro_ctx_controlled_usgs_dtms`.
- Item: `P18_007925_1987_XN_18N282W__P19_008650_1987_XI_18N282W`.
- Acquisition: 2023-04-18T12:00:00Z.
- Exact-head workflow: https://github.com/stoicsatvik/NASA/actions/runs/43215530283
- Result: deterministic asset-parser tests passed; the live public STAC search, QA text and MOLA-control CSV acquisitions all returned HTTP 200.
- Aggregate artifact: https://github.com/stoicsatvik/NASA/actions/runs/43215530283/artifacts/13943192285
- Artifact SHA-256: `3352effd5daf12b0bd1e1f29aaa5750ba1e885c48c83eeba2bfe9a36a4cf64f9`.
- No raw STAC JSON, QA text, CSV rows, coordinates, signed query values or raw asset bytes were committed.

## QA metrics

The 398-byte `qa_metrics.txt` asset parsed six numeric key/value metrics:

| Metric | Value |
|---|---:|
| Input DEM nodata | -32767 |
| Maximum CTX–MOLA difference | +117.316 m |
| Minimum CTX–MOLA difference | -79.9007 m |
| Mean CTX–MOLA difference | +27.3687 m |
| Median CTX–MOLA difference | +26.7783 m |
| Standard deviation of difference | 10.934 m |

The official USGS documentation says these statistics describe CTX–MOLA differences after ground control. It cautions that maximum/minimum can be dominated by edge outliers and unresolved steep terrain, while mean, median and standard deviation in the tens-to-hundreds-of-metres range can indicate broad quality disagreement; differences of a few metres are more reassuring. It also states that MOLA shots are about 300 m apart along track with often kilometre-scale gaps near the equator, and that the two products have different spatial resolution.

For scale only, the absolute mean and median are roughly 5.4–9.1 times the documented typical 3–5 m CTX vertical-precision range; the standard deviation is roughly 2.2–3.6 times that range. These ratios are not a formal normalized error statistic because the QA residuals and typical stereo-precision statement are not identical measurement distributions.

## MOLA-control CSV

The 344,365-byte public CSV returned HTTP 200 and parsed to:

- 8,750 rows.
- Columns: `latitude`, `longitude`, `radius`.
- Latitude range: 17.7613068 to 19.3372370.
- Longitude range: 77.2196079 to 77.8524971.
- Radius range: 3,391,555.1 to 3,393,171.49; mean 3,392,247.04.

The CSV is explicitly the MOLA points used to control the DTM to ground. The `radius` field's unit/reference is not declared by the parsed header, so no conversion to areoid elevation was made. These are control inputs, not an independent held-out validation set. Raw rows and coordinates were not retained.

## Decision

- **Reject this pinned item for uncorrected absolute-elevation or long-baseline slope use** until the large positive CTX–MOLA offset and its spatial structure are understood.
- Do not interpret the +27 m mean/median as a uniform correction that can simply be subtracted. The aggregate receipt cannot distinguish constant bias from tilt, spatially varying residuals, sparse-control effects or local stereo artefacts.
- Keep the item only as a **candidate for relative/local relief analysis** after inspecting its orthoimage, shaded relief, jitter, nodata and spatial residual structure. Even then, a route-safety claim is not supported.
- Do not treat the MOLA control points as independent ground truth or as a dense 20 m validation grid.
- The E581 20 m/200 m slope sensitivity remains relevant: a longer baseline reduces simple vertical-noise sensitivity, but it does not remove systematic tilt or the observed CTX–MOLA disagreement.

## Next decisive experiment

E583 should screen several additional CTX DTM items in the same Jezero region using their small QA assets before spending compute on raster slopes. Compare mean, median and standard deviation across items; retain item IDs, dates, hashes and bounded summaries only. If no item has acceptable residuals, pivot to a better-controlled product rather than tuning a slope model around this item.

## Claim states

- Public CTX item, COG, QA asset and MOLA-control CSV access: **SUPPORTED**.
- QA/MOLA asset parsing and aggregate receipt: **SUPPORTED FOR THIS ITEM**.
- This item's uncorrected absolute-elevation suitability: **REJECTED PENDING RESIDUAL INVESTIGATION**.
- Relative/local relief usefulness: **NOT YET MEASURED**.
- Actual pixel-level slope, route traversability and route safety: **NOT YET MEASURED / NOT PROVEN**.
- Cross-body similarity, E001 known-site recovery, novel analogue discovery, local validation advantage and challenge-selection superiority: unchanged.

No field data, independent validation, local slope measurement, route-safety conclusion or competition outcome is asserted.

## Sources

- Official USGS CTX DTM processing, QA metrics, MOLA spacing and accuracy caveats: https://stac.astrogeology.usgs.gov/docs/data/mars/ctxdtms/
- Pinned item and aggregate acquisition receipt: workflow #43215530283, artifact #13943192285.
