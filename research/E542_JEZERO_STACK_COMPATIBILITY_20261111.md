# E542 — Jezero MOLA / CTX / HiRISE coverage and reference audit

Date: 2026-11-11
Status: metadata-only experiment; raw raster validation pending
Branch: research/e542-jezero-stack-compatibility-20261111
Parent: E541 / PR #100

## Question

Does one pinned Mars area have a documented, multi-resolution MOLA/CTX/HiRISE data stack with a real shared coverage envelope, and which product variants can be combined without silently mixing incompatible registration assumptions?

## Sources and pinned metadata

1. **MOLA MEGT44N000HB PDS3 label**
   [Official PDS label](https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg128/megt44n000hb.lbl). It specifies 128 pixels/degree, 0.463 km/pixel at the equator, simple cylindrical projection, planetocentric latitude, positive-east longitude, IAU2000 reference system, 3396.0 km sphere radius, and tile coverage 0–44°N / 0–90°E. The label says bins without observations are interpolated, only about 55% of equatorial bins contain a shot, and gaps can reach 12 km. The 55% figure is a global equatorial statement, not a Jezero-local count measurement.

2. **Mars 2020 TRN CTX DTM Mosaic**
   [USGS product metadata](https://astrogeology.usgs.gov/search/map/mars_2020_terrain_relative_navigation_ctx_dtm_mosaic), DOI [10.5066/P906QQT8](https://doi.org/10.5066/P906QQT8). Published metadata gives 20 m/pixel, bbox 77.1605–77.699°E / 18.211–18.7212°N, 3396190 m sphere radius, equirectangular projection, planetocentric latitude, positive-east longitude, and MOLA control. The product describes three CTX stereo pairs and reports 9.6 m average horizontal displacement among individual CTX images; the vertical registration is 3.8 m after a 183.3 m mosaic adjustment to HRSC.

3. **Mars Sample Return TRN HiRISE DTM and Orthoimage Mosaics (2025)**
   [USGS product metadata](https://astrogeology.usgs.gov/search/map/mars-sample-return-terrain-relative-navigation-hirise-dtm-mosaic), DOI [10.5066/P13CPYYU](https://doi.org/10.5066/P13CPYYU). Published metadata gives 1 m/pixel, bbox 77.057–77.380°E / 18.135–18.588°N, 3396190 m sphere radius, equirectangular projection, planetocentric latitude, positive-east longitude, and MOLA control. The published alignment to a CTX reference is below 6 m at the 93rd percentile and below 10.2 m at the 99th percentile; eight of ten planned stereo pairs were completed. The exact CTX reference identity still needs to be pinned before a raster overlay.

4. **Mars 2020 Science Investigation CTX DEM Mosaic (2021)**
   [USGS product metadata](https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic). It extends the original TRN CTX DEM with additional CTX orbits, uses a 3396160 m sphere radius, and reports MOLA control. Tao et al. (2023) describe the additional product as MOLA-localized but not co-aligned to HRSC, with significant pixel offsets from HRSC. It is a larger-extent alternative, not an interchangeable substitute for the TRN reference.

5. **Independent Jezero co-registration analysis**
   Tao et al. (2023), [A High-Resolution Digital Terrain Model Mosaic of the Mars 2020 Perseverance Rover Landing Site at Jezero Crater](https://doi.org/10.1029/2023EA003045). The paper reports median horizontal and mean vertical differences of 2.1 m and 0.4 m between the 2020 TRN HiRISE and CTX products, with 95.4% of tested feature correspondences below 6 m. It also warns about the larger 2021 Science Investigation CTX extension's offsets from HRSC.

## Deterministic result

The source metadata supports a shared Jezero coverage envelope:

- The MOLA MEGT44N000HB tile envelope contains both the CTX TRN and 2025 HiRISE metadata envelopes.
- The CTX TRN and 2025 HiRISE envelopes intersect at **77.1605–77.380°E / 18.211–18.588°N**.
- The spherical area of that *bounding-box intersection* is **275.88 km²**. This is not a valid-pixel area; nodata holes, seams and actual raster masks remain unmeasured.
- The nominal linear resolution ratios are MOLA:CTX **23.15:1**, CTX:HiRISE **20:1**, and MOLA:HiRISE **463:1**.

## What changed our belief

**Martian Map #11 has a credible, documented Jezero multi-resolution data path.** The data stack is not a speculative list of instruments: official source metadata identifies a MOLA tile, a 20 m CTX TRN DTM, and a 1 m HiRISE mosaic with overlapping coverage and published CTX alignment statistics.

But the products are not ready for blind concatenation:

- MOLA uses IAU2000 and a 3396.0 km sphere; the CTX/HiRISE products use Mars 2015 metadata and a 3396.19 km sphere. The 190 m sphere-radius difference is a reference-model difference, **not** an observed elevation bias or a vertical correction.
- MOLA's interpolated bins must be separated from actual laser-shot support using the local counts raster. The global 55% equatorial-bin statistic is not a local Jezero measurement.
- The 2025 HiRISE mosaic's exact CTX reference identity must be pinned.
- The 2021 Science Investigation CTX extension must not be silently substituted for the TRN reference; its extra orbits have a documented registration caveat.

**Product choice:** use the 2020 TRN CTX product as the candidate reference and the 2025 HiRISE mosaic only after its exact CTX lineage is pinned. Use MOLA as coarse context with an observed-count mask. Keep the larger 2021 Science Investigation CTX extension quarantined until independently registered.

## Validation

- Local deterministic Python harness: **11/11 tests passed**.
- Tested envelope containment/intersection, spherical bbox-area calculation, resolution ratios, explicit radius differences, MOLA interpolation caveat, product-variant separation, metadata-only claim ceiling, and rejection of Boolean coordinates.
- No raw raster bytes were acquired, no pixel values were inspected, and no local MOLA counts mask was sampled. No elevation-profile comparison or raster registration residual was measured.

## Claim state

- Jezero MOLA/CTX/HiRISE published-metadata coverage compatibility: **SUPPORTED**.
- Raw raster co-registration in this run: **NOT YET MEASURED**.
- Cross-body similarity: **NOT YET PROVEN**.
- Known-site recovery: **NOT YET MEASURED**.
- Novel analogue discovery: **NOT YET PROVEN**.
- Martian Map superiority over MODIS/VIIRS or every other official 2026 challenge: **NOT YET PROVEN**.

This result improves the data-readiness evidence for Challenge #11 but does not justify changing the provisional #11 / #9 tie or locking a challenge.

## Next decisive experiment

Acquire the 9.3 MB official CTX TRN DTM and a bounded HiRISE raster subset; acquire the MOLA 128ppd topography and counts tile; inspect actual file magic, labels, nodata, units, CRS and valid-pixel footprints; pin the exact 2025 CTX reference; transform to one explicit Mars body-fixed reference; then compare elevation profiles and horizontal control residuals over the shared valid-pixel support. Do not advance to route-risk or astronaut-safety claims.


## E543 — local MOLA ground-sample anisotropy correction (2026-11-11)

A review of E542 found that its single MOLA:CTX and MOLA:HiRISE ratios used the PDS label's 463 m/pixel at the equator as though it were an isotropic local ground spacing. For a simple-cylindrical grid, north-south spacing remains the equatorial meridional spacing while east-west ground spacing scales by cos(latitude).

The CTX/HiRISE metadata-envelope overlap centroid is at planetocentric latitude **18.3995°**. Applying the projection geometry gives:

- MOLA east-west ground spacing: **439.3309 m**.
- MOLA north-south ground spacing: **463.0000 m**.
- Local MOLA:CTX ratio: **21.9665:1 east-west**, **23.15:1 north-south**.
- Local MOLA:HiRISE ratio: **439.33:1 east-west**, **463:1 north-south**.

The earlier 23.15:1 and 463:1 values remain valid as equatorial / north-south nominal ratios; they are not local isotropic ratios. The code now reports both nominal and overlap-centroid local values. This is a projection-geometry correction, not a measurement of the raster's effective resolution, valid-pixel support, resampling kernel, or registration quality.

### E543 validation

- Added deterministic tests for the local cosine correction, north/south latitude symmetry, equatorial identity, and rejection of Boolean/nonfinite/out-of-range inputs.
- The metadata-only claim ceiling is unchanged: no raster bytes, pixel values, MOLA count cells, or co-registration residuals were acquired.
- Exact-head Actions validation is recorded in the E543 PR after the branch run completes.
