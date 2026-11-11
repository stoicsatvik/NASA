# E546 — bounded 2025 HiRISE archive range-access feasibility (11 November 2026)

## Question

Can the official USGS 2025 Mars Sample Return HiRISE mosaic archive be inspected through bounded HTTP Range requests, so a small GeoTIFF region can potentially be read without downloading the published 5.3 GB ZIP?

This is a data-access feasibility test, not a raster comparison or scientific analogue result.

## Pinned source and provenance

- Publisher: USGS Astrogeology Science Center.
- Product: Mars Sample Return Terrain Relative Navigation HiRISE DTM and Orthoimage Mosaics.
- DOI: https://doi.org/10.5066/P13CPYYU
- Official product record: https://astrogeology.usgs.gov/search/map/mars-sample-return-terrain-relative-navigation-hirise-dtm-mosaic
- Exact public archive: \`https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/Mars/MSR_TRN_HiRISE_soc_003_USGS_release_aug2024/MSR_TRN_HiRISE_soc_003_USGS_release_aug2024_mosaics.zip\`
- The USGS record publishes a 5.3 GB archive, 1 m/pixel mosaic, 19,144 rows × 26,816 columns, 32-bit raster, and reports eight of ten planned stereo pairs completed.
- USGS metadata says the 2025 HiRISE mosaic was aligned to a CTX reference at <6 m for the 93rd percentile and <10.2 m for the 99th percentile. These are published product-quality summaries, not a local residual measured by this experiment.

## Why this experiment comes before pixel analysis

The 2025 product is distributed as a multi-gigabyte ZIP. A full download is unnecessary and undesirable for a first access test. If the archive supports exact byte ranges and the DTM GeoTIFF is stored (ZIP method 0), its local header and TIFF directory may be readable without transferring the archive. If the member is ZIP-deflated (method 8), random access to its internal TIFF offsets is not available through ordinary ZIP member offsets; downloading and decompressing the whole member would be required. If the server ignores Range, the full archive must be refused.

## Frozen procedure

1. Validate the exact HTTPS host and path; no query strings, alternate hosts or redirects are admitted.
2. Issue HEAD and require a numeric archive Content-Length.
3. Request only the final at-most-65,557 bytes to locate EOCD / ZIP64 metadata.
4. Request only the exact central-directory byte range, capped at 8 MiB.
5. Parse member names, ZIP compression methods, sizes and local-header offsets; reject multi-disk archives, duplicate names, traversal paths and malformed ranges.
6. If exactly one DTM/DEM TIFF member is identified, request its local header and only the first four member bytes. Do not extract the raster.
7. Retain only byte-range receipts, hashes, ZIP member metadata and the four-byte TIFF signature. Never upload raw raster bytes or pixel arrays.
8. Hard cap total transfer at 8.52 MB. A server returning HTTP 200 to a Range request is treated as a negative result and the full response is not consumed.

## Competing explanations

- **H1 — stored TIFF with range support:** a small subsequent COG/GeoTIFF directory-and-tile read may be feasible.
- **H2 — ZIP-deflated TIFF:** the archive is reachable, but member-level random access is not feasible without a full member transfer.
- **H3 — range unsupported / redirect / public access failure:** this exact archive route cannot support bounded acquisition.
- **H4 — archive layout ambiguity or oversized central directory:** the source exists, but the current bounded parser cannot safely select one DTM member.

## Result

Pending exact-head GitHub Actions execution. No successful archive access, member selection, TIFF parse, raster value or co-registration is claimed until a compact receipt is inspected.

## Interpretation boundary

Even a stored TIFF and successful byte-range access would not establish:

- that the HiRISE mosaic and CTX pixels are co-registered at the selected location;
- that MOLA observed-count cells overlap the same valid raster footprint;
- a valid elevation transformation between reference surfaces;
- cross-body similarity, known-site recovery or novel analogue discovery;
- route safety or astronaut safety.

The 2025 LPSC paper identifies the reference as the Mars 2020 CTX DEM and reports that the new mosaic does not meet the <6 m alignment requirement at the 99th percentile; localized offsets can be larger. The exact CTX file identity and local residual must still be verified rather than inferred from the product title.

## Claim states

- Public HiRISE product provenance and published metadata: SUPPORTED.
- Bounded archive range access: NOT YET MEASURED.
- DTM member random access: NOT YET MEASURED.
- HiRISE raster values inspected: NOT YET MEASURED.
- CTX/HiRISE local registration: NOT YET MEASURED.
- MOLA/CTX/HiRISE common-valid-pixel support: NOT YET ESTABLISHED.
- Cross-body similarity: NOT YET PROVEN.
- Known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Challenge-selection superiority: NOT YET PROVEN.

## Next gate

- If the selected DTM member is ZIP-stored and begins with a TIFF signature, use bounded ranges to inspect TIFF IFDs, GeoTIFF CRS/transform/nodata and one internal tile only; then test a frozen local registration against the CTX TRN product.
- If the member is ZIP-deflated, do not download the 5.3 GB archive. Search only documented, legitimate per-scene or cloud-optimized products with controlled geometry; uncontrolled HiRISE RDRs are not substitutes for this controlled mosaic.
- If Range is ignored or the archive is inaccessible, preserve the route-specific negative result and pivot to another independently documented data source.
- Keep Martian Map #11 and MODIS/VIIRS #9 as a provisional tie; planetary analog #10 remains conditional on real positive/negative site evidence and E001.
