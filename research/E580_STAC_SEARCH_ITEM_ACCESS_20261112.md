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


## Exact-head result — 12 November 2026

- Initial run [#43212633786](https://github.com/stoicsatvik/NASA/actions/runs/43212633786) exposed one test-contract defect: the range-summary test expected the redaction flag to be absent, while the receipt intentionally stores `query_values_stored: false`. The live probe was skipped by the failed test gate. The assertion was corrected without changing acquisition code.
- Corrected exact-head run [#43212727544](https://github.com/stoicsatvik/NASA/actions/runs/43212727544) passed **9/9 repository tests**, completed the live probe, and uploaded receipt artifact [#13942396569](https://github.com/stoicsatvik/NASA/actions/runs/43212727544/artifacts/13942396569). Artifact SHA-256: `d642cd36ed8ad8f09a098b0b5ca1a7499cac5c9e67102d1fcf0ce6a9815f91c2`.
- Search returned one item: `P18_007925_1987_XN_18N282W__P19_008650_1987_XI_18N282W`, acquisition datetime `2023-04-18T12:00:00Z`, polygon footprint, bbox [77.2128114, 17.7577892, 77.9059771, 19.3423089].
- Item metadata: shape [4622, 2013], transform [4577133.445008798, 20.162955124498982, 0, 1146178.5021103406, 0, -20.162955124498982], WKT2 present, EPSG field absent. Assets: dtm, image, intersection_error, mola_csv, orthoimage, qa_metrics, thumbnail.
- The public DTM asset returned HTTP **206** for bytes 0–4095 of 18,114,156 bytes. First-range SHA-256: `24c6e28a0934ffeac284d16e197cc431c210247bfe1f2fde47d38942c33bb6f4`.
- This is real item metadata and verified byte-range access. It is **not** a pixel/elevation sample. No raster was downloaded, no pixel values were read, and no slope was calculated.

Claim updates:
- Item-level STAC acquisition for this pinned Jezero query: **SUPPORTED**.
- Public DTM COG byte-range access: **SUPPORTED**.
- Actual raster/pixel sample and units/nodata inspection: **NOT YET MEASURED**.
- E001 known-site recovery, cross-body similarity, novel analogue discovery and challenge-selection superiority remain unchanged.

Next decisive gate: inspect the pinned COG's band units, nodata, CRS, affine transform, data type, QA and a small deterministic set of valid pixel windows. Do not infer vertical units from horizontal posting distance or collection-level metadata.
