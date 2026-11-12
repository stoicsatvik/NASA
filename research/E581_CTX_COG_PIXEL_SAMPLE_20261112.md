# E581 — pinned CTX COG pixel-window sampling

Date: 12 November 2026  
Branch: `research/e581-ctx-cog-pixel-sampling-20261112`  
Base: E580 / PR #140. Draft research only; `main` untouched.

## Question

Does the pinned E580 Jezero CTX item resolve to a readable COG whose item-level projection/shape/transform match the raster, and can actual valid pixel windows be sampled without persisting raw data?

## Pinned source

- Collection: `mro_ctx_controlled_usgs_dtms`
- Item: `P18_007925_1987_XN_18N282W__P19_008650_1987_XI_18N282W`
- Item datetime: 2023-04-18T12:00:00Z
- Footprint bbox: [77.2128114, 17.7577892, 77.9059771, 19.3423089]
- DTM asset: public USGS Astrogeology S3 COG; URL values are not stored.
- Full asset SHA-256: `2acf3fb601fc9728c88cf9b768cc20c0f51dd6ef143936d429f7ca1623ca1ba0`

## Exact-head result

Workflow [#43213482433](https://github.com/stoicsatvik/NASA/actions/runs/43213482433) passed **8/8 deterministic tests**, downloaded the 18,114,156-byte DTM in memory, opened it with rasterio 1.4.3, sampled five deterministic 64×64 windows, and uploaded receipt artifact [#13942017708](https://github.com/stoicsatvik/NASA/actions/runs/43213482433/artifacts/13942017708). Artifact SHA-256: `24e8958ec203c015d67915753d69f40c66523ee89153aaa88b1d4e5c9a5460c9`.

Raster contract:
- GeoTIFF, 2013 columns × 4622 rows, one float32 band.
- NoData: -32767.
- Tiled 512×512, DEFLATE compression.
- Horizontal resolution: 20.162955 m × 20.162955 m.
- CRS is present, linear units are metres, EPSG authority code is absent.
- Item STAC shape and affine transform match the actual raster exactly within the frozen tolerance.
- Item WKT2 hash and raster WKT hash match.
- 20,480 valid pixels sampled across five windows; all five windows have 0% nodata.

## Sample-window results

The COG and STAC band metadata do **not** explicitly declare a vertical unit: `raster:bands[].unit` is absent and GeoTIFF band units are null. Therefore these values are recorded as raw raster values, not labelled metres.

| Window | Min | P05 | Median | Mean | P95 | Max | SD |
|---|---:|---:|---:|---:|---:|---:|---:|
| West-mid | -2419.50 | -2410.15 | -2396.99 | -2395.20 | -2378.13 | -2372.81 | 9.82 |
| Centre | -2546.29 | -2538.43 | -2532.51 | -2531.91 | -2524.84 | -2522.26 | 4.50 |
| East-mid | -2565.03 | -2562.43 | -2557.59 | -2547.57 | -2495.61 | -2466.85 | 21.10 |
| North-mid | -2027.18 | -2021.35 | -2002.91 | -1980.77 | -1872.30 | -1848.70 | 46.45 |
| South-mid | -2617.66 | -2607.35 | -2553.26 | -2557.73 | -2512.03 | -2475.15 | 28.00 |

No slope was computed because the file's vertical-unit metadata is absent. This is deliberate, not a parser failure.

## Source interpretation and next gate

The official USGS CTX DTM documentation says the products contain heights above/below the Mars areoid and are processed through `dem_geoid` after ASP `point2dem`. The ASP documentation states that `point2dem` DEM heights are in metres and describes conversion to the MOLA areoid. This is a potentially sufficient *documented processing-chain inference* for metres, but it is not encoded in this COG's band metadata:
- https://stac.astrogeology.usgs.gov/docs/data/mars/ctxdtms/
- https://stereopipeline.readthedocs.io/en/stable/tools/point2dem.html

Next: record the unit as an explicitly sourced inference, not as TIFF metadata; compute multi-baseline slope summaries (20 m and 200 m) with the unit caveat; inspect the item's QA metrics asset. USGS warns that 20 m posting is not 20 m effective resolution, that typical vertical precision is around 3–5 m, and that short-baseline slope can be highly sensitive to this error. No route-safety claim follows from these five windows.

## Claim states

- Public CTX item and COG acquisition: SUPPORTED.
- Raster/STAC shape and transform agreement: SUPPORTED FOR THIS ITEM.
- Five valid pixel windows acquired: SUPPORTED.
- Vertical unit in TIFF/STAC band metadata: NOT REPORTED.
- Vertical unit in metres from documented ASP/USGS processing chain: CANDIDATE SOURCE-BACKED INFERENCE; not yet applied to slope.
- Slope descriptors: NOT YET MEASURED.
- QA/control residual assessment: NOT YET MEASURED.
- Cross-body similarity, E001 known-site recovery, novel analogue discovery, local validation advantage and challenge-selection superiority: unchanged / NOT YET PROVEN.

No raw raster, raw pixel arrays, field measurements, route-safety conclusions or competition outcomes are asserted.
