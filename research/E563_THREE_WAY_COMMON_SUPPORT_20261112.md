# E563 — three-way MOLA / CTX / HiRISE common-point-support audit (12 November 2026)

## Question

Do the actually observed MOLA bins in the frozen Jezero 33×33 window fall on valid pixels in both the pinned CTX and HiRISE rasters after applying the published MOLA-to-Mars-2015 map-coordinate transformation?

This closes a specific gap left by E545 and E550: MOLA has local laser-shot support, CTX/HiRISE have partial common support, but no experiment has yet measured their three-way common support at the same points.

## Frozen inputs

- MOLA MEGDR v2.0 topography and companion shot-count rasters, PDS Geosciences Node.
- The same 33×33 MOLA window centered at 18.3995°N, 77.27025°E used by E545.
- USGS Mars 2020 TRN CTX DTM mosaic, DOI 10.5066/P906QQT8.
- USGS Mars 2020 TRN HiRISE DTM mosaic, DOI 10.5066/P9REJ9JN.
- HiRISE PDS3 label and GeoTIFF georeferencing metadata.

## Method

1. Re-acquire exact MOLA label and image row ranges; validate dimensions, units, projection, byte ranges and HTTP 206 receipts.
2. Mark a MOLA bin observed only when its companion count is greater than zero. Interpolated topography bins are excluded from the denominator.
3. Derive MOLA pixel-center planetocentric latitude/longitude from the pinned 44°N–0°N, 0°E–90°E simple-cylindrical grid.
4. Derive the target equirectangular CRS from the HiRISE PDS3 label, including its Mars 2015 radius and map scale.
5. Confirm that the CTX raster CRS is equivalent to the PDS3-derived HiRISE CRS before using shared projected coordinates.
6. Sample CTX validity at each observed MOLA bin center. For HiRISE, acquire only bounded row strips spanning observed MOLA point columns; enforce exact byte-range checks and a 2.5 MB transfer cap.
7. Report MOLA-observed, CTX-valid, HiRISE-valid and three-way common point counts. No elevation residual or correction is fitted.

## Interpretation boundary

This is a **point-center support** test, not an area-coverage fraction. A valid sample means the point falls on a finite, non-nodata pixel in the corresponding product. It does not establish horizontal control-point accuracy, vertical datum equivalence, route safety, analogue similarity or known-site recovery.

MOLA's IAU2000 / 3,396.0 km reference and the CTX/HiRISE Mars 2015 reference are not independently tied by control points here. The coordinate transformation preserves planetocentric longitude/latitude and applies the target projection; it does not estimate a datum shift.

## Exact-head result

Pending exact-head GitHub Actions run and compact receipt.

## Claim states

- Bounded MOLA observed-shot support: SUPPORTED by E545; re-acquired in E563.
- CTX/HiRISE CRS parameter equivalence: SUPPORTED by E550; re-checked in E563.
- Three-way MOLA/CTX/HiRISE common point support: NOT YET MEASURED until E563 completes.
- Local horizontal registration residual: NOT YET MEASURED.
- Cross-body similarity: NOT YET PROVEN.
- E001 known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Route safety: NOT CLAIMED.

## Next gate

If three-way support is strong, this only clears a within-Mars spatial-support prerequisite. It does not repair the missing independent Earth positive-site and non-analogue-control labels required for E001. If support is partial or absent, preserve the result and lower Martian Map readiness rather than impute, shift or substitute unsupported pixels.
