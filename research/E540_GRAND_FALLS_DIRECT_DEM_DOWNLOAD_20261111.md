# E540 — Grand Falls direct DEM acquisition via explicit metadata downloadUri (2026-11-11)

## Why this route is different

E538 tested the documented item-wide ZIP and `?name=` single-file route. Both failed to yield a valid TIFF. E539 then inspected public ScienceBase item metadata and official USGS XML without following file URLs. It found explicit `files[].downloadUri` fields on `sciencebase.usgs.gov/manager/download/{fileId}`, distinct from the previously rejected `manager/item/.../file/...` preview URLs.

## Frozen acquisition gate

- Re-fetch the public ScienceBase item metadata.
- Select exactly one file whose name is `GFDF_Ripples_2023_04_18_DEM.tif` and catalogue size is 619,492 bytes.
- Require its own `downloadUri` field to use HTTPS `sciencebase.usgs.gov/manager/download/{fileId}`, with no embedded query or userinfo.
- Follow redirects only to official ScienceBase hosts or Amazon S3.
- Enforce a 5 MB streamed cap; record final host/path and query-key names only, never signed query values.
- Require exact catalogue-size match and TIFF magic.
- Inspect GeoTIFF tags, shape, dtype, compression and nodata with tifffile. Pixel values remain unit-unassigned unless source metadata proves their vertical units.
- Keep raw data only in a seven-day Actions artifact; never commit it.

## Deterministic tests

Seven tests cover exact metadata selection, preview rejection, query/userinfo rejection, duplicate/mismatched file metadata, redirect allowlist and query-value redaction. Exact-head live acquisition is pending.

## Claim boundary

A size-matched TIFF that tifffile can open establishes raw acquisition and file-level metadata only. It does not establish physical comparability to Mars, known-analogue recovery, a valid feature representation or novel discovery.

## Next gate

If acquired, verify CRS, horizontal resolution, vertical units/datum and nodata semantics from GeoTIFF tags plus the USGS source metadata. Only then derive a physically comparable Earth descriptor and choose a defensible non-analogue control. If this exact metadata URI fails, stop this item's endpoint exploration and pivot to another independent public Earth dataset.
