# E545 — bounded MOLA observed-count support at Jezero (11 November 2026)

## Question

Does the pinned MOLA 128 pixels/degree topography product have actual laser-shot support in a small window centered inside the published CTX/2025-HiRISE metadata-envelope intersection, or would the comparison rely on interpolated MOLA bins?

## Pinned public source

- PDS Geosciences Node maintained MGS MOLA Topography Derived bundle.
- Topography tile: MEGT44N000HB.IMG; counts tile: MEGC44N000HB.IMG.
- Both use the same 5,632 × 11,520 grid at 128 pixels/degree over 44°N–0°N and 0°E–90°E.
- Topography is signed 16-bit big-endian integer in metres; counts are unsigned 8-bit observations per bin.
- The topography label describes values as planetary radius minus the GMM3 areoid and explicitly states that bins without observations contain interpolated values.
- The PDS labels specify IAU2000, a 3,396.0 km spherical reference, simple cylindrical projection, planetocentric latitude and positive-east longitude.

## Bounded experiment

- Center: 18.3995°N, 77.27025°E, the centroid of the published CTX/HiRISE metadata-envelope intersection.
- Window: 33 × 33 MOLA bins, centered on the nearest 1-based PDS pixel.
- Request only the 33 required complete rows from each file using HTTP Range. Maximum combined image bytes: 1.2 MB; full rasters are refused if the server ignores Range.
- Validate exact PDS labels, byte ranges, HTTP 206, Content-Range and returned byte counts.
- Compute observed-bin fraction from counts > 0; exclude zero-count/interpolated topography from observed-topography statistics.
- Retain only source/label/range hashes, metadata and summary statistics. Do not retain raw raster bytes or pixel arrays.

## Expected interpretation boundary

A successful positive-count window supports local MOLA shot coverage for this bounded window only. It does not establish common valid-pixel support with CTX/HiRISE, raster co-registration, cross-body similarity, known-site recovery, analogue discovery or route safety.

The MOLA reference is IAU2000 / 3,396.0 km, while the pinned CTX/HiRISE metadata uses Mars 2015 / 3,396.19 km. E545 performs no reference transformation or registration.

## Exact-head result

Exact-head GitHub Actions run 43013238079 succeeded (11 November 2026):

- Deterministic E545 fixtures: 13/13 passed.
- Both PDS labels returned HTTP 200 and passed the frozen dimensions/type/projection contract.
- Topography range: HTTP 206, 760,320 bytes, Content-Range bytes 75110400-75870719/129761280, SHA-256 26bc6c5c3b5445690558a2d2b7af89d8be4d0ef4071eb0f6640c807143db7cd7.
- Counts range: HTTP 206, 380,160 bytes, Content-Range bytes 37555200-37935359/64880640, SHA-256 216841a8e5ad73ea0051e7227bd64086708ae617e451de450904b4f4f0b82b8b.
- The 33 × 33 window contains 346/1,089 bins with count > 0 (31.7723% observed; 743 bins have zero recorded shots and interpolated topography). Positive counts range 1–7, median 2, sum 650.
- Observed-bin topography: min -2,530 m, median -2,080 m, mean -2,115.806 m, max -1,696 m, population SD 228.663 m. These are PDS MOLA areoid-relative values, not yet transformed to the CTX/HiRISE reference.
- Receipt artifact 13851307843; ZIP SHA-256 0c52efbc41515eab4c8f6f25da9b699d74b38edd1395414f51d97cb16f1d23ba. No raw pixels or raster bytes were retained.
- Outcome: MOLA_OBSERVED_SUPPORT_MEASURED. Bounded MOLA ingestion and local observed-shot support for this window: SUPPORTED. The 31.8% result is a measured local coverage fraction, not a global coverage estimate or a co-registration result.
- The MOLA window is centered inside the CTX/HiRISE metadata-envelope intersection; its full footprint extends beyond that intersection. It is not a verified common-valid-pixel window.
- Cross-body similarity remains NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; route safety NOT CLAIMED.


## Claim states (reconciled to exact-head result)

- PDS MOLA source/label interpretation: **SUPPORTED** by the pinned public labels.
- Bounded MOLA topography/count ingestion: **SUPPORTED** for the pinned 33 × 33 window; both exact HTTP 206 ranges passed byte-count and Content-Range validation.
- Jezero-window observed-shot support: **SUPPORTED for this bounded window only**; 346/1,089 bins (31.7723%) have count > 0. This is not a global coverage estimate.
- Common-valid-pixel support with CTX/HiRISE: **NOT YET ESTABLISHED**; the complete MOLA window extends beyond the metadata-envelope intersection and no raster registration/reference transformation is performed.
- Cross-body similarity: **NOT YET PROVEN**.
- Known-site recovery: **NOT YET MEASURED**.
- Novel analogue discovery: **NOT YET PROVEN**.
- Local validation advantage: **NOT YET PROVEN**.
- Route safety: **NOT CLAIMED**.
