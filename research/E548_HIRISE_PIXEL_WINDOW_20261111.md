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

The dedicated workflow runs deterministic fixtures and then the bounded live source probe. Exact-head results and the bounded source receipt are recorded below.

## Exact-head result (11 November 2026)

- Draft PR #108, branch research/e548-hirise-pixel-window-20261111.
- GitHub Actions run [#43023187910](https://github.com/stoicsatvik/NASA/actions/runs/43023187910) succeeded: 9/9 deterministic tests passed; live bounded probe completed.
- The exact PDS3 label was fetched (2,296 bytes; SHA-256 99b972f7ea13f9e05e9d3f265435a0566b53dbde4088781673edeb0b6d24cade). It identifies IEEE_REAL, 32-bit samples, EQUIRECTANGULAR, centre latitude/longitude 0°, A-axis radius 3,396.19 km and 59,274.6975 pixels/degree. It does not expose a standalone UNIT or MISSING_CONSTANT field.
- GeoTIFF GDAL_NODATA supplies -3.4028226550889045e+38; no nodata values occurred in this window.
- 4,096/4,096 finite and usable float32 samples were read from column 10,668 / row 10,712, 64×64. Raw sample values: min −2,439.2717, median −2,436.7209, mean −2,436.6555, SD 1.2090, max −2,433.9929. Sample SHA-256: f9cb7459bc3c6030c29c84070913cf4ff20d0650a3e4c4d438bcf255c2c2ae65.
- 74 exact HTTP Range requests; 188,767 total bytes transferred, below the 1 MB TIFF cap. Receipt artifact [13854994460](https://github.com/stoicsatvik/NASA/actions/runs/43023187910).
- The GeoTIFF uses projected CRS code 32767 (user-defined), not a directly comparable EPSG/ESRI code. This is not evidence of a different physical CRS. Both official USGS product pages describe the CTX and 2020 HiRISE products as equirectangular, with 3,396,190 m spherical radii, planetocentric latitude, positive-east longitude and metre vertical units. Exact parameter-level transform equivalence and common valid-pixel support remain to be tested.
- Local CTX/HiRISE residual, cross-body similarity and E001 known-site recovery remain NOT YET MEASURED / NOT YET PROVEN. No raw pixels were uploaded.

Next: reconstruct the user-defined HiRISE projection from its PDS3 label and GeoKeys, verify it against the E544 CTX CRS, then compare area-matched 1 m HiRISE aggregates to the 20 m CTX raster with nodata masks and preregistered ±6 m shift sensitivity. Do not fit a shift to maximize agreement and call it validation.

