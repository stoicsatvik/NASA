# E552 — provenance audit of unsupported HiRISE windows in E550 (11 November 2026)

## Question

Are E550's three unsupported CTX/HiRISE grid positions caused by partial area coverage, missing CTX cells, or HiRISE windows containing only the product's declared nodata value?

## Frozen inputs

- E550 Actions run [#43025458917](https://github.com/stoicsatvik/NASA/actions/runs/43025458917), artifact 13855824623, artifact ZIP SHA-256 `a1cd14c272ed122f82edaac5f72e788d799ad7311bd488f8beffd989f487ccb1`, receipt JSON SHA-256 `bb13f638136d038ec10d683b26fdc48d684fce38957360bc60f121b6d3401123`.
- E549 Actions run [#43024579396](https://github.com/stoicsatvik/NASA/actions/runs/43024579396), artifact 13856547599, artifact ZIP SHA-256 `67b51cc53cc00dda6e90ee7df0c771fecacd2443a587f4e9b996d2344ec9fed6`, receipt JSON SHA-256 `8e5ef2ed9f33f304a6cda63ec4c775e1434984814dd2caa60aa2e7a7a021f532`.
- Both receipts identify the same controlled HiRISE DTM, USGS DOI [10.5066/P9REJ9JN](https://doi.org/10.5066/P9REJ9JN).
- E549 records the GeoTIFF `GDAL_NODATA` value as `-3.4028226550889045e+38`.
- Each E550 HiRISE sample window is 113×113 float32 values.

No raster was downloaded again and no raw pixel arrays are stored in this audit.

## Discriminating check

Compute SHA-256 for a 113×113 little-endian float32 array filled entirely with the E549 nodata value:

`939e55e9e3abcb6ee16e1ef5761cb7de68a2794c13b91e173db9698310bf3179`.

Compare this digest with each E550 window's recorded sample hash. This is a byte-level equality check against the independently recorded nodata sentinel, not a statistical approximation.

## Result

All three unsupported windows have the exact all-nodata digest:

| Patch | CTX valid cells | Common valid cells | HiRISE window classification |
|---|---:|---:|---|
| x15_y15 | 25 | 0 | ALL NODATA |
| x50_y85 | 25 | 0 | ALL NODATA |
| x85_y85 | 25 | 0 | ALL NODATA |

The other six windows have 25/25 common valid CTX cells and sample hashes different from the all-nodata digest.

Therefore:
- Three of nine E550 HiRISE windows are byte-identical to an all-nodata 113×113 float32 window.
- All nine CTX patches contain 25 valid cells.
- The six E550 residual patches remain measured; the three unsupported patches remain excluded.
- The cause of the nodata is **NOT DETERMINED**. The digest cannot distinguish an unsurveyed footprint from a masked or otherwise invalid terrain region.

## Consequence for E551

E551's exact six-patch permutation result remains unchanged:

- (p(R^2 geq R^2_{obs}) = 0.2444).
- (p(\|\nabla z\| geq \|\nabla z\|_{obs}) = 0.1500).
- Two-sided sign-test (p=0.21875).

The result still does not support a spatially coherent residual gradient. E552 strengthens the missingness description but does not make the six observed locations representative of the nine-position grid. E551's exchangeability statement remains conditional on the six measured patches.

## Validation

- Five deterministic regression tests.
- Recomputes the all-nodata digest from the E549 nodata value and frozen 113×113 shape.
- Requires exactly three all-nodata unsupported windows and six non-nodata full-support windows.
- Preserves the unknown nodata mechanism and E551 claim boundary.
- No new raster acquisition, pixel decode, registration fit, correction surface, or cross-body inference.

## Next gate

Do not impute or fit a correction plane. If broader spatial inference is needed, define a new preregistered sampling design inside a verified common-valid footprint, or obtain an independent reference product. Do not silently replace the three failed locations after observing their residual pattern.
