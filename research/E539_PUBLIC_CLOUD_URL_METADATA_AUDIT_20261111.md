# E539 — public ScienceBase/USGS metadata URL audit (2026-11-11)

## Question

Does the public ScienceBase item or its official USGS XML metadata explicitly expose an anonymous direct cloud/download URL for the Grand Falls 2023 DEM, beyond the already-tested manager-preview and item-wide ZIP routes?

## Frozen scope

- ScienceBase item: `662bccfad34ea70bd5f11f88`.
- Inspect the root item and its immediate public child items, plus the official USGS XML metadata URL.
- Recursively enumerate URL-like metadata fields only.
- Record host, path, query-key names and source field; never store query values, signed tokens or raw metadata.
- Classify manager-preview routes, official catalog file routes, signed/tokenized URLs and other HTTPS candidates separately.
- Do not follow any file URL, download any binary, or infer anonymous access from a metadata field.

## Validation

Six deterministic tests cover manager-preview rejection, catalog-file candidate classification, signed URL rejection, query-value redaction, recursive URL-field discovery and HTTP rejection. Exact-head live metadata audit is pending.

## Claim boundary

A URL found in metadata is only a candidate until anonymous access is independently verified. No raw DEM, CRS, resolution, nodata, vertical datum, physical feature or analogue recovery is claimed.

## Stop rule

If the public metadata contains no explicit direct anonymous candidate, preserve that result and stop trying alternate ScienceBase endpoint patterns for this item. Continue the NASA stream with independent Earth/Mars sources and the all-14 challenge comparison instead.
