# E227 | Independent planetary analogue labels: NASA/USGS source audit

**Date:** 2026-10-24. **Research-only, pre-event.** No competition solution or submission.

## Decisive question

Can an independent official source provide usable known-site labels for E001, and are its coordinates and target-body annotations fit for blinded cross-body retrieval?

**Result:** A public USGS ArcGIS service was successfully ingested without credentials, but its four currently returned records **do not provide Moon/Mars target-body labels**, and one has a substantial geometry/attribute coordinate mismatch. This source alone is **not sufficient for E001**.

## Provenance and exact execution

- NASA Planetary Analog Explorer: https://science.nasa.gov/solar-system/analog-explorer/ (11 descriptive Earth/other-world pairs; 9 Moon/Mars).
- USGS Astrogeology data release: *Known Terrestrial Analog Sites for Planetary Science*, Hunter (2020), DOI https://doi.org/10.5066/P9J72921; ScienceBase item `5f88940b82cebb8c13d912ee`.
- Read-only ScienceBase JSON and FGDC XML accessed; official public ArcGIS FeatureServer discovered from item metadata. Its URL was sanitized to remove embedded query parameters before access or persistence.
- **No access token was used.** The public FeatureServer exposes one point layer, `TerrestrialAnalogs`, returning **4** features in the bounded GeoJSON query.
- Raw public GeoJSON SHA-256: `0d0b61a5663f3cb2c00de5a02dfb6bf4599195a4dd28d81514af4d52351f0f1e`.
- Exact-head Actions run [40117178252](https://github.com/stoicsatvik/NASA/actions/runs/40117178252): success. The workflow runs twelve deterministic source/QC tests and uploads `e227_analogue_source_audit.json` and `e227_usgs_coordinate_qc.json` as an immutable numerical artifact.

## Real public-source measurements

| Published USGS point | Source type | Target body populated? | GeoJSON vs Lat/Lon attribute discrepancy |
|---|---|---|---:|
| Pisgah Lava Flow | Volcanic | No | 22.95 m |
| Holuhraun Lava Flow | Volcanic | No | 2.36 m |
| Oskjuvatn | Volcanic | No | 0.00 m |
| Baugur | Volcanic | No | **3,534.10 m** |

- Missing `AnalogBody`: **4/4** (100%).
- All returned `AnalogType` values: **Volcanic**.
- Geometry-versus-attribute discrepancy greater than 100 m: **1/4**.
- Maximum discrepancy: **3.534 km**, for Baugur. This is a disagreement, **not proof which coordinate is wrong**. Small discrepancies may reflect rounded attributes.
- These four sites are *not* a random negative-control population and do not constitute independent cross-body training/evaluation pairs.

## Independent NASA descriptive-pair audit

The 11 NASA gallery examples were recorded with exact headings, target bodies and analyst-classified primary mechanisms. Six concern Mars, three the Moon, one Venus, and one Enceladus. Five of eleven were **analyst-marked** as having a plausible static surface-morphology component; this is a qualitative annotation, not a measured capability or NASA-issued label.

NASA descriptions explicitly include mineralogy, brines, subsurface ice, operational hazard, seismic signals, biosignatures and changing aeolian forms. A two-feature elevation/slope representation cannot be presumed to recover those process-specific relations. The gallery is **not** a binary physical-similarity benchmark, and no coordinates or negative labels were invented.

## Falsification and next experiment

**REJECT** the assumption that this USGS point service alone is immediately sufficient as a labeled Moon/Mars E001 corpus. Its currently accessible four records have no target-body annotation and one ambiguous location. This does **not** reject the wider USGS dataset or the planetary-analogue challenge.

Next seek independent site-specific Moon/Mars geological analogue **positive pairs with explicit process, location and instrument evidence**, plus separately sourced negative controls. Resolve the Baugur coordinate discrepancy from primary metadata before using it in a location-based benchmark. Keep the 11 NASA descriptive pairs separate from quantitative ground truth.

**Claims:** Official NASA descriptive pairs SUPPORTED; read-only USGS public point ingestion SUPPORTED; observed source-quality limitations SUPPORTED; cross-body similarity **NOT YET PROVEN**; E001 known-site recovery **NOT YET MEASURED**; novel discovery **NOT YET PROVEN**; local field advantage **NOT YET PROVEN**; challenge-selection superiority **NOT YET PROVEN**.

No raw geospatial files, credentials, field measurements, destructive sampling, external communications or live deployments were committed/performed.
