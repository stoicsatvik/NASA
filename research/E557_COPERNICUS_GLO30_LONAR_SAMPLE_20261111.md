# E557 — Copernicus GLO-30 public COG sample near Lonar (2026-11-11)

## Question

Can a public, anonymous Earth DEM provide bounded, reproducible terrain windows at the Lonar literature lead and a nearby comparison point after NASADEM's CMR metadata route resolved only a protected data path?

## Provenance and exact execution

- Repository: stoicsatvik/NASA
- Branch: `research/e557-copernicus-glo30-lonar-sample-20261111`
- Draft PR: #117, stacked on E556; main unchanged
- Exact code/test head: `0679ef0ab45903738fdf80e086b078e61533c077`
- Exact-head Actions: [#43050765819](https://github.com/stoicsatvik/NASA/actions/runs/43050765819), SUCCESS
- Deterministic tests: **7/7 passed**.
- Artifact: [#13868973608](https://github.com/stoicsatvik/NASA/actions/runs/43050765819/artifacts/13868973608), 2,482 bytes; ZIP SHA-256 `55830d1d3457d0692f61492fb7caede6777797f5bd930bb7590fe1772a053ca7`.
- Two earlier test runs failed only because the synthetic fixture's expected minimum and relief were miscalculated; both expectations were corrected from the actual fixture arithmetic. No production thresholds or assertions were weakened.

## Source and access

Copernicus DEM GLO-30 Public, tile `Copernicus_DSM_COG_10_N19_00_E076_00_DEM`, anonymous AWS Open Data bucket `copernicus-dem-30m`.

- HEAD: HTTP 200; object length **39,295,710 bytes**; `Accept-Ranges: bytes`.
- Header probe: HTTP 206, exact range 0–16,383, **16,384 bytes**; TIFF signature `49492a00`.
- Full-resolution raster: 3,600 × 3,600, float32, EPSG:4326, tiled, 1,024 × 1,024 blocks, DEFLATE, 2/4/8 overviews, `AREA_OR_POINT=Point`.
- No full tile was downloaded or retained. GDAL accessed the two COG blocks containing the windows; exact GDAL network bytes were not measured. Each block is 4 MiB uncompressed, so the two touched blocks represent 8 MiB of possible uncompressed block payload, not measured network transfer.
- The GeoTIFF band unit tag is absent (`units=null)). The official product handbook specifies vertical units of metres and vertical datum EGM2008 (EPSG:3855); horizontal coordinates are WGS84-G1150 (EPSG:4326).
- The product is a **Digital Surface Model**, including buildings, infrastructure and vegetation. It is not a bare-earth DTM. The public GLO-30 product is nominally 1 arc-second and is derived primarily from TanDEM-X observations (2011–2015), with local infill from other DEM sources. A source-lineage/quality mask is needed before treating every cell as equivalent.

## Measured windows

Both windows are 17 × 17 (289 valid samples), approximately 465 m east–west × 492 m north–south at the sample latitude.

| Point | Median elevation | Mean | Population SD | Min–max | Local relief | Central slope |
|---|---:|---:|---:|---:|---:|---:|
| Lonar literature lead (19.9750 N, 76.5090 E) | 479.500 m | 479.500 m | 0.000 m | 479.500–479.500 m | 0.000 m | 0.000° |
| Nearby local comparison (19.8000 N, 76.3000 E) | 570.597 m | 569.788 m | 4.520 m | 561.960–576.025 m | 14.064 m | 4.760° |

The Lonar window is exactly flat at the raster's reported 0.5 m vertical quantization. This could reflect a water-covered/flat patch, a local product treatment, or the chosen point falling away from the crater rim; **the current receipt cannot distinguish these explanations**. Do not call it a crater-wide property. The Copernicus water-body and fill/lineage masks were not acquired in E557.

The nearby point is a descriptive comparison, not a negative label. Neither point is an independently validated positive/negative pair. The catalogue's coordinates are approximate (about 10 km for the Lonar literature lead), so this 0.5 km window is not a site-wide sample.

## Interpretation

- Anonymous public GLO-30 COG access for this exact tile: **SUPPORTED**.
- Two descriptive DSM windows: **MEASURED**.
- Bare-earth terrain comparability: **NOT ESTABLISHED**.
- Cross-body similarity: **NOT YET PROVEN**.
- Known-site recovery: **NOT YET MEASURED**.
- Novel analogue discovery: **NOT YET PROVEN**.
- Local validation advantage: **NOT YET PROVEN**.

The 479.5 m flat window is a useful falsification prompt, not an analogue result. Without the water-body mask and fill/lineage layer, treating it as landform roughness would be unsafe. The product's EGM2008 vertical reference must also be transformed/normalized before comparison with planetary elevations.

## Next discriminating work

1. Acquire the Copernicus WBM and FLM/source-lineage layers for this same tile, if a legitimate public path exists; determine whether the Lonar window is classified as water and whether its elevation source was infilled.
2. Sample a crater-rim/annulus transect with multiple coordinate-uncertainty-aware windows rather than relying on one approximate centre point.
3. Independently audit the public Planetary Analogue Catalogue (16 sites, 96 references, all 16 currently Draft) and USGS Known Terrestrial Analog Sites data release (CC0) as candidate-positive sources. They are not non-analogue controls.
4. Keep the DSM separate from bare planetary topography; do not concatenate raw elevations or promote two points into E001 labels.

## External product references

- Copernicus Data Space product description: https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM
- Copernicus DEM Product Handbook: https://dataspace.copernicus.eu/sites/default/files/media/files/2024-06/geo1988-copernicusdem-spe-002_producthandbook_i5.0.pdf
- Copernicus DEM DOI: https://doi.org/10.5270/ESA-c5d3d65
- The catalogue/lineage masks are described in the Copernicus GLO30 Earth Engine catalog: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_DEM_GLO30_2024_1
