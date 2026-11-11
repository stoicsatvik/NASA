# E540 — Grand Falls direct DEM acquisition via explicit metadata downloadUri (2026-11-11)

## Why this route is different

E538 tested the documented item-wide ZIP and `?name=` single-file route. E539 then inspected public ScienceBase item metadata and official USGS XML without following file URLs. The root item explicitly exposes file-specific `files[].downloadUri` fields on `sciencebase.usgs.gov/manager/download/{fileId}`, distinct from the previously rejected `manager/item/.../file/...` preview URLs.

## Frozen acquisition gate

- Re-fetch the public ScienceBase item metadata.
- Select exactly one file whose name is `GFDF_Ripples_2023_04_18_DEM.tif` and catalogue size is 619,492 bytes.
- Require its own `downloadUri` field to use HTTPS `sciencebase.usgs.gov/manager/download/{fileId}`, with no embedded query or userinfo.
- Follow redirects only to official ScienceBase hosts or Amazon S3.
- Enforce a 5 MB streamed cap; record final host/path and query-key names only, never signed query values.
- Require exact catalogue-size match and TIFF magic.
- Inspect GeoTIFF tags, shape, dtype, compression and nodata with tifffile. Pixel values remain unit-unassigned unless source metadata proves their vertical units.
- Keep raw data only in a seven-day Actions artifact; never commit it.

## Exact-head result

- E539.1 corrected metadata classifier: **8/8 deterministic tests passed**; the public metadata audit was rerun in the same workflow.
- E540: **7/7 deterministic tests passed**.
- Actions run [#42968010724](https://github.com/stoicsatvik/NASA/actions/runs/42968010724) used the exact metadata-backed DEM `downloadUri`, after re-fetching the root item metadata and selecting the unique file name/size pair.
- The HTTPS request returned **HTTP 200**, but the final content type was `text/html`; only **4,255 bytes** arrived, beginning `<!doctype`. The response did not match the 619,492-byte catalogue size and had no TIFF magic. No raster was saved or inspected; `raw_sample_downloaded=false`.
- This is a valid negative acquisition result. The route exposes a manager download page in the tested anonymous context, not the raster bytes.

## Claim boundary

- Grand Falls as a USGS-described Mars-analogue candidate: SUPPORTED AS PUBLISHED.
- Raw DEM acquisition: NOT SUPPORTED by the tested public routes.
- CRS, resolution, nodata and vertical units: NOT YET INSPECTED.
- Aeolian feature comparability to Mars: NOT YET PROVEN.
- E001 known-site recovery: NOT YET MEASURED.
- Cross-body similarity, novel analogue discovery and challenge-selection superiority: NOT YET PROVEN.

## Stop rule and next move

Stop further ScienceBase endpoint exploration for this item. Do not try more guessed URL patterns or the orthomosaic route. Pivot to a separate independently documented public Earth dataset with a verified direct data path, or re-evaluate the all-14 official 2026 challenge ranking. No credentials, cookies, access-control bypass, site contact or fieldwork were used.
