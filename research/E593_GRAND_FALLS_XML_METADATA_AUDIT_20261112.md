# E593 — Grand Falls photogrammetry XML metadata audit

Date: 12 November 2026  
Branch: research/e593-grand-falls-xml-metadata-audit-20261112  
Draft PR stacked on E591 / PR #155. Main untouched.

## Question

Does the exact 12,658-byte XML metadata file listed by E591 establish source-described product type, horizontal CRS, vertical datum, grid spacing, nodata, acquisition dates or processing lineage strongly enough to justify opening any of the seven large photogrammetry archives?

## Pinned source

- Child item: 67b78df2d34e1a2e835b13b7.
- E591 metadata SHA-256: f466468ba4b700ecb2a613727483100a9f62f14e8d26dfc8ba840b0122049424.
- Exact metadata file: Photogrammetry_GFDF_ripples_2024.xml.
- Exact catalogue size: 12,658 bytes.
- The item metadata hash must match E591 before the XML request is made.
- The XML file record must match exact filename and size before its download URI is used.
- Only the XML file is fetched. No ZIP archive, raster, image, DEM or orthomosaic bytes are requested.

## Bounded acquisition and safety

- One anonymous item-metadata GET, capped at 5 MB.
- One XML GET, capped at 64 KiB and required to match the 12,658-byte catalogue size.
- HTTPS only; allowlisted ScienceBase/S3 hosts; absent or 443 port only; reject userinfo, fragments, path traversal and unsafe redirects.
- Reject HTML, mismatched item IDs, changed item metadata, duplicate/missing XML records, size mismatch, DTD and entity declarations.
- Parse with Python's standard XML parser only after size and DTD/entity checks.
- Store XML SHA-256, tag-name counts and selected sanitized metadata fields only.
- Do not retain raw XML, raw URLs, signed query values, file paths, contact details or coordinate values.

## Frozen extraction categories

- Product description/title.
- Acquisition and publication dates.
- Horizontal reference: datum, ellipsoid, projected/geographic CRS and units.
- Vertical reference: datum, units and encoding.
- Grid resolution: absolute/ordinate/latitude/longitude resolution, cell size and units.
- Nodata: numeric nodata/missing/fill values separately from a label that merely says “NoData”.
- Raster representation: format, entity type, data type, bands, rows and columns.
- Processing lineage: sanitized process description, process date and source references.

The XML may use FGDC or another schema. The parser records a bounded tag-name inventory as well as recognized fields. No recognized fields is a valid negative result, not a reason to broaden the parser until it produces a positive answer.

## Claim boundary

An XML metadata field is source-described metadata, not independent validation. A CRS label does not prove georegistration accuracy; a grid-spacing field does not prove effective spatial support; a vertical datum label does not establish alignment with MOLA; a nodata label does not prove raster coverage; and a processing description does not prove a reproducible transform chain.

Even a complete metadata record would not establish Earth/Mars morphology comparability, E001 known-site recovery, novel analogue discovery or challenge superiority. The seven ZIP archives total approximately 1.56 GB and remain unopened.

## Validation

The deterministic tests cover:

1. FGDC-style extraction of horizontal/vertical reference, grid resolution, dates, nodata label versus numeric nodata, raster representation and lineage.
2. Coordinate, URL, email and path redaction.
3. Namespace normalization.
4. DTD/entity rejection.
5. 64 KiB cap.
6. HTTPS host/port/userinfo/fragment/traversal policy.
7. Exact child-item metadata hash and XML file selection.
8. Item ID mismatch stopping before XML access.
9. Filename/size mismatch stopping before XML access.
10. Unsafe URL stopping before XML access.
11. HTML and wrong-size XML responses stopping before parsing.

The exact-head live result will be appended after the workflow completes. A missing CRS, vertical datum, grid resolution, nodata value or lineage field remains missing; it will not be inferred from filenames or archive names.

## Next gate

If the XML exposes a defensible small-sample product and exact projection/vertical support, design one separately bounded archive-member inventory that reads only ZIP central-directory metadata and never extracts image/raster bytes. If it does not, keep all seven archives unopened and stop this branch at metadata-only evidence.


