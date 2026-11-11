## E545 update appended below


## E545 — bounded Jezero MOLA observed-count support (2026-11-11)

- Isolated branch: research/e545-mola-observed-support-20261111, based on E544.
- Tests the missing local-support premise directly instead of substituting the global equatorial 55% observed-bin statement.
- Pins the PDS Geosciences Node 128 ppd MOLA topography tile MEGT44N000HB and companion count tile MEGC44N000HB, including their PDS3 labels.
- Samples a 33 × 33 window centered at the published CTX/2025-HiRISE overlap-envelope centroid (18.3995°N, 77.27025°E). Requests only complete fixed-width rows with exact HTTP Range; combined image transfer is capped at 1.2 MB and full-file responses are refused.
- Validates PDS label dimensions, sample types, units, projection, byte offsets, HTTP 206, Content-Range and byte counts. Uses count > 0 to separate observed bins from interpolated topography.
- Retains only hashes, source metadata and compact sample statistics; raw raster bytes and pixel arrays are not committed or uploaded.
- Exact-head Actions result pending. No local MOLA shot-support claim is made until the receipt is inspected.
- Claim states remain: cross-body similarity NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; route safety NOT CLAIMED.
