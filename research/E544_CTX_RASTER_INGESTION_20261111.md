# E544 — bounded official Jezero CTX TRN DTM acquisition (2026-11-11)

## Question

Can the documented USGS Mars 2020 TRN CTX DTM be acquired through its published direct file URL and parsed as a real GeoTIFF, rather than a catalogue preview or HTML response?

## Pinned source

- Publisher: USGS Astrogeology Science Center
- Product: Mars 2020 Terrain Relative Navigation CTX DTM Mosaic
- DOI: https://doi.org/10.5066/P906QQT8
- Product metadata: https://astrogeology.usgs.gov/search/map/mars_2020_terrain_relative_navigation_ctx_dtm_mosaic
- Direct file: https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0.tif
- Published file size: approximately 9.3 MB
- Published nominal grid spacing: 20 m/pixel

The source URL is pinned to one exact HTTPS host and path. No credentials, alternate guessed URL shapes, or access-control workarounds are used.

## Experiment

1. Download at most 20,000,000 bytes from the exact published file URL.
2. Record HTTP status, content type, byte count and SHA-256.
3. Require classic TIFF or BigTIFF magic before parsing.
4. Open with Rasterio and record the actual GeoTIFF driver, dimensions, band count, data type, CRS, affine transform, bounds, resolution, nodata, units, scale and offset.
5. Inspect five deterministic 64×64 windows (four corners and center); retain only valid-pixel counts and summary statistics, never raw pixel arrays.
6. Upload only the compact JSON receipt as a short-retention GitHub Actions artifact. The source raster is not committed or uploaded.

## Decision rules

- A verified GeoTIFF with at least one valid sample window supports **raw CTX raster acquisition and bounded pixel inspection** for this one product.
- A 403/404/410, redirect outside the pinned USGS host, or non-TIFF response is preserved as a route-specific **NEGATIVE_RESULT**, not silently relabelled as a download.
- Network, content-length or parser errors remain **ERROR** and fail the workflow while preserving any receipt artifact.
- Missing CRS, units or nodata metadata remain missing; no values are inferred.
- No vertical-reference transformation, CTX/HiRISE registration, MOLA observed-count analysis, cross-body comparison, known-site recovery or route-safety claim is made by E544.

## Claim ceiling before execution

- Published Jezero MOLA/CTX/HiRISE metadata-envelope compatibility: SUPPORTED (E542).
- MOLA local scale anisotropy correction: SUPPORTED as projection geometry (E543).
- Raw CTX GeoTIFF acquisition: NOT YET MEASURED.
- Cross-body similarity: NOT YET PROVEN.
- Known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Route safety: NOT CLAIMED.

## Next gate after a successful receipt

Pin the exact 2025 HiRISE CTX-reference lineage; acquire a bounded HiRISE sample and the MOLA topography plus observed-count tile; reconcile body-fixed reference, projection, units, nodata and support; then compare elevation profiles only over verified common valid-pixel support. Do not treat metadata-envelope overlap as raster overlap.
