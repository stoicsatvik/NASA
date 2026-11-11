# E567 — 2025 HiRISE FOM confidence support at frozen MOLA points (12 November 2026)

## Question

Does the 2025 USGS Mars Sample Return HiRISE FOM_Confidence raster contain readable, georeferenced samples at the same 346 MOLA observed-shot point centers used by E563, especially where the 2020 HiRISE raster had partial support?

## Pinned inputs

- 2025 USGS product: Mars Sample Return Terrain Relative Navigation HiRISE DTM and Orthoimage Mosaics, DOI 10.5066/P13CPYYU.
- Exact ZIP member: MSR_hirise_soc_003_FOM_Confidence_1m_Eqc_latTs0_lon0.tif.
- Expected member size from E566: 65,308,185 compressed / 66,059,236 uncompressed bytes.
- MOLA counts source: PDS Geosciences Node MEGC44N000HB.IMG; the frozen 33×33 Jezero window centered at 18.3995°N, 77.27025°E.
- Denominator: only bins with MOLA shot count >0, frozen at the E563 result (346 observed bins).

## Bounded protocol

1. Reuse the exact E566 public S3 archive URL and a cached HTTP-range reader.
2. Decompress only the 65.3 MB FOM_Confidence member; never read the 675.6 MB DTM or 4.6 GB orthoimage.
3. Verify exact member name, compressed size, uncompressed size and ZIP method.
4. Open the member in-memory as GeoTIFF; record driver, dimensions, dtype, CRS, transform, bounds, nodata, units, tags and block layout.
5. Transform the frozen MOLA point centers to the raster CRS using the published MOLA coordinate reference and the raster's own CRS. Do not fit a datum shift.
6. Sample only the 346 observed MOLA point centers. Preserve separate denominators for observed points, points inside raster bounds, and valid unmasked confidence samples.
7. Retain only aggregate counts/statistics and metadata. Do not retain raster pixels or point coordinates.

## Interpretation boundary

- The product page confirms that DTM, orthoimage and confidence mosaics are included.
- USGS HiRISE DTM documentation describes FOM values as pixel-level provenance codes for correlation success, errors and editing; confidence maps group FOM categories. This is contextual documentation, not proof that every code in this 2025 member has the same legend.
- Raw FOM_Confidence values are not treated as calibrated uncertainty or a route-risk score.
- A valid confidence sample does not by itself prove that the DTM elevation is valid at the same point.
- The 2025 mosaic is aligned to the CTX reference, so it is not an independent horizontal control network.
- No cross-body similarity, E001 recovery, novel analogue discovery or route-safety claim is made.

## Exact-head result

- Final branch head: `630f1eabd8016734ce1ff07733ee89bb8f9add5e`; exact-head Actions [#43117959720](https://github.com/stoicsatvik/NASA/actions/runs/43117959720) **SUCCESS**, 11 tests passed, live bounded acquisition completed, artifact [#13899432519](https://github.com/stoicsatvik/NASA/actions/runs/43117959720/artifacts/13899432519). The earlier code head `0af3793` also passed run #43115750730; the current head adds documentation-only validation reconciliation.
- The pinned 65,308,185-byte compressed member decompressed to 66,059,236 bytes; SHA-256 `986bbaaa60f452cfeee563ae474e06d83195cf749ff515d6a129f57d1a355d49`.
- GeoTIFF: 19,144 × 26,816, one `uint8` band, nodata 0, 1 m resolution, Mars 2015 equirectangular (radius 3,396,190 m; WKT SHA-256 `77a22ad08d07643ce7c653c5f6cab362edd6bedb262a7b47b7bd5a12f28812d3`).
- At 346 frozen observed MOLA point centers, 329 were inside and 259 had valid unmasked FOM samples: 74.9% of observed points and 78.7% of in-bounds points. Seventy in-bounds points were masked and 17 were outside. Raw codes 3–15, median 14, mean 13.2008; codes remain uninterpreted.
- Range transfer: 66,063,763 bytes in 67 requests under the 100 MiB cap. No DTM pixels were read.
- Two earlier runs failed only because the synthetic nodata fixture did not place nodata at the exact sampled pixel (`assert 4 == 3`). The fixture was corrected; final exact-head validation passed 11/11. The production sampler was not weakened.

## Claim states

- Public 2025 archive range access: SUPPORTED (E566).
- FOM_Confidence member presence: SUPPORTED at archive level (E566).
- Confidence GeoTIFF readability/georeferencing: SUPPORTED for the pinned member.
- Confidence value semantics for this specific product: NOT YET PROVEN; raw codes only.
- Confidence support at the 346 observed MOLA points: MEASURED, 259/346 valid.
- 2025 DTM valid support at those points: NOT YET MEASURED.
- Replacement of 2020 HiRISE nodata: NOT YET MEASURED.
- Independent horizontal registration: NOT YET MEASURED.
- Cross-body similarity: NOT YET PROVEN.
- E001 known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Route safety: NOT CLAIMED.

## Next gate

The confidence raster is readable and has valid samples at 259/346 observed MOLA points, but the 70 in-bounds masked points and product-specific code semantics remain unresolved. E568 now tests the actual DTM at the same points and cross-tabulates DTM validity against FOM validity. Do not treat confidence support as elevation support.
