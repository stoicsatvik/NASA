# E525 — MGD3 spatial-layer source discovery (2026-11-11)

## Finding

The 2018 MGD3 global-summary workbook receipt used by E524 is not the entire Mars Global Digital Dune Database. The official USGS 2007 MGD3 release separately documents a spatial data package with approximately 550 dune-field polygons, a 37-column attribute table, dune type, area, volume, MOLA-based average elevation and dune orientation. The associated THEMIS infrared imagery is described at 100 m/pixel.

Primary sources:

- USGS Open-File Report 2007-1158: https://pubs.usgs.gov/of/2007/1158/
- USGS Mars Global Digital Dune Database overview: https://www.usgs.gov/centers/astrogeology-science-center/science/mars-global-digital-dune-database
- USGS 2018 MGD3 update, which supplies the mineral/stability/thermal-inertia/albedo workbook family already ingested in E318: https://pubs.usgs.gov/publication/ofr20181164

## Why this changes the experiment

E524 found zero directly comparable descriptors in the PAAD CSV plus the profiled 2018 workbook summaries. The 2007 spatial source may supply the missing Mars-side geometry, area, elevation, dune morphology and orientation. A Dune ID join to the 2018 workbook could connect those spatial descriptors to its thermal inertia, albedo and mineral abundance fields. This is a concrete route to a feature matrix; it is not yet a verified join.

## Limits and anti-leakage

- The 2007 database is not an exhaustive census. Small dune fields and regions without adequate coverage are omitted; absence from the database cannot be treated as a non-analogue label.
- The spatial resolution and physical support of each attribute must be recorded separately. The 100 m/pixel THEMIS image support is not automatically the support of MOLA-derived elevation or polygon-level area.
- The PAAD side has approximate elevation and area values, missing composition for 16/45 sites, missing area for 12/45, missing sand source for 3/45 and heterogeneous source methods.
- The 2018 workbook's dune IDs must be reconciled with the spatial release; do not assume ID equivalence across releases.
- No field data, new sensor measurements, or analogue discoveries were made in this source audit.

## Retrieval status

**DOCUMENTED_NOT_INGESTED.** The official source page and dataset structure are identified. The spatial archive itself was not retrieved in this run. Continue through the official USGS download/ScienceBase or OGC endpoints, verify a cryptographic hash and CRS, and preserve retrieval failures. Do not mark the scientific question BLOCKED while legitimate alternate access paths remain.

## Next action

Retrieve the smallest official spatial package, inspect shapefile/geodatabase components and field definitions, verify CRS and Dune ID coverage, then attempt a deterministic join to the E318 workbook. Report matched/unmatched IDs and geometry validity before constructing any cross-body descriptor.