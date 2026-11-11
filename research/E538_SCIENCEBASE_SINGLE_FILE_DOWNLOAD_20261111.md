# E538 — ScienceBase single-file DEM endpoint probe (2026-11-11)

## Question

Can the documented ScienceBase single-file download route retrieve the Grand Falls DEM even though the item-wide ZIP endpoint returned a valid ZIP containing zero-byte TIFF placeholders?

## Prior evidence

- E536 metadata probe: all five pinned item/child metadata requests returned HTTP 200. The 2022–2023 photogrammetry item exposes six files; the DEM catalogue size is 619,492 bytes.
- E536 raw-ingestion run #42959249524: 11 tests passed; the item ZIP was 1,002,830 bytes, but both DEM and orthomosaic ZIP members were zero bytes. No raw raster was acquired.
- Independent E537 run #42958393094 reproduced the zero-byte DEM member and catalogue-size mismatch.
- The individual TIFF metadata URLs resolve to ScienceBase manager preview routes, not the direct catalog file endpoint.

## Method

- Use the pinned item ID 662bccfad34ea70bd5f11f88.
- Request the exact DEM name using the ScienceBase catalog file endpoint with the name query parameter.
- Anonymous HTTPS only; no cookies, credentials, API tokens, or access-control bypass.
- Enforce the ScienceBase request host/path allowlist and an HTTPS final-host allowlist for ScienceBase/S3.
- Maximum response size: 5,000,000 bytes.
- Require TIFF magic or a ZIP containing exactly one non-empty exact-name DEM member.
- Compare the extracted DEM size with the 619,492-byte catalogue size.
- If a size-matched TIFF is acquired, inspect GeoTIFF tags with tifffile; do not assign vertical units or infer physical comparability.
- Store raw response, any extracted DEM, and the receipt only in a seven-day Actions artifact. No raw data is committed.

The single-file endpoint pattern is documented in the USGS-related science-base-automation repository:
https://github.com/esturdivant-usgs/science-base-automation

This probe tests that documented route against this specific item; it does not assume the route will succeed.

## Result

PENDING exact-head Actions. A successful metadata response alone will not count as raw-data acquisition. The result must include a size-matched TIFF with valid magic and readable TIFF structure.

## Claim boundary

A valid Earth photogrammetry DEM may be inspected. This does not establish Mars/Earth physical comparability, analogue recovery, negative controls, or novel analogue discovery. The Grand Falls data are a candidate Earth aeolian-process source only.
