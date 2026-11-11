# E540 — bounded ScienceBase DEM range probe (2026-11-11)

## Question

Does the exact public ScienceBase file record for `GFDF_Ripples_2023_04_18_DEM.tif` expose an uncredentialed, allowlisted `downloadUri` that honors a 32-byte HTTP Range request?

## Frozen scope

- ScienceBase item: `662bccfad34ea70bd5f11f88`.
- Exact filename: `GFDF_Ripples_2023_04_18_DEM.tif`.
- Catalogue size: 619,492 bytes.
- Inspect only the exact file record's `downloadUri`; do not substitute manager-preview links, the item-wide ZIP route, guessed endpoint variants, or other file URLs.
- Reject signed/tokenized query keys before making a request. No cookies, credentials, authorization headers, or access-control bypass.
- Allow HTTPS ScienceBase catalog file hosts and official S3 host patterns only. Validate every redirect before following it.
- Send exactly `Range: bytes=0-31`; read at most 33 bytes to detect an over-read.
- Require HTTP 206, `Content-Range: bytes 0-31/619492`, exactly 32 bytes, and valid TIFF byte-order magic.
- Store only sanitized URL host/path/query-key names, HTTP metadata, a prefix SHA-256, and a TIFF-magic boolean. Never store query values or response bytes.
- Do not download the complete raster or inspect GeoTIFF tags.

## Why this is the next gate

E538's documented `?name=` single-file endpoint returned HTTP 404. E539 inspected the pinned public item and official USGS XML metadata without following file URLs. It found six file records and 45 URL-like metadata fields, but did not prove anonymous file access. The previous `anonymous_direct_candidates` label was too strong; E539 now reports only `unverified_direct_url_candidates`.

## Result

Pending exact-head GitHub Actions. A metadata-provided signed URL is not an anonymous URL and must not be requested. HTTP 403/404, ignored Range, non-TIFF prefix, incorrect Content-Range, or redirects outside the allowlist are preserved as negative outcomes.

## Claim boundary

A valid 32-byte TIFF prefix would establish only that the first byte range is accessible without credentials. It would not establish full DEM acquisition, file integrity, CRS, pixel resolution, nodata, vertical datum, physical calibration, or planetary-analogue recovery. E001 remains NOT READY until independent controls and a defensible feature/validation protocol exist.
