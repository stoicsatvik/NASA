# E568 — 2025 HiRISE DTM and FOM support at observed MOLA points (12 November 2026)

## Question

Does the 2025 USGS Mars Sample Return HiRISE DTM contain valid elevation samples at the same 346 observed MOLA point centers used by E563, and does its FOM_Confidence mask agree with DTM nodata at those exact points?

## Pinned sources

- USGS Mars Sample Return Terrain Relative Navigation HiRISE DTM and Orthoimage Mosaics, DOI 10.5066/P13CPYYU.
- Exact DTM member: MSR_hirise_soc_003_DTM_MOLATopography_DeltaGeoid_1m_Eqc_latTs0_lon0_Blend40.tif.
- Exact FOM member: MSR_hirise_soc_003_FOM_Confidence_1m_Eqc_latTs0_lon0.tif.
- DTM ZIP member size: 675,625,590 compressed / 711,891,990 uncompressed bytes.
- FOM ZIP member size: 65,308,185 compressed / 66,059,236 uncompressed bytes.
- MOLA shot-count source and frozen 33×33 Jezero window are the same as E563/E567. The observed-shot denominator remains 346; zero-count bins are excluded.

## Frozen method

1. Use the exact public S3 archive URL verified by E566.
2. Stream only the DTM and FOM_Confidence ZIP members to temporary runner files. Do not read the 4.6 GB orthoimage or download the full archive.
3. Verify member names, compressed/uncompressed sizes, ZIP method, decompressed byte counts and CRC via the ZIP reader.
4. Open both GeoTIFFs and record CRS, transform, bounds, resolution, dtype, nodata, scale, offset, units, tags and block shape.
5. Transform the same 346 MOLA point centers to each raster CRS without fitting a datum shift.
6. Sample one pixel at each observed point center. Keep observed, in-bounds and valid denominators separate.
7. Compute the DTM/FOM validity cross-tab and raw FOM code counts. Do not interpret FOM codes as calibrated uncertainty.
8. Delete temporary rasters and retain only metadata, aggregate summaries and hashes.

## Prior baseline

E563 measured 164/346 valid points in the 2020 HiRISE DTM, with 256/346 inside its raster bounds and 92 in-bounds nodata points. E567 measured 259/346 valid samples in the 2025 FOM_Confidence raster, with 329/346 inside its bounds. Those are different products and masks; neither result proves 2025 DTM support.

## Interpretation boundaries

- This is point-center support, not area coverage.
- The 2025 mosaic is aligned to the CTX reference, so it is not an independent horizontal control network.
- GeoTIFF scale/offset are recorded and applied to sample summaries; vertical datum equivalence is not tested.
- FOM_Confidence values are retained as raw codes. USGS HiRISE documentation describes FOM as pixel-level provenance for correlation, edits, interpolation/extrapolation, saturation, shadows, nodata and suspicious terrain, but this experiment does not assign numeric meanings to the 2025 codes.
- A valid FOM sample does not by itself prove a valid DTM elevation; the cross-tab measures that relationship.
- No route-safety, cross-body similarity, E001 recovery or novel analogue discovery is claimed.

## Exact-head result

Pending E568 Actions run.

## Claim states

- Public archive range access: SUPPORTED (E566).
- 2025 DTM and FOM member presence: SUPPORTED at archive level (E566).
- 2025 DTM GeoTIFF readability: NOT YET MEASURED.
- 2025 DTM valid support at 346 observed MOLA points: NOT YET MEASURED.
- DTM/FOM mask alignment: NOT YET MEASURED.
- Support relative to the 2020 HiRISE baseline of 164/346: NOT YET MEASURED.
- Independent horizontal registration: NOT YET MEASURED.
- Cross-body similarity: NOT YET PROVEN.
- E001 known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Route safety: NOT CLAIMED.

## Next gate

If the 2025 DTM provides materially better valid support, inspect the DTM scale/offset, MOLA control limitations and FOM categories before any terrain-feature comparison. Do not promote point support into route safety or independent registration accuracy.
