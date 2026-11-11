# E548 — bounded controlled HiRISE pixel-window acquisition (11 November 2026)

## Question

Can the official 2020 Mars 2020 TRN HiRISE DTM be sampled as actual float32 elevation values through small, exact HTTP byte ranges, with PDS3 missing-value semantics and GeoTIFF georeferencing inspected first?

This is the next gate after E547, which proved metadata and one complete strip were range-readable but deliberately decoded no pixels.

## Pinned sources

- Publisher: USGS Astrogeology Science Center.
- Product: Mars 2020 Terrain Relative Navigation HiRISE DTM mosaic (2020 TRN).
- DOI: https://doi.org/10.5066/P9REJ9JN
- Product metadata: https://astrogeology.usgs.gov/search/map/Mars/Mars2020/JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40
- Direct TIFF and PDS3 label are pinned to exact public S3 object paths in the experiment.
- This is not the distinct 2025 MSR mosaic (DOI 10.5066/P13CPYYU).

## Frozen sample

- Raster window: column 10,668; row 10,712; width 64; height 64.
- Selected from the center of the published CTX/HiRISE metadata-envelope intersection, not from observed sample values.
- Only uncompressed float32, one-sample, one-row-per-strip TIFF layout is admitted.
- Each row request is exactly 64 × 4 = 256 bytes; expected sample payload is 16,384 bytes, plus bounded TIFF metadata.
- Total TIFF transfer cap: 1,000,000 bytes; label cap: 256,000 bytes.
- Range responses must be HTTP 206 with exact Content-Range and byte counts. If the server ignores Range, the response is closed without consuming its body.
- No full-raster download, raw pixel upload, credentials, or external write is permitted.

## Measurements

The receipt records source hashes, label fields, TIFF dimensions/dtype/layout, GeoTIFF georeferencing keys, sample SHA-256, finite/missing counts and descriptive statistics. It retains no raw pixel array.

## Interpretation limits

- A successful window read supports bounded pixel acquisition for this one 2020 TRN product only.
- Metadata-envelope overlap is not common valid-pixel support.
- USGS product metadata reports an approximately 0.4 m median vertical offset between the HiRISE and CTX DTM mosaics and published image-feature registration statistics; E548 does not independently reproduce those values.
- Local CTX/HiRISE residuals, common-valid-pixel support, cross-body similarity, E001 known-site recovery, novel analogue discovery and route safety remain unproven/unmeasured.
- The 2020 TRN product must not be conflated with the 2025 MSR mosaic.

## Validation

The dedicated workflow runs deterministic fixtures and then the bounded live source probe. Exact-head results are appended after the workflow completes.
