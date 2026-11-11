# E566 — 2025 HiRISE DTM/confidence archive range audit (12 November 2026)

## Question

Does the 2025 USGS Mars Sample Return HiRISE mosaic provide a second, quality-annotated source over the Jezero region where the 2020 HiRISE DTM had in-bounds nodata, and can the archive be inspected without downloading its 5.3 GB payload?

This is a coverage/quality-source gate for the Martian Map alternative. The 2025 product is aligned to the CTX reference; it is **not** an independent horizontal control network.

## Pinned source

- Publisher: USGS Astrogeology Science Center
- Product: Mars Sample Return Terrain Relative Navigation HiRISE DTM and Orthoimage Mosaics
- DOI: https://doi.org/10.5066/P13CPYYU
- Official metadata: https://astrogeology.usgs.gov/search/map/mars-sample-return-terrain-relative-navigation-hirise-dtm-mosaic
- Exact archive URL: https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/Mars/MSR_TRN_HiRISE_soc_003_USGS_release_aug2024/MSR_TRN_HiRISE_soc_003_USGS_release_aug2024_mosaics.zip
- Published archive size: 5.3 GB
- Published nominal resolution: 1 m/pixel
- Published bounds: 77.057–77.380°E, 18.135–18.588°N
- Published contents: DTM, orthoimage and confidence mosaics
- Published processing: 8 of 10 stereo pairs completed; mosaic aligned to CTX reference to <6 m at the 93rd percentile and <10.2 m at the 99th percentile; a crater-rim vertical-offset exception is documented.

## Frozen bounded protocol

1. Send HEAD to the exact USGS-published S3 object URL with redirects disabled.
2. Require a positive Content-Length.
3. Use a seekable HTTP-range adapter. Every GET must return HTTP 206 and an exact matching Content-Range.
4. Let Python's ZIP reader inspect only the central directory and local member headers.
5. Read at most 16 bytes from each of at most 24 TIFF member prefixes.
6. Cap cumulative range transfer at 32 MiB and any single range at 16 MiB.
7. Retain only archive metadata, member names/roles, compression metadata, TIFF magic checks and byte-range receipts. Never retain raster pixels or full member contents.
8. Preserve redirects, ignored ranges, malformed ZIPs and missing confidence members as negative outcomes. Never silently follow an alternate host or download the full archive.

## Interpretation rules

- A DTM member plus a confidence member supports **archive-level source availability only**.
- A valid TIFF prefix does not prove readable georeferencing, confidence semantics, spatial coverage, or valid pixels at any MOLA point.
- A ZIP-stored TIFF may be amenable to later byte-range TIFF parsing; a deflated ZIP member requires member decompression and may defeat bounded random access.
- The 2025 mosaic's alignment to CTX means it cannot independently validate CTX horizontal control. Its confidence layer must not be called calibrated uncertainty until its metadata and semantics are inspected.
- No route-safety, cross-body similarity, known-site recovery, novel analogue discovery or local validation advantage is claimed.

## Validation

Exact-head GitHub Actions run #43113419588 succeeded: **6/6 deterministic tests passed**. The live run used no credentials and emitted receipt artifact #13897481736 (1,818 bytes; SHA-256 e236f52e23ab60dd32a0a12accd8d3b9af24ad20260366db68bf68e184e87944).

## Exact-head result

- Branch head: `1762cd613440aafac6fa19c137471607f6fa03df`.
- Actions run [#43113419588](https://github.com/stoicsatvik/NASA/actions/runs/43113419588): **6/6 tests passed**; live archive audit completed.
- The exact official S3 object returned `Accept-Ranges: bytes`, HTTP-range access worked without credentials, and the object size was **5,468,062,403 bytes** (ETag `c6a0cc297fd60568c81e77071745ff2b-1043`).
- The ZIP central directory contained **17 members**, including one DTM TIFF, two confidence TIFFs and one orthoimage TIFF. All four TIFF prefixes passed the TIFF-magic check.
- DTM member: `MSR_hirise_soc_003_DTM_MOLATopography_DeltaGeoid_1m_Eqc_latTs0_lon0_Blend40.tif`, 675,625,590 compressed / 711,891,990 uncompressed bytes.
- Confidence members: `MSR_hirise_soc_003_FOM_ColorConfidence_1m_Eqc_latTs0_lon0.tif` (95,525,154 compressed / 1,540,258,047 uncompressed bytes) and `MSR_hirise_soc_003_FOM_Confidence_1m_Eqc_latTs0_lon0.tif` (65,308,185 compressed / 66,059,236 uncompressed bytes).
- All three scientific raster members use ZIP deflate (method 8). Therefore the TIFF members are **not directly random-accessible inside the ZIP**; a selected member must be decompressed before internal TIFF windows can be read.
- The audit made **17 HTTP range requests and transferred 20,311 bytes**, far below the 32 MiB cap. No raster pixel values or full member contents were read or retained.
- Outcome: `ARCHIVE_INDEXED_WITH_DTM_AND_CONFIDENCE`. Archive-level DTM/confidence presence and public range access are SUPPORTED. Actual raster georeferencing, confidence semantics, valid-pixel coverage and replacement of the 2020 HiRISE nodata are NOT YET MEASURED.

## Claim states

- 2025 archive range access: SUPPORTED without credentials for the pinned public S3 object.
- 2025 DTM member presence: SUPPORTED at archive level.
- Confidence member presence: SUPPORTED at archive level (two TIFF members).
- 2025 member random access: NOT SUPPORTED directly inside the ZIP; ZIP deflate requires full member decompression.
- Replacement of 2020 HiRISE nodata: NOT YET MEASURED.
- Independent horizontal registration: NOT YET MEASURED.
- Cross-body similarity: NOT YET PROVEN.
- E001 known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Route safety: NOT CLAIMED.

## Next gate

The archive index is range-addressable, but its members are deflated. The lowest-cost next gate is to decompress only the 65.3 MB FOM_Confidence member (not the 675.6 MB DTM), inspect its GeoTIFF metadata and semantics, then sample the frozen 346 observed-MOLA point centers. If confidence coverage is meaningful, decide whether the DTM's 675.6 MB member is worth a bounded full-member decompression. Do not call the 2025 mosaic an independent registration validation.
