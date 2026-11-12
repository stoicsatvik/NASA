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

Five deterministic tests cover raster/archive classification, signed-query redaction, HTTP failure, empty inventories and invalid JSON. Exact-head workflow #43254742040 passed 5/5 tests and the one bounded metadata request.

## Claim boundary

A metadata-listed DEM/orthomosaic would establish only a public file-access path. It would not establish correct CRS, physical support, calibrated morphology, Mars comparability, known-site recovery or challenge superiority.

## Next gate

If a raster is listed, obtain its authoritative metadata and source checksum before any bounded sample. Do not download a large raster or infer physical comparability from filename/extension alone.


## E591 exact-head result — 12 November 2026

- Exact PR head `b853ce5f0d59ec71d18cfd11c4b21c84d44ceb96`; workflow [#43254742040](https://github.com/stoicsatvik/NASA/actions/runs/43254742040) succeeded: **5/5 deterministic tests** and one bounded metadata GET. Artifact [#13960847379](https://github.com/stoicsatvik/NASA/actions/runs/43254742040/artifacts/13960847379), ZIP SHA-256 `654f29850cdd12e484c73ca501dc262968455787ff81ee13dcb00c4a1eb16085`.
- The exact child item returned HTTP 200 / 7,491 bytes; metadata SHA-256 `f466468ba4b700ecb2a613727483100a9f62f14e8d26dfc8ba840b0122049424`.
- Inventory: **8 files**, comprising **7 ZIP archives** totaling **1,561,281,654 bytes** and one 12,658-byte XML metadata file. No standalone TIFF/IMG/JP2/VRT/DEM file was listed. A spatial extent field is present, but coordinates were not stored.
- The seven archive names are dated 20 Feb, 12 Mar, 16 Apr, 30 Apr, 16 May, 20 Jun and 25 Jul 2024. Their contents are NOT YET INSPECTED. A filename or ZIP archive does not establish that a DEM/orthomosaic is inside.
- No archive, image, DEM or raw coordinate was downloaded. This is metadata inventory only.

### Claim update

- Public photogrammetry child-item metadata access: **SUPPORTED**.
- Archive inventory and sizes: **MEASURED**.
- DEM/orthomosaic presence inside archives, CRS, vertical datum, grid spacing, nodata, georegistration and spatial support: **NOT YET ESTABLISHED**.
- Earth-side morphology descriptor extraction, Mars/Earth comparability, E001 known-site recovery, novel analogue discovery and challenge-selection superiority: unchanged; **NOT YET PROVEN / NOT YET MEASURED**.

### Next gate

Retrieve and parse only the 12,658-byte XML metadata file under the same host/size/redirect constraints. Extract source-described product types, CRS, vertical datum, grid spacing, nodata, acquisition dates and processing lineage if present. Do not download the 1.56 GB archive set until metadata shows a defensible small-sample path and a specific validation question.
