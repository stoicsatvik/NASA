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

The COG and STAC band metadata do **not** explicitly declare a vertical unit: `raster:bands[].unit` is absent and GeoTIFF band units are null. The numeric values below therefore remain recorded as raw raster values, not as a direct metadata assertion of metres.

| Window | Min | P05 | Median | Mean | P95 | Max | SD |
|---|---:|---:|---:|---:|---:|---:|---:|
| West-mid | -2419.50 | -2410.15 | -2396.99 | -2395.20 | -2378.13 | -2372.81 | 9.82 |
| Centre | -2546.29 | -2538.43 | -2532.51 | -2531.91 | -2524.84 | -2522.26 | 4.50 |
| East-mid | -2565.03 | -2562.43 | -2557.59 | -2547.57 | -2495.61 | -2466.85 | 21.10 |
| North-mid | -2027.18 | -2021.35 | -2002.91 | -1980.77 | -1872.30 | -1848.70 | 46.45 |
| South-mid | -2617.66 | -2607.35 | -2553.26 | -2557.73 | -2512.03 | -2475.15 | 28.00 |

No slope was computed in E581. That is deliberate, not a parser failure.

## Source interpretation and unit boundary

The official USGS CTX DTM collection documentation states that these products are generated with Ames Stereo Pipeline, that a 20 m/post DTM is extracted with `point2dem`, and that the DTM is then processed with `dem_geoid` to obtain heights above the equipotential Mars surface (areoid):  
https://stac.astrogeology.usgs.gov/docs/data/mars/ctxdtms/

The ASP `point2dem` documentation states that `point2dem -r mars` produces elevations in metres relative to the IAU reference spheroid, and that `dem_geoid` converts those heights to the MOLA areoid:  
https://stereopipeline.readthedocs.io/en/stable/tools/point2dem.html

The ASP `dem_geoid` documentation describes the ellipsoid-to-areoid adjustment and identifies the Mars correction source; its custom correction GeoTIFF is specified in metres:  
https://stereopipeline.readthedocs.io/en/stable/tools/dem_geoid.html

**Refined conclusion:** the documented collection-level processing chain supports a metre-valued elevation interpretation relative to the Mars areoid. This is stronger than an unsupported guess from raster magnitudes. It is still a **processing-documentation inference**, not a value read from the COG's missing unit field. The exact per-item processing command/provenance has not yet been independently inspected, so the receipt continues to report `vertical_unit: unknown` from file metadata.

The USGS documentation also reports typical vertical precision around 3–5 m and warns that effective resolution is coarser than the 20 m posting. A 20 m adjacent-pixel slope is therefore especially sensitive to stereo noise; even a 200 m baseline needs a stated uncertainty and quality context. No slope or route-safety claim follows from the five sampled windows.

## Next discriminating gate

1. Inspect the item's `qa_metrics` asset and MOLA-control CSV, retaining only bounded summaries and hashes. Determine whether the item exposes useful residual statistics and whether the CSV has the expected control-point schema.
2. Look for item-specific provenance commands or a pinned processing manifest. If absent, retain the metre label as a collection-level documented inference rather than promoting it to direct metadata.
3. Only then calculate conditional 20 m and 200 m slope summaries. Label any result as conditional on the documented unit inference, report valid-pair counts and nodata handling, and keep the USGS 3–5 m vertical-precision caveat attached.
4. Do not infer route traversability from local slope summaries alone.

## Claim states

- Public CTX item and COG acquisition: SUPPORTED.
- Raster/STAC shape and transform agreement: SUPPORTED FOR THIS ITEM.
- Five valid pixel windows acquired: SUPPORTED.
- Vertical unit in TIFF/STAC band metadata: NOT REPORTED.
- Metre-valued elevation relative to areoid from documented collection processing chain: SUPPORTED AS A COLLECTION-LEVEL INFERENCE; item-specific command not independently verified.
- Slope descriptors: NOT YET MEASURED.
- QA/control residual assessment: NOT YET MEASURED.
- Cross-body similarity, E001 known-site recovery, novel analogue discovery, local validation advantage and challenge-selection superiority: unchanged / NOT YET PROVEN.

No raw raster, raw pixel arrays, field measurements, route-safety conclusions or competition outcomes are asserted.
