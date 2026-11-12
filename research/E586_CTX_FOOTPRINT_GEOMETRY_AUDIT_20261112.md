# E586 — actual Jezero CTX footprint geometry audit

Date: 12 November 2026  
Branch: \`research/e586-ctx-footprint-geometry-audit-20261112\`  
Base: E585 / PR #147. Draft research only; \`main\` untouched.

## Question

Do the nine E583 Jezero CTX items have actual product footprints that are AOI-contained and spatially independent, or did the E585 bounding-box diagnostic overstate their overlap and containment?

## Frozen design

- Repeat one anonymous STAC POST to the official USGS Astrogeology API.
- Same collection, Jezero bounding box and limit 9 as E583.
- Require the exact nine E583 item IDs before joining geometries to QA summaries.
- Use actual GeoJSON Polygon/MultiPolygon geometry, not bounding boxes.
- Project with a spherical cylindrical equal-area transform using the Mars 2015 radius (3,396,190 m); report footprint/AOI fractions and pairwise polygon IoU.
- Store only geometry SHA-256, derived areas/fractions, QA aggregates and safe asset metadata summaries.
- Do not store raw item JSON, coordinates, signed URL values, QA text, rasters or credentials.
- No slope, route-safety, independent-accuracy or E001 claim.

## Interpretation boundary

Actual footprint overlap is not proof of shared control lineage or statistical dependence. The QA asset is attached to each product; geometry alone does not prove whether its residual summary is AOI-clipped. The residuals remain post-control CTX–MOLA QA, not held-out validation.

## Validation

Nine deterministic tests cover exact item-set pinning, true polygon overlap versus bbox overlap, partial AOI coverage, polygon holes, multipolygons, invalid geometry, deterministic geometry hashes and signed-query redaction. The bounded live STAC acquisition runs only on the isolated research branch and uploads an aggregate receipt artifact.

## Decision states

Pending live acquisition. Until the exact nine geometries are acquired and validated, no E586 footprint result is claimed. All NASA scientific claim states remain unchanged.
