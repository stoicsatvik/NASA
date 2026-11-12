# E601 — controlled CTX STAC item-access and sample-ingestion probe

Date: 13 November 2026  
Branch: `research/e601-ctx-stac-item-access-20261113`  
Base: E600 / PR #166. Draft research only; `main` untouched.

## Question

Can the official USGS controlled MRO CTX DTM collection provide a real, provenance-preserving Mars terrain sample for the higher-readiness Martian Map challenge, and can the current automation runtime retrieve one item and its QA assets?

## Official collection metadata — successful

Live collection metadata endpoint:
https://stac.astrogeology.usgs.gov/api/collections/mro_ctx_controlled_usgs_dtms

Observed on 13 November 2026:
- STAC collection: `mro_ctx_controlled_usgs_dtms`.
- Target: Mars; instrument: MRO Context Camera (CTX).
- NASA is listed as producer; USGS Astrogeology as processor/host.
- License: CC0-1.0.
- Temporal extent: 2023-04-18 through 2025-07-04.
- Projection: Mars 2015 ocentric equirectangular WKT2, central longitude 0.
- Collection GSD summary: 20.0002065–35.9625866 m.
- The collection description says the DTMs are generated with Ames Stereo Pipeline and controlled to MOLA using `pc_align`.
- The collection explicitly warns that some products are jittery and/or have large nodata regions and may not improve on lower-resolution data.

This is a successful collection-metadata retrieval, not item or raster ingestion.

## Independent official item-query documentation

USGS Astrogeology's Mosaic.json tutorial:
https://stac.astrogeology.usgs.gov/docs/tutorials/mosaic_json/

The tutorial identifies Jezero at 77.69° E, 18.41° N and gives the example bounding box:
`[76.69, 17.41, 78.69, 19.41]`.

The tutorial's historical example reports 80 matching CTX DTM items for that bbox and demonstrates limiting the result to 10. **The 80 count is a published tutorial result, not a live count measured in this run.**

The example item asset keys include:
`dtm`, `image`, `intersection_error`, `mola_csv`, `orthoimage`, `qa_metrics`, and `thumbnail`.

The tutorial exposes example hillshade and orthoimage COG URLs for Jezero. It does not expose the exact DTM COG URL in the reviewed page text. No DTM URL is inferred by replacing filename suffixes.

The official CTX DTM documentation states that products have 20 m post spacing, are aligned to MOLA individual shot tracks, and contain holes/ragged edges where stereo processing did not produce a good topographic solution. Post spacing is not effective resolution.

## Retrieval attempts and preserved failures

1. Collection metadata GET through the public USGS STAC host: **SUCCESS**.
2. Exact `items` href returned by the collection metadata (AWS API Gateway): **INACCESSIBLE through the current web retrieval path**.
3. Equivalent public-host `/api/collections/.../items?limit=1` and `/api/search` GET probes: **INACCESSIBLE through the current web retrieval path**.
4. Exact S3 hillshade COG URL exposed by the official tutorial: **INACCESSIBLE through the current web retrieval path**.
5. Container `curl -I` to the official STAC item endpoint: **FAILED before HTTP with DNS resolution error** (`Could not resolve host: stac.astrogeology.usgs.gov`).

These failures are transport/runtime access failures. They do not establish that the source is unavailable or that the collection has zero items. The official tutorial's `pystac-client` example provides a legitimate retrieval route from a network-enabled environment.

## Result

**Source readiness is SUPPORTED; item/raster ingestion is BLOCKED in this automation runtime by DNS/API access.** This is not a scientific null and does not block the NASA repository as a whole.

No item ID, current live item count, raster pixel, terrain measurement, DTM asset URL, QA score or scientific result is claimed. No actual raster was downloaded. No MOLA comparison or slope calculation was run.

## Next decisive test

On a network-enabled authorized environment, run the official `pystac-client` query against the pinned Jezero bbox and request one item first. Preserve:
- raw STAC item JSON and content hash;
- item ID, footprint, acquisition identifiers and collection version;
- exact `dtm`, `qa_metrics`, `intersection_error`, `mola_csv` and `orthoimage` asset hrefs;
- WKT2/CRS, GSD, raster band units, nodata and QA masks;
- COG byte-range behavior and a small deterministic elevation window with uncertainty.

Do not mosaic items until their MOLA-control lineage and QA are checked. Compare one pinned DTM window with same-area MOLA context. If the item query succeeds but the DTM asset is missing or QA is poor, preserve the failure and select another item by a preregistered rule rather than hand-picking a visually attractive result.

## Claim states

- Repo operating system: SUPPORTED.
- Public controlled CTX collection metadata: SUPPORTED.
- Current live Jezero item count: NOT MEASURED.
- Actual CTX DTM item/raster ingestion: BLOCKED IN THIS RUNTIME.
- Terrain sample / CRS-registration / MOLA comparison: NOT YET MEASURED.
- Cross-body similarity: NOT YET PROVEN.
- Known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Local validation advantage: NOT YET PROVEN.
- Challenge-selection superiority: NOT YET PROVEN.

No UI polish, field data, user test, competition submission or deployment was performed.
