# E586 — actual Jezero CTX footprint geometry audit

Date: 12 November 2026  
Branch: \`research/e586-ctx-footprint-geometry-audit-20261112\`  
Base: E585 / PR #147. Draft research only; \`main\` untouched.

## Question

Do the nine E583 Jezero CTX items have actual product footprints that are AOI-contained and spatially independent, or did the E585 bounding-box diagnostic overstate their overlap and containment?

## Live acquisition

- One anonymous USGS Astrogeology STAC POST to \`/api/search\`.
- Collection: \`mro_ctx_controlled_usgs_dtms\`.
- Jezero bbox: [76.69, 17.41, 78.69, 19.41]; limit 9.
- HTTP 200; 90,433 bytes; all nine IDs exactly match the E583 QA receipt.
- Nine valid Polygon geometries; zero invalid; geometry bounds exactly match the published STAC bboxes.
- No credentials, raw item JSON, raw geometry, coordinates, QA text, signed query values or rasters stored.
- Search response SHA-256: \`0298b4ef52fe96ad0595657c364da321d81a56e299d9e1a1fe8d22132aa475c5\`.

## Results

| Item | Actual footprint inside AOI | Bbox fraction | Actual / bbox |
|---|---:|---:|---:|
| N02 | 100.0000% | 100.0000% | 1.0000 |
| N03 | 100.0000% | 100.0000% | 1.0000 |
| N04 | 100.0000% | 100.0000% | 1.0000 |
| N04 | 99.9857% | 99.3842% | 1.0061 |
| N09 | 0.5058% | 3.5634% | 0.1420 |
| N15 | 47.8140% | 48.0276% | 0.9956 |
| P02 | 100.0000% | 100.0000% | 1.0000 |
| P05 | 0.0434% | 12.2790% | 0.0035 |
| P18 | 100.0000% | 100.0000% | 1.0000 |

The >=99%-contained count remains 6/9, but the bbox audit materially overstated P05's true AOI coverage by about 282.8x and N09's by about 7.0x. N15's bbox fraction is close to its actual polygon fraction.

Actual footprint overlap:
- All nine: 22/36 pairs intersect; 10/36 have IoU >=0.1; maximum IoU 0.747534.
- The six >=99%-contained items: 14/15 pairs intersect; 7/15 have IoU >=0.1; maximum IoU 0.747534.
- E585 bbox overlap had 28/36 intersections and 14/36 IoU >=0.1. Bounding boxes therefore overstate pairwise overlap, but actual footprints still overlap substantially.

The six contained products retain a median QA item-mean of +26.17935 m and median QA item-median of +25.2618 m. All nine STAC assets are titled "ASP Generated Quality Assurance Metrics" and typed text/plain.

## Method and limits

Geometry is projected with a spherical cylindrical equal-area approximation using Mars 2015 semi-major radius 3,396,190 m. The source CRS is Mars 2015 ocentric; the custom area projection is explicitly an approximation. It is not a DEM or terrain measurement. The Mars CRS reference records the 3,396,190 m semi-major and 3,376,200 m semi-minor axes: https://voparis-vespa-crs.obspm.fr/web/mars.html .

Actual footprint/AOI overlap does not establish where the attached QA metrics were computed. The QA assets remain product-level post-control CTX–MOLA residual summaries unless documentation proves AOI clipping. Spatial overlap also does not establish shared control lineage or statistical dependence. These are not independent validation errors, route-safety measurements or E001 labels.

## Validation

- [Exact-head Actions run #43225029602](https://github.com/stoicsatvik/NASA/actions/runs/43225029602): 10/10 deterministic tests passed; live STAC acquisition and geometry audit completed.
- Aggregate artifact [#13947177574](https://github.com/stoicsatvik/NASA/actions/runs/43225029602/artifacts/13947177574).
- Durable aggregate receipt: \`research/results/E586_CTX_FOOTPRINT_GEOMETRY_AUDIT_20261112.json\`.
- USGS sources: https://stac.astrogeology.usgs.gov/docs/reference/api/ and https://stac.astrogeology.usgs.gov/docs/tutorials/mosaic_json/ .

## Decision

E585's six-versus-three containment classification survives, but its bbox fractions and pairwise-overlap counts were overconfident. Keep the six contained items only as a spatially qualified descriptive QA cohort; do not call them independent or AOI-clipped.

Next gate: resolve the CTX–MOLA \`geodiff\` input order and initial pc-align control lineage from public processing documentation/metadata, or find an independent control set. All NASA scientific claim states remain unchanged: E001 known-site recovery NOT YET MEASURED; cross-body similarity NOT YET PROVEN; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; challenge-selection superiority NOT YET PROVEN.
