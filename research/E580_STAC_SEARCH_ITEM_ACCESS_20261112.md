# E580 — STAC search-path item acquisition gate

Date: 12 November 2026  
Branch: `research/e580-stac-search-post-20261112`  
Base: E579 / PR #139. Draft research only; `main` untouched.

## Question

Can the official USGS Astrogeology STAC search endpoint return one actual CTX DTM item for a pinned Jezero area, and can its public DTM asset serve a bounded byte range?

This is the next data-readiness gate for Martian Map. It is not a terrain-quality, registration, route-safety, or analogue-recovery experiment.

## Source and frozen query

- STAC API: https://stac.astrogeology.usgs.gov/api/
- Collection: `mro_ctx_controlled_usgs_dtms`
- Search endpoint: `/search`
- Collection metadata endpoint: https://stac.astrogeology.usgs.gov/api/collections/mro_ctx_controlled_usgs_dtms
- Jezero bounding box: `[76.69, 17.41, 78.69, 19.41]` (longitude/latitude order)
- Limit: one item
- Method: one anonymous HTTPS POST with a JSON STAC search body.
- If a public `dtm` asset is returned, issue one anonymous HTTPS GET with `Range: bytes=0-4095`.

The official USGS tutorials document this collection ID, the STAC search pattern, Jezero example bounds and DTM asset access:
- https://stac.astrogeology.usgs.gov/docs/tutorials/mosaic_json/
- https://stac.astrogeology.usgs.gov/docs/tutorials/qgis_3d/
- https://stac.astrogeology.usgs.gov/docs/reference/api/

The mosaic tutorial reports 80 Jezero-bbox matches in its documented example. That is historical tutorial output, not a current availability assertion.

## Safety and data handling

- No Earthdata account, API key, cookies, credentials or paid service.
- HTTPS only; redirects and DTM asset hosts are pinned to the public USGS STAC / USGS Astrogeology S3 hosts.
- Search response cap: 1 MB; DTM range cap: 4 KiB; timeout: 20 seconds.
- No full raster is downloaded.
- No raw STAC item JSON, asset query values, raw raster bytes or pixel values are persisted.
- Receipt stores item identity, footprint/bbox, projection metadata, asset names, redacted URL summary, range status and a hash of the bounded response bytes.

## Local contract checks

Eight deterministic local contract checks passed for the frozen payload, STAC FeatureCollection parsing, empty-result handling, URL redaction, public-host allowlisting and receipt semantics. The exact repository test module is also committed and will run in the branch workflow before the live request.

## Decision boundary

Possible outcomes are deliberately separated:
- HTTP/search transport failure: acquisition failure, not a scientific null.
- Empty FeatureCollection: no items matched this exact query; not evidence that no usable Mars data exist.
- Item metadata acquired without a public DTM asset: item discovery only.
- Item plus verified 206 byte-range response: metadata and bounded asset access supported.
- No pixel or elevation sample is claimed by E580, even if the byte-range gate passes.

The collection-level CRS, temporal range, GSD and MOLA-control metadata remain as recorded in E579. Item-level CRS/shape/transform and the DTM byte-range result must be read from this experiment's receipt rather than inferred from collection metadata.

## Next gate

If item and range access pass, acquire a bounded COG header / tile sample with a geospatial reader and record:
- actual item ID, footprint and acquisition provenance;
- item-level CRS/WKT, affine transform, shape, units and nodata;
- COG block/overview structure and QA asset availability;
- a reproducible elevation/slope sample with its pixel support and uncertainty.

Do not claim route safety, cross-body similarity, E001 recovery, or challenge superiority from this access gate.

## Claim states

- Repo operating system: SUPPORTED.
- Martian Map public collection metadata access: SUPPORTED.
- Item-level acquisition: NOT YET MEASURED pending exact-head workflow.
- DTM byte-range access: NOT YET MEASURED pending exact-head workflow.
- Actual raster/pixel sampling: NOT YET MEASURED.
- Cross-body similarity: NOT YET PROVEN.
- Known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Local validation advantage: NOT YET PROVEN.
- Challenge-selection superiority: NOT YET PROVEN.

No field data, terrain measurements, route-safety claim, challenge lock or competition submission is asserted.
