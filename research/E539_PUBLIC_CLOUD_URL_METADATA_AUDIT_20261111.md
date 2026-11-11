# E539 — public ScienceBase/USGS URL metadata audit (2026-11-11)

## Question

Does the public ScienceBase item or its official USGS XML metadata explicitly expose a file-specific download URI for the Grand Falls 2023 DEM, beyond the already-tested manager-preview and item-wide ZIP routes?

## Frozen scope

- ScienceBase item: `662bccfad34ea70bd5f11f88`.
- Inspect the root item and official USGS XML metadata; the immediate child listing returned no child records in this run.
- Recursively enumerate URL-like metadata fields only.
- Record host, path, query-key names and source field; never store query values, signed tokens or raw metadata.
- Count a candidate only when the source is a file-specific `files[].downloadUri` or `downloadURL` field and the URL is an HTTPS file route. Generic DOI, item, metadata and preview links are not download candidates.
- Do not follow any file URL, download any binary, or infer anonymous access from a metadata field.

## Exact-head result

- Actions run [#42967733262](https://github.com/stoicsatvik/NASA/actions/runs/42967733262): initial six-fixture suite passed and the live metadata requests returned HTTP 200.
- One root item with six file entries was inspected. The official USGS XML metadata returned HTTP 200, 21,529 bytes, SHA-256 `09b9b4cc869f6455a9e80e2741b62723d8cdce8602487a101dbc6cee4a13c95e`.
- The initial broad URL inventory contained 45 URL-like fields, but its 43-candidate counter incorrectly included DOI, metadata, item and generic HTTPS links. It is not a count of file downloads.
- The source fields include six file-specific `downloadUri` entries: four catalog file routes and two `sciencebase.usgs.gov/manager/download/{fileId}` routes. The latter correspond to the DEM/orthomosaic records; query values and raw metadata were not stored.
- E539 did not follow any file URL. The manager/download route was only a metadata-declared candidate, not a verified anonymous data transfer.

## E539.1 classification correction

The first result exposed an overly broad candidate classifier. The code now distinguishes:
- manager download routes from manager preview/UI routes;
- file-specific download URI fields from generic item/DOI/metadata links;
- tokenized URLs from unsigned metadata candidates.

Eight deterministic tests now cover these boundaries. The E540 workflow reruns the corrected metadata audit before its bounded DEM attempt.

## Claim boundary

A URL found in metadata is only a candidate until anonymous binary access is independently verified. No raw DEM, CRS, resolution, nodata, vertical datum, physical feature or analogue recovery is claimed.

## Stop rule

E540 tests the exact DEM `downloadUri` and returns HTML rather than TIFF. Stop further endpoint exploration for this item and pivot to another independent public Earth dataset or a different official 2026 challenge.
