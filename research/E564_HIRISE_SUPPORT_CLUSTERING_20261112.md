# E564 — spatial clustering of unsupported observed MOLA points

Date: 12 November 2026

## Question

Within the frozen Jezero 33×33 MOLA window, are the 90 observed MOLA bins outside the HiRISE raster and the 92 in-bounds-but-nodata bins spatially aggregated on the MOLA grid, or are they dispersed?

This is a descriptive follow-up to E563. It does not attempt to explain the missing support or repair it.

## Frozen inputs and method

- Reuse only the boolean masks already held in memory by E563: MOLA observed-shot mask, CTX valid mask, HiRISE in-bounds mask and HiRISE finite/non-nodata mask.
- Do not persist or emit raster values, point coordinates, row/column indices, or geometry arrays.
- Build a four-neighbor cardinal adjacency graph over observed MOLA bins only. Zero-count/interpolated MOLA bins are excluded from both nodes and edges.
- Report four-connected component sizes and same-category adjacency-edge counts for CTX-invalid, HiRISE-outside-bounds and HiRISE-inside-nodata categories.
- For each non-degenerate category, compare the observed adjacency count with 9,999 deterministic random relabelings that preserve the fixed observed MOLA mask and category count.
- Use seed 20261112. The upper-tail reference fraction is descriptive only; it is not an inferential p-value because the uniform-label reference does not model the deterministic raster footprint, geology or nodata-generation process.

## Claim boundary

The result can describe clustering on this one bounded MOLA lattice. It cannot identify why HiRISE pixels are absent, establish a physical geologic cause, estimate a registration shift, validate elevation values, or support route safety or analogue recovery. Do not impute or substitute unsupported pixels.

## Exact-head result

Pending the dedicated E564 workflow. Record the exact branch head, Actions run, artifact, component sizes, adjacency counts and reference summaries here after the bounded live run. Preserve any acquisition or parser failure as a negative result.

## Next gate

If unsupported points are strongly concentrated, use that only to prioritize an independent footprint/quality-mask or control-point provenance search. If they are dispersed, do not interpret that as evidence of valid coverage. In either case, independent horizontal-control provenance and analysis-grade Earth positive/control labels remain separate requirements.


## Exact-head live result (12 November 2026)

Exact branch head `ca9dfa437e30cc1cd83b747843c67b9bd54ba60f` completed [E564 workflow #43104061311](https://github.com/stoicsatvik/NASA/actions/runs/43104061311) successfully. E563 geometry plus E564 clustering tests passed **11/11**. Compact receipt: [artifact #13891699522](https://github.com/stoicsatvik/NASA/actions/runs/43104061311/artifacts/13891699522), ZIP SHA-256 `9a7a568353be95bc69b8e6ec627e9090d6724d23045559e9d731b63979dc90d4`.

### Bounded live support

- MOLA window: 33×33; **346/1,089** bins had observed shots.
- CTX valid support: **346/346** observed MOLA bins.
- HiRISE: 256/346 observed points inside raster bounds; **164/346** had finite/non-nodata pixels. Thus 90 were outside bounds and 92 were inside-but-nodata.
- Three-way common point support: **164/346 = 47.3988%**. This is point-center support, not area coverage.
- CRS parameter equivalence: supported by the pinned CTX/HiRISE definitions; coordinate round-trip error `8.42e-10 m`. Independent horizontal-control residual remains NOT MEASURED; MOLA and HiRISE reference radii differ by 190 m.
- HiRISE transfer: 959,660 bytes over 29 range requests; no raw pixels or point coordinates persisted. `tifffile` emitted a GDAL_NODATA-to-float32 warning, but the pinned nodata value was resolved from the GeoTIFF tag and the run completed.

### Spatial topology

The observed lattice contains 422 cardinal adjacency edges.

| Unsupported category | Count | 4-connected components | Largest component | Same-category edges | Fixed-count reference mean / 95th | Upper-tail fraction |
|---|---:|---:|---:|---:|---:|---:|
| HiRISE outside bounds | 90 | 6 | 59 | 113 | 28.33 / 35 | 0.0001 |
| HiRISE inside nodata | 92 | 8 | 44 | 96 | 29.59 / 37 | 0.0001 |

The upper-tail fractions are **descriptive reference summaries, not inferential p-values**. The uniform-label reference does not model deterministic raster footprint geometry, geology or nodata generation. The result supports that both unsupported categories are spatially concentrated on this one bounded lattice relative to that simple reference; it does not identify their physical cause or establish a geologic process.

### Claim boundary and next gate

E564 measures topology only. It does not establish a registration shift, vertical agreement, route safety, analogue recovery or cross-body similarity. The next action is to compare the component pattern against independent product-footprint/coverage or FOM provenance, not to repeat nearby pixel probes. If no product-specific provenance exists, preserve partial support rather than imputing missing values.
