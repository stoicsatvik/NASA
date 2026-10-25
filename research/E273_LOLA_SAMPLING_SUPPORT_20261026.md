# E273 | Real LOLA spatial-aggregation support falsification

**Execution:** 2026-10-26 local / 2026-10-25 UTC. Read-only, pre-event research. **Exact-head [GitHub Actions 40235733739](https://github.com/stoicsatvik/NASA/actions/runs/40235733739): SUCCESS, 83/83 deterministic tests.** Numerical receipt: workflow artifact **12615070896**, `e273-lola-sampling-support-evidence`. No raw rasters committed.

## Question

E212 compared the elevation standard deviation of a 4×4-pixel Moon patch (approximately 30.323 km north-south) to a 2×2-pixel Mars patch (approximately 29.579 km north-south). Equal physical footprint does **not** imply equal sample support or equal instrument smoothing. Does the Moon roughness distribution survive reducing each 4×4 window to four 2×2 block means before comparing to native four-sample Mars windows?

**This is a necessary representation stress test, not E001 or an analogue ranking.**

## Frozen real sources and processing

- Lunar NASA SVS LOLA-derived `ldem_4.tif`, 1440×720 floating TIFF, values in km relative to 1737.4-km sphere, converted to metres. Source SHA-256 `330afa2556a86fd05ac6ba2f912f246600fdade35de2a0d90593d50d07b01b65`.
- Martian PDS MOLA `MEGT90N000CB.IMG`, 4ppd big-endian signed 16-bit, metres above areoid; SHA-256 `25f16fb7aaf857898dcf98bc4f841341a24f8b9f7e98453ca083bc45d897ca2c`.
- MOLA `MEGC90N000CB.IMG` per-cell observation counts; SHA-256 `7e920ec43497b4beddf974650471600c7afd4916e2a8dd3500d6b14714365661`.
- Only equatorial ±10° rows. For the Moon, calculate within-patch SD on the original 4×4 samples and on the four means of its four 2×2 subblocks. For Mars, calculate native 2×2 SD with at least 75% measured cells, never silently fill missing counts. Compare distributions descriptively; do not align unrelated Moon/Mars coordinates.
- Source fingerprints checked before execution. NASA SVS lunar derivative has no independent per-bin observation-count mask.

## Observed result

| Diagnostic | Result |
|---|---:|
| Lunar 4×4 physical support | 30.323 km north-south |
| Martian 2×2 physical support | 29.579 km north-south |
| Lunar aligned windows | 7,200 |
| Median lunar roughness retained after 4×4 → four block means | **0.627667** |
| Reduction in median lunar roughness under spatial averaging | **37.23%** |
| Original vs aggregated lunar top-decile overlap | **638/720 = 88.61%** |
| Median lunar/Mars roughness ratio using native Moon 4×4 | **5.99167** |
| Median lunar/Mars roughness ratio using averaged Moon 2×2 | **3.76077** |

The Moon/Mars roughness ratio changed **37.23%** solely by altering the lunar spatial-aggregation convention while retaining nearly equal north-south physical support. The 82/720 lunar patches exiting the top decile show that rank is also not invariant to aggregation.

This does **not** demonstrate that lunar or Martian terrain is more or less geologically analogous to Earth. A block mean is not a measured MOLA or LOLA point-spread function; different observation geometry, vertical datums, missingness and geology remain uncontrolled.

## Claim states

- **SUPPORTED IN REAL-DERIVED RASTER TEST:** the E212 naive median roughness contrast is sensitive to sample-support aggregation.
- **REJECTED:** treating equal-angle or nearly equal-distance tile width alone as sufficient measurement harmonization.
- **NOT YET PROVEN:** instrument-corrected cross-body similarity.
- **NOT YET MEASURED:** E001 independently labelled known-site recovery.
- **NOT YET PROVEN:** novel analogue discovery, local field advantage, challenge-selection superiority.

## Next experiment

Prioritize independently labelled analogue positives and negative controls, and a source-supported model of the LOLA/MOLA observation footprints. Test leave-one-site-out E001 against random, standardized Euclidean and physically weighted baselines **only when those labels and comparable descriptors exist**. No further optimization on the two unvalidated Earth research leads, and no geospatial UI polishing. Re-rank all official 2026 challenge statements after 28 October.
