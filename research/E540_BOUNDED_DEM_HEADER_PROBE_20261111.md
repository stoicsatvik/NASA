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

## Claim boundary

A positive result establishes only that the first 32 bytes of the named public file were returned as a valid TIFF-family header. It does not parse the TIFF directory or establish CRS, vertical datum, pixel scale, nodata, elevation units, uncertainty, or comparability with Mars data. A failure does not establish that all USGS access routes are unavailable.

No full raster download, fieldwork, credential use, contact, deployment, merge or competition submission is part of this experiment.

## Result

Pending exact-head Actions execution. No scientific claim is promoted before the live receipt is inspected.
