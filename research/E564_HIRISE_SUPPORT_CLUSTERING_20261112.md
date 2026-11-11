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