## E593 exact-head live result — 12 November 2026

- Final exact head: 503d83e2a355362b894d1e88830a84413e182f7a. Workflow [#43259099282](https://github.com/stoicsatvik/NASA/actions/runs/43259099282) completed successfully: **14/14 deterministic tests passed** and the one bounded live metadata acquisition succeeded. Artifact [#13962867109](https://github.com/stoicsatvik/NASA/actions/runs/43259099282/artifacts/13962867109), ZIP SHA-256 084057e510263038e4002847a20fb3df5d9ab96ad47a3eb5b168d50d1e34d732.
- The initial 13-test run also parsed the same XML. Extending processing-lineage capture to 3,000 characters exposed a fixture defect: run [#43258901440](https://github.com/stoicsatvik/NASA/actions/runs/43258901440) failed 1/14 because the synthetic FGDC fixture omitted the newly tested accuracy/geoform fields; the live probe was skipped. The fixture was corrected, and the exact final head passed 14/14. This was a test-fixture failure, not a source-data failure.
- The E591 item metadata SHA-256 matched exactly: f466468ba4b700ecb2a613727483100a9f62f14e8d26dfc8ba840b0122049424. Exactly one XML record matched the pinned filename and 12,658-byte size. Item metadata and XML requests returned HTTP 200; content type was application/fgdc+xml. XML SHA-256: 0811ca45fadb55c44c438c28a7dd1f6a52b47b09b5abd9f2440cb95ceddd1517.
- The XML explicitly states: **“There is no geospatial data in this dataset, only non-projected point coordinates, so no topology tests were performed.”** The parser found no horizontal CRS, vertical datum, grid resolution, numeric nodata or nodata label fields. The XML tag inventory contains no FGDC spatial-reference section (spref/horizsys/vertdef).
- The product is described as raster digital data. The process description records Nikon D750 / 35 mm imagery with roughly 60% overlap, Metashape high-accuracy camera alignment, filtering of reprojection/reconstruction/projection outliers, an ultra-high-quality dense cloud, a 2.5D height-field mesh, scale-bar marker distances for **relative geometry**, DEM generation with **edge-gap extrapolation**, and orthomosaics forced to match the corresponding DEM pixel dimensions.
- The metadata's completeness statement places the observations at one location in the dune field, approximately 50 m south of the weather-station enclosure, over 2024-02-20 to 2024-07-25. The accuracy-report text is qualitative; it supplies no numeric checkpoint RMSE, independent control residuals, scale-bar uncertainty or vertical accuracy.
- The product's logic statement is a decisive limitation: only non-projected point coordinates are supplied, not geospatial data. A DEM filename or raster form label does not create a CRS. Scale-bar-based relative geometry is not absolute georeferencing. Edge extrapolation also means edge cells are not all direct observations.
- Only the exact 12,658-byte XML file was downloaded. No ZIP, raster, image, DEM or orthomosaic bytes were requested. The seven archives (about 1.56 GB) remain unopened. The durable aggregate receipt is research/results/E593_GRAND_FALLS_XML_METADATA_AUDIT_20261112.json; raw XML, coordinates, URLs, file paths and contact details were not retained.

### Updated decision and next gate

- Source-described local relative 2.5D morphology product: **SUPPORTED**.
- Absolute geospatial placement / horizontal CRS: **NOT SUPPORTED BY THIS XML**.
- Vertical datum, grid spacing and nodata semantics: **NOT ESTABLISHED**.
- Independent geometric accuracy: **NOT ESTABLISHED**.
- Direct MOLA/CTX registration, geospatial overlay or spatially calibrated Mars-analogue comparison: **NOT ADMISSIBLE FROM THIS SOURCE RECORD**.
- Do not open the seven archives under the original georeferencing gate. The only defensible follow-on is a separately justified search for scale-bar calibration, non-projected control-point distances and independent checkpoint residuals. If those are absent, retain this as a local relative-morphology analogue and stop; do not manufacture a geospatial reference frame.
