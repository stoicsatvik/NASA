# E547 — bounded direct controlled HiRISE GeoTIFF range probe (11 November 2026)

## Question

E546 established that the official 2025 MSR HiRISE mosaic ZIP supports HTTP Range, but its DTM member is ZIP-DEFLATE and cannot be accessed as a small TIFF window through ordinary ZIP member offsets.

A separate USGS 2020 Mars 2020 Terrain Relative Navigation HiRISE product page and public S3 directory expose a direct 1 m DTM GeoTIFF. E547 tests whether that distinct, older controlled product can be inspected through bounded TIFF metadata and segment-range reads.

This is an alternate-source feasibility test. It is **not** a substitute for the 2025 MSR mosaic and does not establish raster registration.

## Pinned source

- Publisher: USGS Astrogeology Science Center.
- Product: Mars 2020 Terrain Relative Navigation HiRISE DTM mosaic.
- Product DOI: https://doi.org/10.5066/P9QJDP48
- Product page: https://astrogeology.usgs.gov/search/map/Mars/Mars2020/JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40
- Public S3 directory: https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/HiRISE/index.html
- Exact direct object: \`JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40.tif\`
- The USGS directory lists the DTM GeoTIFF and XML/PDS labels as separate objects.
- This is the 2020 TRN product, not the 2025 MSR mosaic (DOI 10.5066/P13CPYYU) tested by E546.

## Frozen procedure and transfer limits

1. Validate the exact HTTPS host and path; no query, alternate host, credentials, fragment or redirect is admitted.
2. Issue HEAD and require HTTP 200 plus a positive numeric Content-Length.
3. Use a seekable HTTP Range reader for TIFF header, IFD and tag arrays.
4. Inspect only the first TIFF page and its structural metadata: dimensions, dtype, compression, tiling/strip layout, georeferencing-tag presence and segment table.
5. Read at most one compressed tile/strip, and only if its declared byte count is at most 512,000 bytes.
6. Cap all HTTP range bytes at 1,000,000. If the server ignores Range, close the response without consuming its body.
7. Retain only range receipts, hashes, TIFF metadata and a short compressed-segment prefix. Do not decode pixels or upload raster bytes.

## Deterministic controls

Synthetic TIFF fixtures cover:
- exact URL allowlisting;
- tiled TIFF metadata and one bounded segment read;
- refusal to read a segment larger than the cap;
- Range ignored without consuming a full response;
- mismatched Content-Range rejection;
- transfer-budget enforcement before a network request;
- invalid seeks outside the pinned object.

## Exact-head result

GitHub Actions [#43021100543](https://github.com/stoicsatvik/NASA/actions/runs/43021100543) succeeded on head `16c2e9ba64102ffff37dd2c968736b69ebab3f06`:

- Deterministic fixtures: **8/8 passed**.
- HTTP HEAD: **200**, `Content-Type: image/tiff`, `Accept-Ranges: bytes`.
- Direct TIFF object size: **1,839,545,409 bytes**.
- TIFF: one page, **21,400 × 21,488**, float32, 32 bits/sample, one sample/pixel.
- Compression tag: **1 (uncompressed)**.
- Layout: **not tiled**; **21,488 strips**, one row per strip, each full row 85,600 bytes.
- Georeferencing tags present: ModelPixelScale `[1, 1, 0]`, ModelTiepoint `[0, 0, 0, 4577366, 1106618, 0]`, GeoKeyDirectory present.
- One 85,600-byte row strip was fetched by exact HTTP Range and hashed; no pixel values were decoded.
- **12 range requests; 258,025 total bytes transferred**, below the 1,000,000-byte cap.
- Compact receipt artifact [13854428457](https://github.com/stoicsatvik/NASA/actions/runs/43021100543/artifacts/13854428457), ZIP SHA-256 `8ed484a78adce58569e4ed159d8a627e81bca924f6c95a7296085d3b93084156`.

Outcome: **DIRECT_TIFF_SEGMENT_RANGE_READ**. The 2020 direct TIFF is range-addressable at the strip level. It is not tiled, and this experiment does not establish COG status.

### Preserved interpretation boundary

- Direct object existence, TIFF metadata access and one bounded strip read: **SUPPORTED**.
- A 64×64 pixel-window read: **NOT YET MEASURED**.
- Pixel decoding, nodata semantics, vertical units and local CTX/HiRISE registration: **NOT YET MEASURED**.
- The 2020 product is not the 2025 MSR mosaic tested by E546.
- No raster bytes or pixel arrays were uploaded; only the compact receipt was retained.

## Interpretation boundary

Even if the direct 2020 TIFF supports a bounded segment read, this does not establish:
- that the file is a Cloud Optimized GeoTIFF;
- that the 2020 mosaic is the exact CTX reference used by the 2025 MSR product;
- that 2020 and 2025 HiRISE mosaics share a common pixel grid or vertical datum;
- local CTX/HiRISE registration residuals;
- common valid-pixel support with the E544 CTX DTM and E545 MOLA observed-count window;
- cross-body similarity, known-site recovery, novel analogue discovery or route safety.

No pixel values are decoded by this experiment.

## Next gate

If the 2020 DTM supports bounded segment access, inspect its GeoTIFF georeferencing tags and sidecar label, then compare its published coordinate reference and coverage against the E544 CTX TRN DTM. Keep the 2025 MSR mosaic as a separate product lineage. If the direct TIFF is not range-addressable or has no small independently readable segment, preserve the negative result and do not download it in full.
