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


## E544.1 — allowlist correction (11 November 2026)

The first exact-head workflow (#43010052871) passed all **10/10 fixture tests** and reached the published URL. It returned a redirect to `asc-pds-services.s3.us-west-2.amazonaws.com`, which the initial single-host allowlist rejected. The receipt therefore recorded `REDIRECT_OUTSIDE_ALLOWLIST`; **no raster bytes were acquired**. This was a false negative caused by an over-restrictive redirect policy, not evidence that the public dataset is unavailable.

The official USGS Astrogeology CTX directory independently lists the exact same TIFF filename under that S3 host. E544 now permits only the exact pinned source URL and the exact corresponding S3 object path from that official directory. It does not permit arbitrary S3 paths or hosts. The corrected live acquisition and GeoTIFF parse are pending.


## E544 exact-head result (11 November 2026)

- Branch head: `e64a9e69d86d2a1953e71a07821d4e73c75d9294`.
- Exact-head GitHub Actions [#43010645516](https://github.com/stoicsatvik/NASA/actions/runs/43010645516): **12/12 fixture tests passed**; bounded live acquisition completed; compact receipt artifact **13850830857** uploaded.
- HTTP **200**, `image/tiff`, **9,662,387 bytes**, final object host/path exactly matched the official USGS PDS CTX directory entry.
- SHA-256: `16a1aa66c3f48c1bca252795827db7b417876217aff0f5e1aff18027fab2327b`.
- Rasterio opened a one-band float32 GeoTIFF, **1596 × 1512**, CRS **ESRI:103885**, affine resolution **20 × 20 CRS units**, and bounds **4573663.250853–4605583.250853 / 1079453.140188–1109693.140188**.
- Nodata: `-3.4028226550889045e+38`. Five deterministic 64×64 windows contained **20,480/20,480 valid pixels**. Their sampled values ranged from **-2699.7209 to -2033.5281**; these are bounded window statistics, not a full-raster distribution.
- The GeoTIFF band unit tag is absent (`unit_band_1=null)). The USGS product metadata separately lists vertical coordinate-system units as **meters**. Preserve that provenance distinction rather than claiming the TIFF itself encodes a band unit.
- The raster was read in memory; no raw raster or pixel array was committed or uploaded. Only the 1,816-byte JSON receipt artifact was retained.

## Updated claim state

- Raw CTX GeoTIFF acquisition and bounded pixel inspection for this pinned product: **SUPPORTED**.
- Jezero metadata-envelope compatibility: SUPPORTED (E542).
- MOLA local scale anisotropy correction: SUPPORTED as projection geometry (E543).
- CTX/HiRISE raster co-registration: NOT YET MEASURED.
- MOLA local observed-count support: NOT YET MEASURED.
- Cross-body similarity: NOT YET PROVEN.
- Known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Route safety: NOT CLAIMED.

The first E544 run's allowlist false negative and its receipt remain preserved; the corrected exact-object redirect policy is what produced the successful acquisition.
