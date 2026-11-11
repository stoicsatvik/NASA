# E566 — 2025 HiRISE DTM/confidence archive range audit (12 November 2026)

## Question

Does the 2025 USGS Mars Sample Return HiRISE mosaic provide a second, quality-annotated source over the Jezero region where the 2020 HiRISE DTM had in-bounds nodata, and can the archive be inspected without downloading its 5.3 GB payload?

This is a coverage/quality-source gate for the Martian Map alternative. The 2025 product is aligned to the CTX reference; it is **not** an independent horizontal control network.

## Pinned source

- Publisher: USGS Astrogeology Science Center
- Product: Mars Sample Return Terrain Relative Navigation HiRISE DTM and Orthoimage Mosaics
- DOI: https://doi.org/10.5066/P13CPYYU
- Official metadata: https://astrogeology.usgs.gov/search/map/mars-sample-return-terrain-relative-navigation-hirise-dtm-mosaic
- Exact archive URL: https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/Mars/MSR_TRN_HiRISE_soc_003_USGS_release_aug2024/MSR_TRN_HiRISE_soc_003_USGS_release_aug2024_mosaics.zip
- Published archive size: 5.3 GB
- Published nominal resolution: 1 m/pixel
- Published bounds: 77.057–77.380°E, 18.135–18.588°N
- Published contents: DTM, orthoimage and confidence mosaics
- Published processing: 8 of 10 stereo pairs completed; mosaic aligned to CTX reference to <6 m at the 93rd percentile and <10.2 m at the 99th percentile; a crater-rim vertical-offset exception is documented.

## Frozen bounded protocol

1. Send HEAD to the exact USGS-published S3 object URL with redirects disabled.
2. Require a positive Content-Length.
3. Use a seekable HTTP-range adapter. Every GET must return HTTP 206 and an exact matching Content-Range.
4. Let Python's ZIP reader inspect only the central directory and local member headers.
5. Read at most 16 bytes from each of at most 24 TIFF member prefixes.
6. Cap cumulative range transfer at 32 MiB and any single range at 16 MiB.
7. Retain only archive metadata, member names/roles, compression metadata, TIFF magic checks and byte-range receipts. Never retain raster pixels or full member contents.
8. Preserve redirects, ignored ranges, malformed ZIPs and missing confidence members as negative outcomes. Never silently follow an alternate host or download the full archive.

## Interpretation rules

- A DTM member plus a confidence member supports **archive-level source availability only**.
- A valid TIFF prefix does not prove readable georeferencing, confidence semantics, spatial coverage, or valid pixels at any MOLA point.
- A ZIP-stored TIFF may be amenable to later byte-range TIFF parsing; a deflated ZIP member requires member decompression and may defeat bounded random access.
- The 2025 mosaic's alignment to CTX means it cannot independently validate CTX horizontal control. Its confidence layer must not be called calibrated uncertainty until its metadata and semantics are inspected.
- No route-safety, cross-body similarity, known-site recovery, novel analogue discovery or local validation advantage is claimed.

## Validation

Pending exact-head GitHub Actions run. Deterministic tests use synthetic ZIP fixtures and a fake HTTP range server. The live workflow uses no credentials and stores only a compact receipt.

## Exact-head result

Pending.

## Claim states

- 2025 archive range access: NOT YET MEASURED.
- 2025 DTM member presence: NOT YET MEASURED.
- Confidence member presence: NOT YET MEASURED.
- 2025 member random access: NOT YET MEASURED.
- Replacement of 2020 HiRISE nodata: NOT YET MEASURED.
- Independent horizontal registration: NOT YET MEASURED.
- Cross-body similarity: NOT YET PROVEN.
- E001 known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Route safety: NOT CLAIMED.

## Next gate

If the archive supports bounded member access, pin the DTM and confidence TIFF names and their GeoTIFF/PDS metadata. Then sample only the 92 previously observed-MOLA points that landed on 2020 HiRISE nodata, preserving the exact point denominator and confidence-mask semantics. If the archive is not range-addressable, reject this product for the current 48-hour event rather than downloading 5.3 GB. Do not call the 2025 mosaic an independent registration validation.
