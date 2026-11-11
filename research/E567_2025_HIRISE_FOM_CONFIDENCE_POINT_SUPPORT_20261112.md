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

Pending E567 Actions run.

## Claim states

- Public 2025 archive range access: SUPPORTED (E566).
- FOM_Confidence member presence: SUPPORTED at archive level (E566).
- Confidence GeoTIFF readability/georeferencing: NOT YET MEASURED.
- Confidence value semantics for this specific product: NOT YET PROVEN.
- Confidence support at the 346 observed MOLA points: NOT YET MEASURED.
- 2025 DTM valid support at those points: NOT YET MEASURED.
- Replacement of 2020 HiRISE nodata: NOT YET MEASURED.
- Independent horizontal registration: NOT YET MEASURED.
- Cross-body similarity: NOT YET PROVEN.
- E001 known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Route safety: NOT CLAIMED.

## Next gate

If the confidence raster is readable and covers the points, inspect the product-specific FOM legend/metadata and decide whether its values can support a defensible mask. Only then consider the 675.6 MB DTM member. If the confidence file does not add meaningful support or its codes cannot be interpreted, stop this branch rather than downloading the DTM merely because it exists.
