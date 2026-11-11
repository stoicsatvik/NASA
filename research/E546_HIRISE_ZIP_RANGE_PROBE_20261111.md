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

Exact-head GitHub Actions run [#43018937442](https://github.com/stoicsatvik/NASA/actions/runs/43018937442) succeeded on commit `deb4c02f26146466aab06e78e0a2cfc0942763ab`: **12/12 deterministic tests passed** and the bounded live probe completed.

- HEAD: HTTP 200; `Accept-Ranges: bytes`; archive size **5,468,062,403 bytes**; ZIP64; 17 members.
- Exact central directory: 3,215 bytes. One DTM TIFF candidate was identified.
- DTM member: ZIP method **8 (DEFLATE)**; compressed **675,625,590 bytes**, uncompressed **711,891,990 bytes**.
- The DTM local header was verified and only four bytes at the compressed member offset were read. They are not TIFF magic because the member is deflated.
- Orthomosaic member is also DEFLATE: 4,631,266,296 compressed bytes / 4,674,976,833 uncompressed bytes.
- Total transfer: **68,993 bytes**, below the 8.52 MB cap. Receipt artifact: [13854770384](https://github.com/stoicsatvik/NASA/actions/runs/43018937442/artifacts/13854770384), SHA-256 `82eb60c3c2871d076bace47fde5db08fe31022623d3de700335d504d513a6efe`.
- Outcome: **ZIP_DEFLATED_MEMBER_NOT_RANDOM_ACCESSIBLE**. The archive supports bounded Range access, but its DTM and orthomosaic members do not permit ordinary random access to internal TIFF tiles through ZIP member offsets. No raster pixel or value was acquired.

### Preserved implementation/test failures

- First run [#43018471829](https://github.com/stoicsatvik/NASA/actions/runs/43018471829): 11/11 fixtures passed; live probe reached ZIP64 central-directory parsing, then failed on nested ZIP64 receipt accounting before producing a receipt. This was a runner bug, not a source-access failure.
- Intermediate run [#43018803181](https://github.com/stoicsatvik/NASA/actions/runs/43018803181): one ZIP64 fixture failed because the test encoded the signature as escaped text rather than binary bytes. The fixture was corrected; the final exact-head run passed 12/12.

### Updated interpretation

- Public archive provenance and bounded HTTP Range access: **SUPPORTED**.
- DTM/orthomosaic random access through this ZIP layout: **NOT SUPPORTED** without downloading/decompressing the corresponding large member.
- Full 5.3 GB archive download: **REJECTED** as the next experiment; no download was attempted.
- Raster values and CTX/HiRISE registration: **NOT YET MEASURED**.
- Cross-body similarity: **NOT YET PROVEN**; known-site recovery **NOT YET MEASURED**; novel analogue discovery **NOT YET PROVEN**; challenge-selection superiority **NOT YET PROVEN**.

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
- Bounded archive range access: SUPPORTED.
- DTM member random access through this ZIP layout: NOT SUPPORTED (DEFLATE).
- HiRISE raster values inspected: NOT YET MEASURED.
- CTX/HiRISE local registration: NOT YET MEASURED.
- MOLA/CTX/HiRISE common-valid-pixel support: NOT YET ESTABLISHED.
- Cross-body similarity: NOT YET PROVEN.
- Known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Challenge-selection superiority: NOT YET PROVEN.

## Next gate

- The DTM and orthomosaic members are ZIP-deflated. Do not download the 5.3 GB archive or the 676 MB compressed DTM member merely to obtain a small window.
- Search for a separately published, directly addressable controlled HiRISE GeoTIFF/COG covering the CTX overlap. The USGS uncontrolled HiRISE RDR collection is explicitly not co-registered with controlled products and is not an admissible substitute.
- If no controlled range-addressable product exists, preserve the source limitation and pivot to another independently documented planetary/Earth dataset.
- Keep Martian Map #11 and MODIS/VIIRS #9 as a provisional tie; planetary analog #10 remains conditional on real positive/negative site evidence and E001.
