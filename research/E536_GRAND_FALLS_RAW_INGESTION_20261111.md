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

## Initial live result — negative acquisition preserved

Exact-head run [#42954866734](https://github.com/stoicsatvik/NASA/actions/runs/42954866734) passed its original five parser tests and completed the ScienceBase metadata request, but it did **not** acquire a valid raster:

- The item API returned HTTP 200 and listed six direct files.
- The smallest TIFF catalogue entry was the 619,492-byte DEM `GFDF_Ripples_2023_04_18_DEM.tif`.
- Its catalogue URL used the ScienceBase `/manager/item/.../file/...` preview route. The request returned 4,255 bytes beginning with `<!do`, i.e. HTML, not TIFF.
- `tifffile` correctly raised `TiffFileError: not a TIFF file`. The initial script nevertheless set `raw_sample_downloaded=true` merely because bytes were written with a `.tif` filename. That status bug is corrected below; the initial result remains preserved as a failed acquisition.

## E536.1 corrective implementation

- Treat `/manager/item/.../file/...` as a preview route, not a direct binary download URL.
- Restrict binary downloads to HTTPS ScienceBase catalog file endpoints and reject unexpected redirects, content types, and file signatures.
- Cap ScienceBase JSON metadata responses at 5 MiB.
- If no direct TIFF URL is available, use the official item-files ZIP endpoint `/catalog/file/get/{itemId}` only when every catalogue file size is known and their sum is within the 50,000,000-byte cap. The DOI-USGS `sciencebasepy` implementation uses this same endpoint for `get_item_files_zip`: https://github.com/DOI-USGS/sciencebasepy/blob/master/sciencebasepy/SbSession.py#L3643-L3690.
- The current item catalogue sizes sum to 48,431,208 bytes. Extract only the smallest TIFF member, enforce the same 50 MB cap, and verify TIFF magic before inspection.
- Set `raw_sample_downloaded=true` only when `tifffile` successfully opens and inspects the extracted TIFF; an HTML preview can no longer be reported as a raster.

Five new fixture tests cover manager-preview rejection, file signatures, the archive-size gate, smallest-TIFF extraction, and HTML disguised as TIFF. The first run of the new ten-test suite caught a 2,000-byte arithmetic error in the fixture's catalogue-size sum (expected 48,429,208; actual 48,431,208); that test expectation was corrected. Current-head live validation is pending.

## Claim boundary

- Grand Falls as a USGS-described Mars-analogue candidate: **SUPPORTED AS PUBLISHED**.
- Initial raw DEM acquisition: **FAILED** because the selected manager URL returned HTML; corrected item-archive fallback: **PENDING exact-head validation**.
- CRS, resolution, nodata and vertical units: **NOT YET INSPECTED**.
- Aeolian feature comparability to Mars: **NOT YET PROVEN**.
- E001 known-site recovery: **NOT YET MEASURED**.
- Cross-body similarity, novel analogue discovery and challenge-selection superiority: **NOT YET PROVEN**.

## Next gate

If a raw raster is acquired, inspect the exact GeoTIFF metadata and units before deriving any morphology descriptor. If the bounded API path fails, preserve the HTTP error and use the official ScienceBase item/child/file APIs as the next access route; do not substitute catalogue prose for measured data.
