# E523 — USGS PAAD live ingestion result

**Retrieved:** 2026-11-10 18:11:01 UTC  
**Workflow:** [#42872539472](https://github.com/stoicsatvik/NASA/actions/runs/42872539472)  
**Artifact:** [13788909175](https://github.com/stoicsatvik/NASA/actions/runs/42872539472/artifacts/13788909175)  
**Source item:** `64d418c3d34ef477cf3ced10`

## Outcome

**Status:** `INGESTED`

The corrected E523 workflow completed successfully:

- Deterministic parser/provenance tests: **10/10 passed**.
- Live USGS ScienceBase acquisition: **45/45 sites**, matching the FGDC release metadata.
- CSV-to-shapefile coordinate cross-check: **45 matched, 0 mismatched, 0 missing pairs** at the declared 0.00051° tolerance (CSV coordinates are stored to four decimals; shapefile coordinates to three).
- CRS: WGS 84 geographic coordinates; geometry: points.
- Normalized table: 45 rows × 13 columns (12 source attributes plus `source_file`).
- No acquisition warnings were emitted.

The original failure was a CLI receipt-key mismatch, not a source-data failure. The regression test now verifies the CLI summary key, and the corrected live run retained an `INGESTED` receipt rather than overwriting it with a failure receipt.

## Data quality and limitations

| Attribute | Missing sites |
|---|---:|
| Composition of sand | 16 |
| Areal coverage | 12 |
| Sand source | 3 |
| Elevation | 1 |
| All other source fields | 0 |

The dataset spans 12 country/region labels and 13 dune-type tokens. All 45 site names and coordinate pairs are unique in this release.

The USGS metadata explicitly says this is a **subset**, with a US-heavy sampling bias from the initial literature search and author network. Elevation may be estimated from GMTED2010 (~250 m regional-scale source); areal coverage and elevation are marked approximate where appropriate. Missing values remain missing; no values were imputed. The raw source strings and references are retained.

This is a terrestrial dune-field index, not a measured Mars dataset. It does not yet establish analog suitability, wind-regime equivalence, sediment-transport equivalence, or a quantitative Mars-to-Earth similarity score. In particular, the missing composition and areal-coverage fields prevent treating all sites as equally characterized.

## Integrity

- Source archive SHA-256: `8d01a089d5958a32d1db951bb46c6ae672b48cd850b2656cfc62f848e6ab9423`
- ScienceBase item JSON SHA-256: `a3e9572a8d40745a95797890fde0c1e26999ee35d46eb23c4ceb735bab10557b`
- Artifact ZIP SHA-256: `426669c28fb0984504e78cd700184c93ead08a53c32b20bec3404018ee87f58d`
- Receipt JSON SHA-256: `bd5d816089ff26594ac60b9f2a450bca8e8f1b9e1b15e07932c73f82d7f2f8be`
- Normalized CSV SHA-256: `0eb40273f9f685e4fd67181c63fa51e24e2fa348cc850cb1641d5e43af221334`

The exact artifact contains the raw FGDC XML, source CSV, shapefile components, normalized CSV and full receipt. No raw file was rewritten.

## Next falsifiable experiment

Use the 45 verified coordinates as the terrestrial index, then compare them against a **predeclared** set of Mars dune-system descriptors. Candidate independent variables include dune morphology, latitude/season, topographic setting, spectral/mineralogical composition, grain-size proxy, and wind-regime proxy. First test whether each feature is available at compatible spatial resolution and uncertainty; only then define a distance metric and baseline ranking. Do not assign an analog score from the current PAAD metadata alone.
