# E536 — Grand Falls raw-raster ingestion probe (2026-11-11)

## Question

Can the official USGS/ScienceBase release for the December 2022–April 2023 Grand Falls photogrammetry component yield one directly downloadable, inspectable raw DEM within a strict size and time budget?

## Pinned source

- USGS Science Data Catalog item: `USGS:662bccfad34ea70bd5f11f88`
- ScienceBase item ID: `662bccfad34ea70bd5f11f88`
- Parent data-release DOI: `10.5066/P9FRH62D`
- Catalog describes raw imagery, DEMs and an orthomosaic; the release covers 2022-12-06 through 2023-04-18.
- The USGS page states the data are public and CC0 1.0. Public data access is not permission for field access.

## Frozen acquisition limits

- Anonymous GET only; no account credentials or contact.
- Follow the parent item and at most two child levels, with a maximum of 50 visited items.
- Inventory attached files and preserve item IDs, file names, catalogue sizes and direct URLs.
- Download only the smallest directly listed GeoTIFF or ZIP whose catalogue size is at most 50,000,000 bytes. Enforce the same cap while streaming.
- If a ZIP is selected, extract only the smallest contained TIFF under the same cap.
- Record SHA-256 for downloaded files. Inspect TIFF shape, dtype, compression, GeoTIFF tags and nodata where possible. Pixel statistics remain unit-unassigned until vertical units and CRS are verified.
- Store the receipt and any sample only as a seven-day Actions artifact. Do not commit raw raster data.

## Validation

Five deterministic parser/normalization tests are included. The live ScienceBase result, download outcome, byte count, hashes and raster metadata are **PENDING exact-head Actions**. This report intentionally makes no successful-ingestion claim before the workflow receipt exists.

## Claim boundary

- Grand Falls as a USGS-described Mars-analogue candidate: **SUPPORTED AS PUBLISHED**.
- Raw DEM ingestion: **NOT YET MEASURED**.
- CRS, resolution, nodata and vertical units: **NOT YET INSPECTED**.
- Aeolian feature comparability to Mars: **NOT YET PROVEN**.
- E001 known-site recovery: **NOT YET MEASURED**.
- Cross-body similarity, novel analogue discovery and challenge-selection superiority: **NOT YET PROVEN**.

## Next gate

If a raw raster is acquired, inspect the exact GeoTIFF metadata and units before deriving any morphology descriptor. If the bounded API path fails, preserve the HTTP error and use the official ScienceBase item/child/file APIs as the next access route; do not substitute catalogue prose for measured data.
