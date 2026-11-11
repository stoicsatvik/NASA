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

Pending the first exact-head GitHub Actions run. No MOLA pixels or local shot counts are claimed before the compact receipt is inspected.

## Claim states

- PDS MOLA source/label interpretation: SUPPORTED by the pinned public labels.
- Bounded MOLA topography/count ingestion: NOT YET MEASURED.
- Jezero-window observed-shot support: NOT YET MEASURED.
- Cross-body similarity: NOT YET PROVEN.
- Known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Local validation advantage: NOT YET PROVEN.
- Route safety: NOT CLAIMED.
