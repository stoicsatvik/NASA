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
