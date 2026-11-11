# E540: bounded anonymous DEM header probe

Date: 2026-11-11  
Source item: USGS ScienceBase 662bccfad34ea70bd5f11f88  
Target file: GFDF_Ripples_2023_04_18_DEM.tif  
Upstream evidence: E539 / NASA PR #98

## Question

Does the exact DEM file record expose an anonymous, metadata-provided downloadUri that returns a valid TIFF header under a strict 32-byte HTTP range request?

## Frozen protocol

1. Fetch only the pinned public ScienceBase item JSON.
2. Require exactly one file record whose name exactly matches the target DEM.
3. Require its own downloadUri; do not construct a URL from an item ID or filename.
4. Reject source URLs with credentials, fragments, non-HTTPS schemes, token-like query keys, or hosts/paths outside the pinned ScienceBase download routes.
5. Send no Authorization header or cookies. Request only Range: bytes=0-31.
6. Follow redirects only to the pinned ScienceBase hosts or the exact USGS ScienceBase S3 host observed in E539. Signed redirect query values are never stored.
7. Read at most 33 bytes to detect a server that ignores the range. Store no raster bytes, raw URL, or query values; retain only status, sanitized host/path/query-key names, response metadata, TIFF magic and a SHA-256 of the bounded header.
8. Preserve 403/404, malformed range, wrong magic, size mismatch, range-ignored and redirect-rejected outcomes.

## Exact-head validation and result

PR #99 exact-head Actions run [42974298041](https://github.com/stoicsatvik/NASA/actions/runs/42974298041) succeeded on commit 7167417e19049d9e182a31cbc173235a66bfc925. The push-triggered run [42974268490](https://github.com/stoicsatvik/NASA/actions/runs/42974268490) also succeeded.

- Deterministic tests: **8/8 passed**.
- Pinned ScienceBase item metadata: HTTP 200.
- Exactly one file record matched GFDF_Ripples_2023_04_18_DEM.tif.
- Anonymous request: HTTP 206, exactly 32 bytes returned for Range bytes=0-31.
- Content-Range: bytes 0-31/4255; Content-Length: 32.
- Content-Type: text/html; charset=UTF-8.
- ScienceBase metadata file size: 619,492 bytes. The response's range total is 4,255 bytes, a 615,237-byte discrepancy (metadata size is about 145.6× larger).
- TIFF magic: absent. Bounded-header SHA-256: da601195ac485b469d11020bd536befb96529d3a1f367ed9e97db3d7095afc6b.
- Decision: **NON_TIFF_HEADER**. The tested manager/download route returned a partial HTML response, not a TIFF header.

## Interpretation and claim boundary

This falsifies the tested metadata-provided manager/download route as a raw DEM byte endpoint in this public context. It does **not** prove that every ScienceBase route or every USGS dataset is inaccessible. No DEM bytes, CRS, resolution, nodata, vertical datum, elevation units, physical feature, or analogue recovery are established.

No full raster download, fieldwork, credential use, contact, deployment, merge or competition submission occurred. No raster bytes, raw URL or query values were stored.

## Next gate

Stop repeating URL guesses for this item. Prioritize a separately documented public raw-data path (or an independent MOLA/LOLA/Diviner/Earthdata product) with explicit format and metadata. E001 remains NOT YET MEASURED / NOT READY until real comparable descriptors, known-site labels and defensible controls exist.
