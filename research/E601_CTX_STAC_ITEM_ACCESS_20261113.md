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

## Prior successful item/raster acquisition — project state

E601 is a **current-runtime recheck**, not the first CTX item acquisition. The earlier exact-head experiments remain valid:

- **E580** [workflow #43212727544](https://github.com/stoicsatvik/NASA/actions/runs/43212727544) acquired the pinned Jezero item `P18_007925_1987_XN_18N282W__P19_008650_1987_XI_18N282W`, its item metadata and a 4 KiB DTM byte range (HTTP 206).
- **E581** [workflow #43213482433](https://github.com/stoicsatvik/NASA/actions/runs/43213482433) downloaded the 18,114,156-byte DTM in memory and sampled five deterministic 64×64 windows: 20,480 valid pixels, with no nodata in those windows. The TIFF/STAC band metadata did not declare a vertical unit. The collection processing documentation supports a metre-valued areoid interpretation, but the item-specific command remains unverified.
- **E582** [workflow #43215530283](https://github.com/stoicsatvik/NASA/actions/runs/43215530283) acquired the 398-byte QA metrics and 344,365-byte MOLA-control CSV. The QA summary was mean +27.3687 m, median +26.7783 m and SD 10.934 m. The 8,750 MOLA rows are control inputs, not held-out validation; the pinned item was rejected for uncorrected absolute-elevation or long-baseline slope use pending residual investigation.
- **E583/E584/E586** screened nine Jezero products, acquired 9/9 QA assets and checked actual footprints. Six footprints were at least 99% inside the AOI, but the contained subset still had 14/15 intersecting pairs. QA spatial support is not established by footprint geometry.

Therefore, E601's negative result applies only to **re-acquisition from this current automation runtime on 13 November**. It does not invalidate the earlier successful item, raster, QA or MOLA-control acquisitions. No new item or raster was acquired in E601.

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
5. Container `curl -I` to the collection metadata's AWS API Gateway item host (`g6goyz4w56.execute-api.us-west-2.amazonaws.com`) and the public S3 bucket host (`astrogeo-ard.s3.amazonaws.com`): **FAILED before HTTP with DNS resolution errors**.

These failures are transport/runtime access failures. They do not establish that the source is unavailable or that the collection has zero items. The official tutorial's `pystac-client` example provides a legitimate retrieval route from a network-enabled environment.

## Result

**Current-runtime re-acquisition is BLOCKED by DNS/API access; prior item/raster/QA acquisition remains SUPPORTED by E580–E586.** E601 adds an environment-specific transport failure, not a new scientific null and not a reversal of the earlier data-readiness result.

No new item ID, live item count, raster pixel, terrain measurement, DTM asset URL, QA score or scientific result was acquired in E601. The earlier E581 pixel windows and E582 QA/MOLA-control summaries remain the authoritative project evidence; they must not be described as independent validation.

## Next decisive test

Do **not** repeat the already-acquired P18 item or its QA/MOLA assets. E580–E588 and E599 have already covered item acquisition, pixel sampling, QA, cohort geometry and the bounded public provenance surfaces. The next CTX experiment should run only if a genuinely distinct item-specific provenance route or an independent control source is found. If a new item is selected, use a predeclared cohort rule, retain only sanitized STAC fields and hashes (never signed query values or raw URLs), and inspect its `intersection_error`/orthoimage before any slope calculation. MOLA control points and post-control QA residuals must remain separate from held-out validation.

Otherwise, stop repeating the same P18/QA surfaces and prioritize the E600 independent-site data gate or a genuinely independent Mars reference product.

## Claim states

- Repo operating system: SUPPORTED.
- Public controlled CTX collection metadata: SUPPORTED.
- Current live Jezero item count: NOT MEASURED.
- P18 CTX DTM item and raster acquisition: SUPPORTED by E580/E581.
- Five P18 pixel windows: SUPPORTED by E581; vertical unit absent from raster metadata.
- P18 QA and MOLA-control asset acquisition: SUPPORTED by E582; not independent validation.
- Current-runtime re-acquisition: BLOCKED by DNS/API access in E601.
- Item-specific processing provenance and independent accuracy: NOT ESTABLISHED.
- Cross-body similarity: NOT YET PROVEN.
- Known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Local validation advantage: NOT YET PROVEN.
- Challenge-selection superiority: NOT YET PROVEN.

No UI polish, field data, user test, competition submission or deployment was performed.
