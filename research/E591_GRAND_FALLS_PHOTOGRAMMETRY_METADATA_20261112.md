# E591 — Grand Falls photogrammetry child-item metadata inventory

Date: 12 November 2026  
Branch: `research/e591-grand-falls-photogrammetry-metadata-20261112`  
Draft PR stacked on E590 / PR #154. Main untouched.

## Question

Does the distinct USGS Grand Falls ripple-photogrammetry child item expose a metadata-listed DEM, orthomosaic or archive that could support a real Earth-side morphology sample?

## Frozen scope

- One anonymous HTTPS GET to the exact child item ID discovered in E590's official parent-child inventory: `67b78df2d34e1a2e835b13b7`.
- Maximum metadata response: 5 MB; timeout and redirect allowlist inherited from E590.
- Record only metadata hash, item title, file names, extensions, sizes, host/query-key summaries and whether a spatial extent field exists.
- No file downloads, signed query values, raw coordinates, images, DEMs, credentials, contact or field access.
- A listed raster is not treated as validated: CRS, vertical datum, grid spacing, nodata, georegistration and spatial support remain separate gates.

## Validation

Five deterministic tests cover raster/archive classification, signed-query redaction, HTTP failure, empty inventories and invalid JSON. Exact-head CI and the one bounded metadata request are pending.

## Claim boundary

A metadata-listed DEM/orthomosaic would establish only a public file-access path. It would not establish correct CRS, physical support, calibrated morphology, Mars comparability, known-site recovery or challenge superiority.

## Next gate

If a raster is listed, obtain its authoritative metadata and source checksum before any bounded sample. Do not download a large raster or infer physical comparability from filename/extension alone.
