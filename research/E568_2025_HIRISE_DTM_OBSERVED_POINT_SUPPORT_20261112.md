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

E563 measured 164/346 valid points in the 2020 HiRISE DTM, with 256/346 inside its raster bounds and 92 in-bounds nodata points. E567 measured 259/346 valid samples in the 2025 FOM_Confidence raster, with 329/346 inside its bounds. E568 now measures the actual 2025 DTM at the same 346 observed point centers. The aggregate 2025 DTM support count is 259/346, 95 points above the 2020 aggregate (27.46 percentage points), but E563 did not retain its per-point validity mask, so this is not a paired point-by-point mask comparison.

## Interpretation boundaries

- This is point-center support, not area coverage.
- The 2025 mosaic is aligned to the CTX reference, so it is not an independent horizontal control network.
- GeoTIFF scale/offset are recorded and applied to sample summaries; vertical datum equivalence is not tested.
- FOM_Confidence values are retained as raw codes. USGS HiRISE documentation describes FOM as pixel-level provenance for correlation, edits, interpolation/extrapolation, saturation, shadows, nodata and suspicious terrain, but this experiment does not assign numeric meanings to the 2025 codes.
- A valid FOM sample does not by itself prove a valid DTM elevation; the cross-tab measures that relationship.
- No route-safety, cross-body similarity, E001 recovery or novel analogue discovery is claimed.

## Exact-head result

- Final code/test head: 41915fa71cbdd77bcf124d9763dec24fae3511f6; exact-head Actions [#43117751701](https://github.com/stoicsatvik/NASA/actions/runs/43117751701) SUCCESS. The combined E566/E567/E568 deterministic suite passed 16 tests; bounded live acquisition completed. Receipt artifact [#13898873321](https://github.com/stoicsatvik/NASA/actions/runs/43117751701/artifacts/13898873321).
- Archive transport: 742,395,283 bytes in 712 range requests under the 850 MiB cap. The 5.47 GB archive was not downloaded as a whole; the 4.6 GB orthoimage was not read; temporary DTM/FOM rasters were deleted. Only a 3,062-byte aggregate receipt was uploaded.
- Both GeoTIFFs are 19,144 × 26,816, one band, 1 m resolution, with identical CRS, transform, bounds and resolution. DTM is float32 with nodata −32767, scale 1 and offset 0; FOM is uint8 with nodata 0. Neither band declares a unit in the GeoTIFF metadata.
- At 346 frozen observed MOLA point centers, 329 were inside both raster bounds, 17 were outside both, 259 were valid in both, and 70 were in-bounds nodata in both. There were zero points inside only one raster and zero validity-mask disagreements within the shared footprint. The explicit cross-tab now separates outside-footprint points from in-footprint nodata.
- DTM sample summary (scale/offset applied as recorded): min −2428.0457, median −2012.3060, mean −2038.0110, max −1651.6827. GeoTIFF band units are null; no vertical datum equivalence or elevation accuracy is claimed.
- The 2025 DTM has 259/346 valid point centers (74.86%), versus E563's 164/346 aggregate for the 2020 DTM (47.40%): +95 supported centers / +27.46 percentage points. This is an aggregate comparison, not a paired mask-overlap statistic, because E563 did not retain its per-point mask.
- FOM codes remain uninterpreted raw categories. Identical DTM/FOM validity masks show support-mask agreement at these points, not calibrated confidence or independent accuracy evidence.

## Claim states

- Public archive range access: SUPPORTED (E566).
- 2025 DTM and FOM member presence: SUPPORTED at archive level (E566).
- 2025 DTM GeoTIFF readability: SUPPORTED for this pinned member.
- 2025 DTM valid support at the 346 observed MOLA points: MEASURED, 259/346 for this bounded window.
- FOM support at the same points: MEASURED, 259/346 (E567/E568).
- DTM/FOM validity-mask agreement: MEASURED at the 346 point centers; 259 both valid, 70 both in-bounds nodata, 17 outside both, zero discordant points.
- Aggregate support relative to the 2020 HiRISE baseline: MEASURED, +95 valid centers; not paired point-by-point.
- Independent horizontal registration: NOT YET MEASURED.
- Vertical datum equivalence / absolute elevation accuracy: NOT YET MEASURED.
- FOM numeric-code semantics for this exact product: NOT YET PROVEN.
- Cross-body similarity: NOT YET PROVEN.
- E001 known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Route safety: NOT CLAIMED.

## Next gate

If the 2025 DTM provides materially better valid support, inspect the DTM scale/offset, MOLA control limitations and FOM categories before any terrain-feature comparison. Do not promote point support into route safety or independent registration accuracy.


## Exact-head result (12 November 2026)

Dedicated Actions run [#43115633885](https://github.com/stoicsatvik/NASA/actions/runs/43115633885) succeeded on head `0d692a630d30ed7cf2bb4b2e19b1a1f56804149c`; receipt artifact [#13899160705](https://github.com/stoicsatvik/NASA/actions/runs/43115633885/artifacts/13899160705).

- 2025 DTM valid support: **259/346** observed MOLA point centers (74.86%); 329/346 are inside raster bounds, with 259/329 valid among those inside.
- FOM_Confidence valid support: **259/346**, exactly the same mask as the DTM at these point centers (259 both valid, 87 both invalid, zero one-sided-valid points).
- Raw FOM code 14 is most frequent (112), followed by 13 (52), 15 (49), and 12 (23); codes remain uninterpreted categories, not calibrated confidence values.
- 712 HTTP ranges transferred 742,395,283 bytes under the 850 MiB cap. The full archive and orthoimage were not downloaded. Temporary rasters were deleted; no point coordinates or raw per-point values were retained.

The 2025 aggregate count is 95 points higher than E563's 2020 count (164/346 versus 259/346, +27.46 percentage points). This is **not a paired comparison** because E563 did not retain its per-point mask. It is not evidence of a causal improvement or independent registration. The 2025 mosaic is CTX-aligned, and FOM codes are not interpreted.

## Updated claim states

- 2025 DTM GeoTIFF readability: SUPPORTED for the pinned member.
- 2025 DTM valid support at 346 observed MOLA points: MEASURED for this bounded window.
- DTM/FOM validity-mask agreement: MEASURED for this bounded window.
- 2020-versus-2025 aggregate support difference: MEASURED; paired pointwise difference NOT YET MEASURED.
- Independent horizontal registration: NOT YET MEASURED.
- Cross-body similarity: NOT YET PROVEN; known-site recovery: NOT YET MEASURED; novel analogue discovery: NOT YET PROVEN; local validation advantage: NOT YET PROVEN; route safety: NOT CLAIMED.

Next: only if this coverage difference is decision-relevant, run a paired 346-point 2020/2025 support-mask comparison and CRS sensitivity. Do not promote point support into route safety or known-analogue recovery.
